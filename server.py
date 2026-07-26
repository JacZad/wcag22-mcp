#!/usr/bin/env python3
"""
WCAG 2.2 MCP Server — JSON-backed.
Loads wcag-data.json (built by build_data.py) and serves WCAG 2.2 content
via MCP tools. Logs all requests to ~/.hermes/logs/wcag22-mcp.log.

Usage:
  python3 server.py                          # stdio
  python3 server.py --transport sse --port 9099      # SSE
  python3 server.py --transport streamable-http --port 9099  # Streamable HTTP
"""

import argparse
import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
    from mcp.server.transport_security import TransportSecuritySettings
except ImportError:
    print("ERROR: mcp package not installed. Run: pip install mcp")
    exit(1)

# ── Logging ──

LOG_DIR = Path.home() / ".hermes" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "wcag22-mcp.log"

log = logging.getLogger("wcag22")
log.setLevel(logging.INFO)
fh = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
fh.setLevel(logging.INFO)
log.addHandler(fh)
# Nie propaguj do root loggera (nie mieszaj z stderr serwera)
log.propagate = False


def _fmt_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _trunc(s, maxlen=300):
    if not s:
        return ""
    s = str(s)
    if len(s) <= maxlen:
        return s
    return s[:maxlen] + f"…  [{len(s)} znaków łącznie]"


def _format_args(args_dict):
    """Sformatuj argumenty w czytelny sposób."""
    if not args_dict:
        return "(bez argumentów)"
    parts = []
    for k, v in args_dict.items():
        v_str = _trunc(str(v), 120)
        parts.append(f"{k}={v_str}")
    return ", ".join(parts)


def _format_size(text):
    n = len(text)
    if n < 1024:
        return f"{n} B"
    return f"{n/1024:.1f} KB"


def log_request(remote, method, params, tool_name, tool_args, body_preview):
    """Zaloguj przychodzące żądanie."""
    ts = _fmt_ts()
    lines = []
    lines.append("")
    lines.append("=" * 72)
    lines.append(f"  📥 ZAPYTANIE  |  {ts}")
    lines.append("=" * 72)

    if tool_name:
        lines.append(f"  Narzędzie:    {tool_name}()")
        lines.append(f"  Argumenty:    {_format_args(tool_args)}")
    else:
        lines.append(f"  Metoda MCP:   {method}")
        lines.append(f"  Parametry:    {_trunc(str(params), 200)}")

    if remote:
        lines.append(f"  Źródło:       {remote}")

    lines.append("-" * 72)

    full = "\n".join(lines)
    log.info(full)


def log_response(tool_name, elapsed_ms, content, error=None, truncated=False):
    """Zaloguj odpowiedź."""
    ts = _fmt_ts()
    lines = []
    status = "❌ BŁĄD" if error else "✅ OK"
    size = _format_size(content) if content else "0 B"
    lines.append(f"  📤 ODPOWIEDŹ  |  {ts}  |  {status}  |  {size}  |  {elapsed_ms}ms")

    if error:
        lines.append(f"  Błąd:         {_trunc(error, 500)}")
    if content:
        lines.append(f"  Treść:")
        for line in content.strip().split("\n")[:20]:
            lines.append(f"    {line}")
        if truncated:
            lines.append(f"    … [przycięto — pełna odpowiedź ma {_format_size(content)}]")
    lines.append("=" * 72)

    full = "\n".join(lines)
    log.info(full)


# ─── Middleware dla streamable-HTTP ───

class MCPLogMiddleware:
    """
    ASGI middleware logujący wszystkie żądania i odpowiedzi MCP
    dla transportu streamable-http.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Zbierz body żądania, potem odtwórz receive dla wewnętrznej aplikacji
        body_chunks = []
        more_body = True
        while more_body:
            msg = await receive()
            if msg["type"] == "http.request":
                body_chunks.append(msg.get("body", b""))
                more_body = msg.get("more_body", False)
            elif msg["type"] == "http.disconnect":
                return

        body = b"".join(body_chunks)
        remote = scope.get("client", ["?"])[0] or "?"

        # Sparsuj żądanie MCP
        tool_name = ""
        tool_args = {}
        method = "?"
        params = {}
        if body:
            try:
                data = json.loads(body)
                method = data.get("method", "?")
                params = data.get("params", {})
                if method == "tools/call":
                    tool_name = params.get("name", "")
                    tool_args = params.get("arguments", {})
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

        # Log request
        log_request(remote, method, params, tool_name, tool_args, "")

        # Odtwórz receive dla wewnętrznej aplikacji
        body_sent = False

        async def replay_receive():
            nonlocal body_sent
            if not body_sent:
                body_sent = True
                return {
                    "type": "http.request",
                    "body": body,
                    "more_body": False,
                }
            return {"type": "http.disconnect"}

        # Mierz czas
        start = time.time()
        response_headers = {}
        response_chunks = []

        async def passthrough_send(msg):
            """Przepuść odpowiedź z anti-buffering headers i zbierz treść."""
            nonlocal response_headers, response_chunks
            
            if msg["type"] == "http.response.start":
                response_headers = dict(msg.get("headers", []))
                # Dodaj nagłówki zapobiegające buforowaniu przez Cloudflare/proxy
                h = list(msg.get("headers", []))
                sent_headers = {k.lower() for k, _ in h}
                no_buf = [
                    (b"x-accel-buffering", b"no"),
                    (b"cache-control", b"no-cache, no-store, must-revalidate"),
                    (b"pragma", b"no-cache"),
                    (b"connection", b"keep-alive"),
                ]
                for key, val in no_buf:
                    if key not in sent_headers:
                        h.append((key, val))
                msg["headers"] = h
            
            elif msg["type"] == "http.response.body":
                response_chunks.append(msg.get("body", b""))
            
            await send(msg)

        try:
            await self.app(scope, replay_receive, passthrough_send)
        except Exception as e:
            elapsed_ms = int((time.time() - start) * 1000)
            log_response(tool_name, elapsed_ms, "", error=str(e))
            raise

        elapsed_ms = int((time.time() - start) * 1000)
        # Log response — pełna treść (json_response daje Content-Length)
        resp_body = b"".join(response_chunks)
        resp_text = resp_body.decode("utf-8", errors="replace") if resp_body else ""
        log_response(tool_name, elapsed_ms, resp_text, error=None, truncated=len(resp_body) > 2000)


# ── Load data ──

DATA_PATH = Path(__file__).parent / "wcag-data.json"

with open(DATA_PATH) as f:
    DATA = json.load(f)

SCS = DATA["scs"]
TECHNIQUES = DATA["techniques"]
DEFINITIONS = DATA["definitions"]
PRINCIPLES = DATA["principles"]
GUIDELINES = DATA["guidelines"]
INDEXES = DATA["indexes"]
COUNTS = DATA["counts"]
CATEGORIES = DATA.get("categories", {})
PATTERNS = DATA.get("patterns", {})

# ── Load search index (FTS5 + technique embeddings) ──
EMBED_DIR = Path(__file__).parent / "embeddings"

SEARCH_DB = None
TECH_EMBEDDINGS = None
TECH_INDEX = None
UND_EMBEDDINGS = None
UND_INDEX = None
try:
    import sqlite3
    SEARCH_DB = sqlite3.connect(str(EMBED_DIR / "search.db"), check_same_thread=False)
    SEARCH_DB.execute("PRAGMA query_only = 1")
except Exception as e:
    log.warning(f"FTS5 index not available: {e}")

try:
    import numpy as np
    TECH_EMBEDDINGS = np.load(str(EMBED_DIR / "tech_embeddings.npy"))
    with open(EMBED_DIR / "tech_index.json") as f:
        TECH_INDEX = json.load(f)
    log.info(f"Loaded {TECH_EMBEDDINGS.shape[0]} technique embeddings ({TECH_EMBEDDINGS.shape[1]}d)")
except Exception as e:
    log.warning(f"Technique embeddings not available: {e}")

try:
    import numpy as np
    UND_EMBEDDINGS = np.load(str(EMBED_DIR / "und_embeddings.npy"))
    with open(EMBED_DIR / "und_index.json") as f:
        UND_INDEX = json.load(f)
    log.info(f"Loaded {UND_EMBEDDINGS.shape[0]} understanding embeddings ({UND_EMBEDDINGS.shape[1]}d)")
except Exception as e:
    log.warning(f"Understanding embeddings not available: {e}")

# Build reverse maps
SC_ID_TO_SLUG = {sc["id"]: sc["slug"] for sc in SCS.values()}
SLUG_TO_SC_ID = {sc["slug"]: sc["id"] for sc in SCS.values()}

# Polish SC titles (from WCAG 2.2 PL translation)
SC_PL = {
    '1.1.1': 'Treść nietekstowa',
    '1.2.1': 'Tylko audio lub tylko wideo (nagranie)',
    '1.2.2': 'Napisy rozszerzone (nagranie)',
    '1.2.3': 'Audiodeskrypcja lub alternatywa tekstowa dla mediów (nagranie)',
    '1.2.4': 'Napisy rozszerzone (na żywo)',
    '1.2.5': 'Audiodeskrypcja (nagranie)',
    '1.2.6': 'Język migowy (nagranie)',
    '1.2.7': 'Rozszerzona audiodeskrypcja (nagranie)',
    '1.2.8': 'Alternatywa dla mediów (nagranie)',
    '1.2.9': 'Tylko audio (na żywo)',
    '1.3.1': 'Informacje i relacje',
    '1.3.2': 'Zrozumiała kolejność',
    '1.3.3': 'Właściwości zmysłowe',
    '1.3.4': 'Orientacja',
    '1.3.5': 'Określenie pożądanej wartości',
    '1.3.6': 'Określenie przeznaczenia',
    '1.4.1': 'Użycie koloru',
    '1.4.2': 'Kontrola odtwarzania dźwięku',
    '1.4.3': 'Kontrast (minimalny)',
    '1.4.4': 'Zmiana rozmiaru tekstu',
    '1.4.5': 'Obrazy tekstu',
    '1.4.6': 'Kontrast (wzmocniony)',
    '1.4.7': 'Niska głośność lub bez dźwięków w tle',
    '1.4.8': 'Prezentacja wizualna',
    '1.4.9': 'Obrazy tekstu (bez wyjątków)',
    '1.4.10': 'Dopasowanie do ekranu',
    '1.4.11': 'Kontrast elementów nietekstowych',
    '1.4.12': 'Odstępy w tekście',
    '1.4.13': 'Treść spod kursora lub fokusu',
    '2.1.1': 'Klawiatura',
    '2.1.2': 'Bez pułapki na klawiaturę',
    '2.1.3': 'Klawiatura (bez wyjątków)',
    '2.1.4': 'Jednoznakowe skróty klawiaturowe',
    '2.2.1': 'Dostosowanie czasu',
    '2.2.2': 'Pauza, zatrzymanie, ukrycie',
    '2.2.3': 'Bez ograniczeń czasowych',
    '2.2.4': 'Przerywanie',
    '2.2.5': 'Ponowne potwierdzenie autentyczności',
    '2.2.6': 'Ostrzeżenie o limicie czasu',
    '2.3.1': 'Trzy błyski lub wartości poniżej progu',
    '2.3.2': 'Trzy błyski',
    '2.3.3': 'Animacja po interakcji',
    '2.4.1': 'Możliwość pominięcia bloków',
    '2.4.2': 'Tytuły stron',
    '2.4.3': 'Kolejność fokusu',
    '2.4.4': 'Cel łącza (w kontekście)',
    '2.4.5': 'Wiele dróg',
    '2.4.6': 'Nagłówki i etykiety',
    '2.4.7': 'Widoczny fokus',
    '2.4.8': 'Lokalizacja',
    '2.4.9': 'Cel łącza (z samego łącza)',
    '2.4.10': 'Nagłówki sekcji',
    '2.4.11': 'Fokus niezakryty (minimum)',
    '2.4.12': 'Fokus niezakryty (ulepszony)',
    '2.4.13': 'Wygląd fokusu',
    '2.5.1': 'Gesty dotykowe',
    '2.5.2': 'Rezygnacja ze wskazania',
    '2.5.3': 'Etykieta w nazwie',
    '2.5.4': 'Aktywowanie ruchem',
    '2.5.5': 'Rozmiar celu dotykowego (ulepszone)',
    '2.5.6': 'Równoległy mechanizm wprowadzania danych',
    '2.5.7': 'Przeciąganie',
    '2.5.8': 'Rozmiar celu (minimum)',
    '3.1.1': 'Język strony',
    '3.1.2': 'Język części',
    '3.1.3': 'Nietypowe słowa',
    '3.1.4': 'Skróty',
    '3.1.5': 'Poziom umiejętności czytania',
    '3.1.6': 'Wymowa',
    '3.2.1': 'Po otrzymaniu fokusu',
    '3.2.2': 'Podczas wprowadzania danych',
    '3.2.3': 'Spójna nawigacja',
    '3.2.4': 'Spójna identyfikacja',
    '3.2.5': 'Zmiana na żądanie',
    '3.2.6': 'Spójna pomoc',
    '3.3.1': 'Identyfikacja błędu',
    '3.3.2': 'Etykiety lub instrukcje',
    '3.3.3': 'Sugestie korekty błędów',
    '3.3.4': 'Zapobieganie błędom (prawnym, finansowym, w danych)',
    '3.3.5': 'Pomoc',
    '3.3.6': 'Zapobieganie błędom (wszystkim)',
    '3.3.7': 'Ponowne wpisy',
    '3.3.8': 'Dostępne uwierzytelnianie (minimum)',
    '3.3.9': 'Dostępne uwierzytelnianie (ulepszone)',
    '4.1.1': 'Poprawność kodu',
    '4.1.2': 'Nazwa, rola, wartość',
    '4.1.3': 'Komunikaty o stanie',
}

# ── Build knowledge graph (NetworkX) ──

GRAPH = None
try:
    import networkx as nx
    import re as _re

    G = nx.MultiDiGraph()

    # Add SC nodes
    for sc_id, sc in SCS.items():
        G.add_node("SC:" + sc_id, type="sc", title=sc.get("title", ""),
                   level=sc.get("level", ""), pl_title=SC_PL.get(sc_id, ""))

    # Add technique nodes
    for tid, tech in TECHNIQUES.items():
        G.add_node("T:" + tid, type="technique",
                   category=tech.get("category", ""),
                   tech_type=tech.get("type", ""),
                   wid=tid)
        # Edge: technique → SC
        for sc_id in tech.get("applies_to", []):
            if sc_id in SCS:
                G.add_edge("T:" + tid, "SC:" + sc_id, relation="applies_to")

    # Add SC → technique edges (reverse)
    for sc_id, tech_ids in INDEXES.get("tech_by_sc", {}).items():
        if sc_id not in SCS:
            continue
        for tid in tech_ids:
            if tid in TECHNIQUES:
                G.add_edge("SC:" + sc_id, "T:" + tid, relation="has_technique")

    # Add failure edges
    for sc_id, fail_ids in INDEXES.get("failures_by_sc", {}).items():
        if sc_id not in SCS:
            continue
        for fid in fail_ids:
            if fid in TECHNIQUES:
                G.add_edge("SC:" + sc_id, "T:" + fid, relation="has_failure")

    # Add category nodes + edges
    for cat_name, sc_ids in CATEGORIES.items():
        cat_node = "CAT:" + cat_name
        G.add_node(cat_node, type="category", title=cat_name)
        for sc_id in sc_ids:
            sc_node = "SC:" + sc_id
            if sc_node in G:
                G.add_edge(sc_node, cat_node, relation="in_category")
                G.add_edge(cat_node, sc_node, relation="has_sc")

    # Add pattern nodes + edges
    for pname, pdata in PATTERNS.items():
        pat_node = "PAT:" + pname
        G.add_node(pat_node, type="pattern", title=pdata.get("name", pname))
        for sc_id in pdata.get("scs", []):
            sc_node = "SC:" + sc_id
            if sc_node in G:
                G.add_edge(sc_node, pat_node, relation="in_pattern")
                G.add_edge(pat_node, sc_node, relation="has_sc")

    # Add related techniques (parsed from content_md)
    for tid, tech in TECHNIQUES.items():
        md = tech.get("content_md", "")
        m = _re.search(r'## Related Techniques\s+(.*?)(?=##|\Z)', md, _re.DOTALL)
        if m:
            related_text = m.group(1)
            related_ids = _re.findall(r'\b([A-Z]+\d+)\b', related_text)
            for rid in related_ids:
                if rid in TECHNIQUES and rid != tid:
                    G.add_edge("T:" + tid, "T:" + rid, relation="related_to")

    # Edge: technique → definition
    def_node_map = {}
    for term_key, defn in DEFINITIONS.items():
        dnode = "DEF:" + term_key.lower().replace(" ", "_")
        G.add_node(dnode, type="definition", term=defn.get("term", term_key))
        def_node_map[term_key.lower()] = dnode

    for tid, tech in TECHNIQUES.items():
        md = tech.get("content_md", "").lower()
        for term_lower, dnode in def_node_map.items():
            if term_lower in md:
                G.add_edge("T:" + tid, dnode, relation="references")
                break  # one edge per technique per definition is enough

    # Edge: SC → definition (from normative text or understanding)
    for sc_id, sc in SCS.items():
        haystack = (sc.get("normative_md", "") + " " + sc.get("understanding_md", "")).lower()
        for term_lower, dnode in def_node_map.items():
            if term_lower in haystack:
                G.add_edge("SC:" + sc_id, dnode, relation="references")

    # Edge: SC ↔ SC via shared techniques (co-occurrence)
    sc_techs = {}
    for sc_id in SCS:
        sc_techs[sc_id] = set(INDEXES.get("tech_by_sc", {}).get(sc_id, []))
    for a_id in SCS:
        for b_id in SCS:
            if a_id >= b_id:
                continue
            shared = sc_techs[a_id] & sc_techs[b_id]
            if len(shared) >= 2:  # at least 2 shared techniques = meaningful connection
                G.add_edge("SC:" + a_id, "SC:" + b_id, relation="shares_techniques",
                           weight=len(shared))

    # Edge: SC ↔ SC via shared definitions (co-occurrence)
    sc_defs = {}
    for sc_id, sc in SCS.items():
        haystack = (sc.get("normative_md", "") + " " + sc.get("understanding_md", "")).lower()
        sc_defs[sc_id] = set()
        for term_lower in def_node_map:
            if term_lower in haystack:
                sc_defs[sc_id].add(term_lower)
    for a_id in SCS:
        for b_id in SCS:
            if a_id >= b_id:
                continue
            shared = sc_defs[a_id] & sc_defs[b_id]
            if len(shared) >= 3:  # at least 3 shared definitions
                G.add_edge("SC:" + a_id, "SC:" + b_id, relation="shares_definitions",
                           weight=len(shared))

    GRAPH = G
    log.info(f"Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges, "
             f"{len(CATEGORIES)} categories")
except ImportError:
    log.warning("networkx not installed — graph tools disabled. Install: pip install networkx")
except Exception as e:
    log.warning(f"Graph build failed: {e}", exc_info=True)


def _relative_luminance(hex_color):
    """Calculate relative luminance per WCAG 2.1 formula."""
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    def linearize(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


def _contrast_ratio(hex1, hex2):
    """Calculate contrast ratio between two hex colors."""
    l1 = _relative_luminance(hex1)
    l2 = _relative_luminance(hex2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _resolve(identifier):
    """Resolve '1.1.1' or 'non-text-content' to an SC ID."""
    identifier = identifier.strip().lower()
    if identifier in SCS:
        return identifier
    if identifier in SC_ID_TO_SLUG:
        return identifier
    for sc_id, sc in SCS.items():
        if identifier in sc["slug"] or identifier in sc["title"].lower():
            return sc_id
    return None


def _snippet(text, query, max_len=150):
    if not text:
        return ""
    idx = text.lower().find(query.lower())
    if idx == -1:
        return text[:max_len] + ("..." if len(text) > max_len else "")
    start = max(0, idx - 60)
    end = min(len(text), idx + len(query) + 90)
    s = text[start:end]
    if start > 0:
        s = "..." + s
    if end < len(text):
        s += "..."
    return s


# ─── MCP server ───

mcp = FastMCP(
    "WCAG 2.2 MCP Server",
    json_response=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
    ),
)


@mcp.tool()
def get_sc(identifier: str) -> str:
    """
    Get a WCAG 2.2 success criterion by ID or slug.
    
    Examples: "1.1.1", "non-text-content", "2.4.7"
    Returns: title, level, normative text, and exceptions as Markdown.
    """
    sc_id = _resolve(identifier)
    if not sc_id:
        return f"SC '{identifier}' not found. Try list_scs() to see all."
    
    sc = SCS[sc_id]
    pl_title = SC_PL.get(sc_id, '')
    title_line = f"# {sc['id']} — {sc['title']}"
    if pl_title:
        title_line += f"  |  {pl_title}"
    lines = [
        title_line,
        f"**Level:** {sc.get('level', '')}  **Version:** {sc.get('version', '')}",
        f"**Principle:** {sc.get('principle', '')}  **Guideline:** {sc.get('guideline', '')}",
        "",
        "## Normative Text",
        sc.get('normative_md', ''),
    ]
    if sc.get('exceptions_md'):
        lines.append("")
        lines.append("## Exceptions")
        lines.append(sc['exceptions_md'])
    if sc.get('understanding_md'):
        lines.append("")
        lines.append("## Understanding")
        lines.append(sc['understanding_md'])
    
    lines.append("")
    lines.append(f"📖 [View on W3C]({sc.get('w3c_url', '#')})")
    
    return "\n".join(lines)


@mcp.tool()
def get_definition(term: str) -> str:
    """
    Get the definition of a WCAG term.
    
    Examples: "assistive technology", "keyboard interface", "text alternative"
    Returns the definition as Markdown from the WCAG 2.2 glossary.
    """
    key = term.strip().lower()
    # Direct match
    defn = DEFINITIONS.get(key)
    if not defn:
        # Partial match
        for k, v in DEFINITIONS.items():
            if key in k or k in key:
                defn = v
                break
    if not defn:
        return f"Term '{term}' not found."
    
    lines = [f"## {defn['term']}", "", defn['definition_md']]
    if defn.get('details'):
        lines.append("")
        lines.append("**Examples:**")
        for d in defn['details']:
            lines.append(f"- {d}")
    
    return "\n".join(lines)


@mcp.tool()
def get_techniques(identifier: str) -> str:
    """
    Get techniques for a WCAG 2.2 success criterion.
    
    Examples: "1.1.1", "bypass-blocks", "2.4.7"
    Returns technique IDs with category, type, and snippet.
    Use get_technique(id) for full content of a specific technique.
    """
    sc_id = _resolve(identifier) or identifier
    sc = SCS.get(sc_id, {})
    
    title = f"{sc.get('id', '')} — {sc.get('title', identifier)}" if sc else identifier
    pl_title = SC_PL.get(sc_id, '')
    header = f"# Techniques for {title}"
    if pl_title:
        header += f"  |  {pl_title}"
    header += "\n"
    
    tech_ids = INDEXES.get("tech_by_sc", {}).get(sc_id, [])
    failure_ids = INDEXES.get("failures_by_sc", {}).get(sc_id, [])
    
    if not tech_ids:
        return header + "\nNo techniques found for this success criterion."
    
    lines = [header]
    
    # Separate sufficient/advisory from failures
    sufficient = [t for t in tech_ids if t not in failure_ids]
    failures = [t for t in tech_ids if t in failure_ids]
    
    if sufficient:
        lines.append("## Sufficient & Advisory Techniques")
        for tid in sorted(sufficient):
            tech = TECHNIQUES.get(tid, {})
            cat = tech.get("category", "")
            ttype = tech.get("type", "technique")
            lines.append(f"- **{tid}** ({cat}) — {ttype}")
    
    if failures:
        lines.append("")
        lines.append("## Common Failures")
        for fid in sorted(failures):
            tech = TECHNIQUES.get(fid, {})
            cat = tech.get("category", "")
            lines.append(f"- **{fid}** ({cat})")
    
    lines.append("")
    lines.append(f"📖 Full list: https://www.w3.org/WAI/WCAG22/Techniques/")
    lines.append("")
    lines.append("💡 Use `get_technique(\"GXXX\")` to view the full content of a specific technique.")
    
    return "\n".join(lines)


@mcp.tool()
def get_technique(technique_id: str) -> str:
    """
    Get the full content of a specific WCAG technique by its ID.
    
    Examples: "G103", "H2", "F3", "SL28"
    Returns the full technique description, applicability, examples, and tests.
    """
    tid = technique_id.strip()
    tech = TECHNIQUES.get(tid)
    if not tech:
        # Try without leading @@
        for k, v in TECHNIQUES.items():
            if k.endswith(tid):
                tech = v
                tid = k
                break
    if not tech:
        return f"Technique '{technique_id}' not found."
    
    lines = [
        f"# {tid}",
        f"**Category:** {tech.get('category', '')}",
        f"**Type:** {tech.get('type', '')}",
        "",
    ]
    if tech.get("applies_to"):
        lines.append(f"**Applies to:** {', '.join(tech['applies_to'])}")
        lines.append("")
    
    content = tech.get("content_md", "")
    if content:
        lines.append(content)
    
    return "\n".join(lines)


@mcp.tool()
def check_contrast(foreground: str, background: str) -> str:
    """
    Calculate WCAG contrast ratio between two hex colors.
    
    Examples: check_contrast("#047857", "#FFFFFF"), check_contrast("000000", "fff")
    Returns contrast ratio and pass/fail for AA and AAA levels.
    """
    fg = foreground.lstrip('#')
    bg = background.lstrip('#')
    
    for name, val in [("foreground", fg), ("background", bg)]:
        if not re.match(r'^[0-9A-Fa-f]{6}$', val):
            return f"Invalid {name} color '{foreground}'. Use 6-digit hex (e.g. #047857 or 047857)."
    
    ratio = _contrast_ratio(f'#{fg}', f'#{bg}')
    
    lines = [
        f"# Kontrast: {ratio:.2f}:1",
        f"",
        f"| Foreground | `#{fg.upper()}` |",
        f"| Background | `#{bg.upper()}` |",
        f"| Ratio | **{ratio:.2f}:1** |",
        f"",
        f"## Wynik (WCAG 2.2)",
        f"| Poziom | Normal text (≥4.5:1) | Large text (≥3:1) |",
        f"|---|---|---|",
        f"| **AA** | {'✅' if ratio >= 4.5 else '❌'} {ratio:.2f}:1 | {'✅' if ratio >= 3 else '❌'} {ratio:.2f}:1 |",
        f"| **AAA** | {'✅' if ratio >= 7 else '❌'} {ratio:.2f}:1 | {'✅' if ratio >= 4.5 else '❌'} {ratio:.2f}:1 |",
        f"",
        f"*Large text = bold ≥14pt or regular ≥18pt (≈18.66px CSS).*",
    ]
    
    return "\n".join(lines)


@mcp.tool()
def get_failures(identifier: str) -> str:
    """
    Get common failures for a WCAG 2.2 success criterion.
    
    Examples: "1.3.2", "focus-visible", "2.4.7"
    Returns failure IDs with category and description snippet.
    Use get_technique(id) for full content.
    """
    sc_id = _resolve(identifier) or identifier
    sc = SCS.get(sc_id, {})
    
    title = f"{sc.get('id', '')} — {sc.get('title', identifier)}" if sc else identifier
    header = f"# Common Failures for {title}\\n"
    
    # Collect failures: from failures_by_sc + F-prefix techniques from tech_by_sc
    failures = set(INDEXES.get("failures_by_sc", {}).get(sc_id, []))
    all_techs = INDEXES.get("tech_by_sc", {}).get(sc_id, [])
    for tid in all_techs:
        if tid.startswith('F') and tid not in failures:
            failures.add(tid)
    
    if not failures:
        return header + "\nNo documented failures for this success criterion."
    
    lines = [header]
    for fid in sorted(failures):
        tech = TECHNIQUES.get(fid, {})
        cat = tech.get('category', '')
        snippet = tech.get('content_md', '')[:120].strip().replace('\n', ' ')
        if snippet:
            lines.append(f"- **{fid}** ({cat}) — {snippet}…")
        else:
            lines.append(f"- **{fid}** ({cat})")
    
    return "\n".join(lines)


@mcp.tool()
def get_understanding(identifier: str) -> str:
    """
    Get the Understanding document for a WCAG 2.2 success criterion.
    
    Examples: "1.4.3", "non-text-content", "2.4.11"
    Returns the full Understanding doc as Markdown.
    """
    sc_id = _resolve(identifier) or identifier
    sc = SCS.get(sc_id)
    
    if not sc:
        return f"SC '{identifier}' not found."
    
    full_md = sc.get("understanding_full_md", "")
    if full_md:
        return f"# {sc.get('title', '')}\n\n{full_md}\n\n📖 [Full understanding]({sc.get('w3c_url', '#')})"
    
    short_md = sc.get("understanding_short_md", "")
    if short_md:
        return f"# {sc.get('title', '')} (streszczenie)\n\n{short_md}\n\n📖 [Full understanding]({sc.get('w3c_url', '#')})"
    
    return f"No understanding document for '{identifier}'."


@mcp.tool()
def get_principle(principle_id: str) -> str:
    """
    Get a WCAG 2.2 principle with its guidelines and success criteria.
    
    Examples: "1" (Perceivable), "2" (Operable), "3", "4"
    """
    p = PRINCIPLES.get(principle_id)
    if not p:
        return f"Principle '{principle_id}' not found. Use 1-4."
    
    lines = [f"# Principle {p['num']}: {p['title']}", ""]
    
    for gn in p.get("guidelines", []):
        g = GUIDELINES.get(gn, {})
        lines.append(f"## Guideline {g.get('num', gn)}: {g.get('title', '')}")
        for sc_id in g.get("scs", []):
            sc = SCS.get(sc_id, {})
            lines.append(f"- **{sc.get('id', '')}** {sc.get('title', '')} ({sc.get('level', '')})")
        lines.append("")
    
    return "\n".join(lines)


@mcp.tool()
def get_guideline(guideline_id: str) -> str:
    """
    Get a WCAG 2.2 guideline with its success criteria.
    
    Examples: "1.1" (Text Alternatives), "2.4" (Navigable), "3.3"
    """
    g = GUIDELINES.get(guideline_id)
    if not g:
        return f"Guideline '{guideline_id}' not found. Examples: 1.1, 2.4, 3.3"
    
    p = PRINCIPLES.get(g.get("principle", ""), {})
    lines = [
        f"# Guideline {g['num']}: {g['title']}",
        f"**Principle:** {g.get('principle', '')} — {p.get('title', '')}",
        "",
    ]
    
    for sc_id in g.get("scs", []):
        sc = SCS.get(sc_id, {})
        lines.append(f"- **{sc.get('id', '')}** {sc.get('title', '')} ({sc.get('level', '')})")
    
    return "\n".join(lines)


@mcp.tool()
def get_hierarchy(identifier: str) -> str:
    """
    Get a WCAG 2.2 principle (1-4) or guideline (e.g. 2.4) with its SCs.

    Examples: "1" (Perceivable), "2.4" (Navigable), "3.1"
    """
    if "." in identifier:
        return get_guideline(identifier)
    else:
        return get_principle(identifier)


@mcp.tool()
def list_scs(level: str = "") -> str:
    """
    List all WCAG 2.2 success criteria, optionally filtered by level.
    
    Examples: list_scs(), list_scs("A"), list_scs("AA"), list_scs("AAA")
    """
    level_filter = level.upper() if level else None
    
    if level_filter:
        sc_ids = INDEXES.get("by_level", {}).get(level_filter, [])
        if not sc_ids:
            return f"No SCs at level '{level}'. Use A, AA, or AAA."
        header = f"# WCAG 2.2 — Level {level_filter} ({len(sc_ids)})\n"
    else:
        sc_ids = sorted(SCS.keys(), key=lambda x: [int(p) for p in x.split('.')])
        header = f"# WCAG 2.2 — All Levels ({len(sc_ids)})\n"
    
    lines = [header]
    by_principle = {}
    for sc_id in sc_ids:
        sc = SCS[sc_id]
        p = sc.get("principle", "")
        if p not in by_principle:
            by_principle[p] = []
        by_principle[p].append(sc)
    
    for p_num in sorted(by_principle.keys()):
        p_title = PRINCIPLES.get(p_num, {}).get("title", "")
        lines.append(f"## Principle {p_num}: {p_title}")
        for sc in by_principle[p_num]:
            lines.append(f"- **{sc['id']}** {sc['title']} ({sc.get('level', '')})")
        lines.append("")
    
    return "\n".join(lines)


@mcp.tool()
def get_pattern(pattern_name: str) -> str:
    """
    Get a development pattern for a UI component (Combobox, Dialog, etc.).

    Returns native HTML alternatives, required ARIA attributes,
    keyboard interactions, and related SCs.

    Examples: "combobox", "dialog", "carousel"
    """
    pname = pattern_name.strip().lower()
    pattern = PATTERNS.get(pname)
    if not pattern:
        available = ", ".join(sorted(PATTERNS.keys()))
        return f"Pattern '{pname}' not found. Available: {available}"

    lines = [
        f"# {pattern.get('name', pname)} — wzorzec deweloperski",
        "",
    ]

    first_rule = pattern.get("first_rule_of_aria", "")
    if first_rule:
        lines.append(f"**Pierwsza zasada ARIA:** {first_rule}")
        lines.append("")

    natives = pattern.get("native_alternatives", [])
    if natives:
        lines.append("## Zanim użyjesz ARIA — alternatywy natywne")
        for alt in natives:
            lines.append(f"### {alt.get('when', '')}")
            lines.append(f"```html\n{alt.get('html', '')}\n```")
            lines.append(f"✅ {alt.get('benefits', '')}")
            lines.append("")

    custom_when = pattern.get("use_custom_aria_only_when", [])
    if custom_when:
        lines.append("## Kiedy potrzebujesz custom ARIA")
        for w in custom_when:
            lines.append(f"- {w}")
        lines.append("")

    roles = pattern.get("roles", {})
    if roles:
        lines.append("## Role ARIA")
        for element, role in roles.items():
            lines.append(f"- **{element}**: `role=\"{role}\"`")
        lines.append("")

    req = pattern.get("required_attributes", {})
    if req:
        lines.append("## Wymagane atrybuty")
        for element, attrs in req.items():
            for a in attrs:
                lines.append(f"- `{element}` → `{a}`")
        lines.append("")

    opt = pattern.get("optional_attributes", {})
    if opt:
        lines.append("## Opcjonalne atrybuty")
        for element, attrs in opt.items():
            for a in attrs:
                lines.append(f"- `{element}` → `{a}`")
        lines.append("")

    kb = pattern.get("keyboard", [])
    if kb:
        lines.append("## Klawiatura")
        for k in kb:
            lines.append(f"- {k}")
        lines.append("")

    fm = pattern.get("focus_management", [])
    if fm:
        lines.append("## Zarządzanie fokusem")
        for f in fm:
            lines.append(f"- {f}")
        lines.append("")

    scs = pattern.get("scs", [])
    if scs:
        lines.append("## Powiązane kryteria sukcesu")
        for sc_id in scs:
            sc = SCS.get(sc_id, {})
            pl_text = SC_PL.get(sc_id, "")
            sc_title = sc.get("title", "")
            sc_level = sc.get("level", "")
            pl_str = f" / {pl_text}" if pl_text else ""
            lines.append(f"- **{sc_id}** {sc_title}{pl_str} ({sc_level})")
        lines.append("")

    techs = pattern.get("techniques", [])
    if techs:
        lines.append("## Powiązane techniki")
        for tid in techs:
            lines.append(f"- `{tid}`")
        lines.append("")

    apg_url = pattern.get("apg_url", "")
    if apg_url:
        lines.append(f"📖 [Pełny wzorzec w APG]({apg_url})")

    return "\n".join(lines)


@mcp.tool()
def list_patterns() -> str:
    """
    List all available UI component patterns with descriptions.

    Each pattern describes: native HTML alternatives, required ARIA attributes,
    keyboard interactions, and related SCs.

    Use get_pattern(name) for full details of a specific pattern.
    """
    if not PATTERNS:
        return "No patterns defined."

    lines = ["# Dostępne wzorce deweloperskie"]
    for pname in sorted(PATTERNS.keys()):
        pdata = PATTERNS[pname]
        name = pdata.get("name", pname)
        apg = pdata.get("apg_url", "")
        nscs = len(pdata.get("scs", []))
        url_str = f" — {apg}" if apg else ""
        lines.append(f"- **{pname}** — {name} ({nscs} SC){url_str}")
    lines.append("")
    lines.append("💡 Użyj `get_pattern(\"nazwa\")` aby zobaczyć pełny wzorzec.")

    return "\n".join(lines)


@mcp.tool()
def search(query: str) -> str:
    """
    Search WCAG 2.2 content using hybrid FTS5 + semantic embedding.
    
    QUERY MUST BE IN ENGLISH. The underlying data is entirely English.
    Translate from other languages before calling this tool.
    
    - SCs + definitions: FTS5 full-text search
    - Techniques: semantic embedding search on summaries
    
    Examples: "contrast", "keyboard focus", "text alternative"
    Returns top 15 results with type, ID, and snippet.
    """
    q = query.strip()
    if not q:
        return "Empty query."
    
    _start = time.time()
    results = []
    
    # ── 1. FTS5 search: SCs ──
    if SEARCH_DB is not None:
        try:
            # FTS5: prefix phrase matching
            fts_query = " OR ".join(f'"{w}"*' for w in q.split() if len(w) > 1)
            if fts_query:
                cursor = SEARCH_DB.execute(
                    "SELECT id, type, title, level, rank FROM docs WHERE docs MATCH ? AND type='sc' ORDER BY rank LIMIT 10",
                    (fts_query,)
                )
                for row in cursor.fetchall():
                    sc_id, typ, title, level, rank = row
                    # BM25 rank is negative; better = more negative
                    # Normalize to 0-1 and add title boost
                    score = 8 + max(0, -rank / 15.0)  # ~8-9 range
                    pl_title = SC_PL.get(sc_id, title)
                    results.append({
                        "type": "sc", "id": sc_id,
                        "title": f"{title} / {pl_title}",
                        "level": level, "score": score,
                    })
            
            # Definitions: only match when the TERM contains query words
            cursor = SEARCH_DB.execute(
                "SELECT id FROM docs WHERE type='definition'",
            )
            all_defs = [r[0] for r in cursor.fetchall()]
            q_lower = q.lower()
            q_words = set(q_lower.split())
            for term in all_defs:
                term_lower = term.lower()
                # Count how many query words appear in the term
                matches = sum(1 for w in q_words if w in term_lower)
                if matches > 0:
                    # Bonus if the term appears as a substring or vice versa
                    if term_lower in q_lower or q_lower in term_lower:
                        matches += 1
                    score = 4 + matches  # ~5-7 range
                    results.append({
                        "type": "definition", "id": term,
                        "title": term, "score": score,
                    })
        except Exception as e:
            pass
    
    # ── 2. Semantic search: technique embeddings ──
    if TECH_EMBEDDINGS is not None and TECH_INDEX is not None:
        import urllib.request as _ur
        import json as _json
        
        try:
            # Embed the query
            body = _json.dumps({
                "model": "nomic-embed-text",
                "input": [q],
            }).encode()
            req = _ur.Request(
                "http://localhost:11434/api/embed", body,
                {"Content-Type": "application/json"}
            )
            with _ur.urlopen(req, timeout=30) as resp:
                emb_result = _json.loads(resp.read())
            q_emb = emb_result["embeddings"][0]
            
            # Cosine similarity — we already have normalized embeddings
            import numpy as _np
            sims = _np.dot(TECH_EMBEDDINGS, q_emb)
            
            # Top 7 techniques
            top_idx = _np.argsort(sims)[-7:][::-1]
            for idx in top_idx:
                item = TECH_INDEX["items"][idx]
                score = float(sims[idx])
                if score > 0.3:  # minimum relevance threshold
                    results.append({
                        "type": "technique", "id": item["id"],
                        "score": 2.5 + score * 3,  # ~3.4-4.7 range
                        "applies_to": item.get("applies_to", []),
                        "snippet": item.get("summary", item.get("embed_text", ""))[:150],
                    })
        except Exception as e:
            pass
    
    # ── 3. Semantic search: understanding embeddings ──
    if UND_EMBEDDINGS is not None and UND_INDEX is not None:
        import urllib.request as _ur
        import json as _json
        
        try:
            body = _json.dumps({
                "model": "nomic-embed-text",
                "input": [q],
            }).encode()
            req = _ur.Request(
                "http://localhost:11434/api/embed", body,
                {"Content-Type": "application/json"}
            )
            with _ur.urlopen(req, timeout=30) as resp:
                emb_result = _json.loads(resp.read())
            q_emb = emb_result["embeddings"][0]
            
            import numpy as _np
            sims = _np.dot(UND_EMBEDDINGS, q_emb)
            
            top_idx = _np.argsort(sims)[-5:][::-1]
            for idx in top_idx:
                item = UND_INDEX["items"][idx]
                score = float(sims[idx])
                if score > 0.3:
                    sc_data = SCS.get(item["id"], {})
                    results.append({
                        "type": "understanding",
                        "id": item["id"],
                        "title": item.get("title", ""),
                        "score": 1.5 + score * 2.5,
                        "snippet": sc_data.get("understanding_short_md", "")[:150],
                    })
        except Exception as e:
            pass
    
    # ── Fallback: if no index, do brute-force text search ──
    if not results:
        for sc_id, sc in SCS.items():
            haystack = (sc.get("title", "") + " " + sc.get("normative_md", "")).lower()
            score = haystack.count(q.lower()) * 2
            if q.lower() in sc.get("title", "").lower():
                score += 5
            if score > 0:
                results.append({
                    "type": "sc", "id": sc_id,
                    "title": sc.get("title", ""),
                    "level": sc.get("level", ""),
                    "score": score,
                })
        
        for tid, tech in list(TECHNIQUES.items())[:100]:
            if q.lower() in tid.lower() or q.lower() in tech.get("content_md", "").lower()[:200]:
                results.append({
                    "type": "technique", "id": tid,
                    "score": 2,
                })
    
    # ── Rank & display ──
    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:15]
    
    elapsed = time.time() - _start
    lines = [f"# Search: \"{query}\" — {len(results)} matches ({elapsed*1000:.0f}ms)\n"]
    for r in results:
        icon = {"sc": "🎯", "definition": "📖", "technique": "🔧", "understanding": "📝"}.get(r["type"], "•")
        if r["type"] == "sc":
            lines.append(f"{icon} **{r['id']}** — {r['title']} ({r.get('level', '')})")
        elif r["type"] == "definition":
            lines.append(f"{icon} **{r['title']}**")
        elif r["type"] == "technique":
            lines.append(f"{icon} **{r['id']}**")
            if r.get("applies_to"):
                at = r["applies_to"]
                sc_labels = ", ".join(f"{s['sc_id']} {s['title']}" for s in at[:3])
                if len(at) > 3:
                    sc_labels += f" +{len(at)-3}"
                lines.append(f"  📌 {sc_labels}")
            if r.get("snippet"):
                lines.append(f"  > {r['snippet']}")
        elif r["type"] == "understanding":
            lines.append(f"{icon} **{r['id']}** — {r['title']} (objaśnienie)")
            if r.get("snippet"):
                lines.append(f"  > {r['snippet']}")
    
    return "\n".join(lines)


@mcp.tool()
def status() -> str:
    """
    Get server status and statistics about the loaded WCAG 2.2 data.
    """
    return (
        f"## WCAG 2.2 MCP Server — Status\n\n"
        f"**Success Criteria:** {COUNTS['scs']}\n"
        f"**Terms/Definitions:** {COUNTS['definitions']}\n"
        f"**Techniques:** {COUNTS['techniques']}\n"
        f"**Understanding Docs:** {COUNTS['understanding']}\n"
        f"**Categories:** {COUNTS.get('categories', 0)}\n"
        f"**Patterns:** {COUNTS.get('patterns', 0)}\n"
        f"**Data size:** {os.path.getsize(DATA_PATH) / 1024:.0f} KB\n"
        f"\n"
        f"### Tools\n"
        f"- `get_sc(identifier)` — Get a success criterion (with Polish titles)\n"
        f"- `get_techniques(identifier)` — Get techniques for an SC\n"
        f"- `get_technique(technique_id)` — Get full content of a technique\n"
        f"- `get_failures(identifier)` — Get failures for an SC\n"
        f"- `get_definition(term)` — Get a term definition\n"
        f"- `get_understanding(identifier)` — Get understanding doc\n"
        f"- `check_contrast(foreground, background)` — Check WCAG contrast ratio\n"
        f"- `get_hierarchy(id)` — Get a principle (1-4) or guideline (e.g. 2.4)\n"
        f"- `list_scs(level)` — List SCs, filter by A/AA/AAA\n"
        f"- `search(query)` — Search across all content\n"
        f"- `graph_query(entity)` — Query graph: neighbors, paths, categories\n"
        f"- `graph_between(entity_a, entity_b)` — Find connections between two entities\n"
        f"- `graph_categories()` — List thematic categories with statistics\n"
        f"- `get_pattern(name)` — Get a development pattern (combobox, dialog...)\n"
        f"- `list_patterns()` — List available patterns\n"
        f"- `status()` — This status message"
    )


# ─── Graph tools ───


@mcp.tool()
def graph_query(entity: str) -> str:
    """
    Query the WCAG knowledge graph for an entity (SC, technique, or category).
    Returns its neighbors, connections, and categories.

    Examples: "1.4.3", "G18", "Fokus", "non-text-content"
    """
    if GRAPH is None:
        return "Graph is not available. Install: pip install networkx"

    # Resolve the raw input to a node ID
    node_id = _resolve_graph_node(entity)
    if not node_id:
        return f"Entity '{entity}' not found in the graph."

    if node_id not in GRAPH:
        return f"Node '{entity}' resolved to '{node_id}' but not in graph."

    node_data = GRAPH.nodes[node_id]
    ntype = node_data.get("type", "?")
    lines = [f"# {node_data.get('title', node_id)} ({ntype})"]

    if ntype == "sc":
        lines.append(f"**SC:** {entity}  **Level:** {node_data.get('level', '')}")
        pl = node_data.get("pl_title", "")
        if pl:
            lines.append(f"**PL:** {pl}")
    elif ntype == "technique":
        lines.append(f"**Category:** {node_data.get('category', '')}  "
                     f"**Type:** {node_data.get('tech_type', '')}")
        lines.append(f"**ID:** {node_data.get('wid', entity)}")
    elif ntype == "category":
        lines.append(f"**Category node** — shows which SCs belong here")
    elif ntype == "definition":
        lines.append(f"**Definition** — glossary term")

    lines.append("")

    # Group neighbors by relation
    from_neighbors = {}
    to_neighbors = {}
    for _, neighbor, data in GRAPH.out_edges(node_id, data=True):
        rel = data.get("relation", "?")
        if rel not in to_neighbors:
            to_neighbors[rel] = []
        to_neighbors[rel].append(neighbor)

    for neighbor, _, data in GRAPH.in_edges(node_id, data=True):
        rel = data.get("relation", "?")
        if rel not in from_neighbors:
            from_neighbors[rel] = []
        from_neighbors[rel].append(neighbor)

    rel_labels = {
        "applies_to": "→ dotyczy SC",
        "has_technique": "← ma technikę",
        "has_failure": "← ma błąd (failure)",
        "in_category": "→ należy do kategorii",
        "has_sc": "← zawiera SC",
        "related_to": "↔ powiązana technika",
        "references": "→ odnosi się do definicji",
        "shares_techniques": "↔ dzieli techniki z",
        "shares_definitions": "↔ dzieli definicje z",
    }

    if to_neighbors:
        lines.append("### Krawędzie wychodzące")
        for rel, neighbors in sorted(to_neighbors.items()):
            label = rel_labels.get(rel, rel)
            for n in sorted(neighbors, key=_graph_sort_key):
                nd = GRAPH.nodes[n]
                title = nd.get("title", nd.get("term", n))
                ntype_label = {"sc": "SC", "technique": "T", "category": "KAT",
                               "definition": "DEF"}.get(nd.get("type", ""), "?")
                weight = ""
                for _, _, d in GRAPH.out_edges(node_id, data=True):
                    if d.get("relation") == rel and n in [v for _, v in GRAPH.out_edges(node_id)]:
                        if "weight" in d:
                            weight = f" (w={d['weight']})"
                        break
                lines.append(f"- {label}: **{ntype_label} {_graph_short(n)}** {title}{weight}")

    if from_neighbors:
        lines.append("### Krawędzie przychodzące")
        for rel, neighbors in sorted(from_neighbors.items()):
            label = rel_labels.get(rel, rel)
            for n in sorted(neighbors, key=_graph_sort_key):
                nd = GRAPH.nodes[n]
                title = nd.get("title", nd.get("term", n))
                ntype_label = {"sc": "SC", "technique": "T", "category": "KAT",
                               "definition": "DEF", "pattern": "PAT"}.get(nd.get("type", ""), "?")
                lines.append(f"- {label}: **{ntype_label} {_graph_short(n)}** {title}")

    return "\n".join(lines)


@mcp.tool()
def graph_between(entity_a: str, entity_b: str) -> str:
    """
    Find how two entities are connected in the WCAG knowledge graph.
    Shows shared neighbors, shortest paths, and overlap statistics.

    Examples: graph_between("1.4.3", "1.4.1"), graph_between("Fokus", "G18")
    """
    if GRAPH is None:
        return "Graph is not available. Install: pip install networkx"

    a = _resolve_graph_node(entity_a)
    b = _resolve_graph_node(entity_b)

    if not a:
        return f"Entity '{entity_a}' not found."
    if not b:
        return f"Entity '{entity_b}' not found."
    if a == b:
        return f"Both resolve to the same node: {a}"

    na = GRAPH.nodes.get(a)
    nb = GRAPH.nodes.get(b)
    title_a = na.get("title", na.get("term", entity_a)) if na else entity_a
    title_b = nb.get("title", nb.get("term", entity_b)) if nb else entity_b

    lines = [f"# Połączenia: {_graph_short(a)} ({title_a}) ↔ {_graph_short(b)} ({title_b})"]

    # Shared neighbors
    preds_a = set(GRAPH.predecessors(a)) | set(GRAPH.successors(a))
    preds_b = set(GRAPH.predecessors(b)) | set(GRAPH.successors(b))
    shared = preds_a & preds_b

    if shared:
        lines.append(f"\n### Wspólni sąsiedzi ({len(shared)})")
        for n in sorted(shared, key=_graph_sort_key):
            nd = GRAPH.nodes[n]
            title = nd.get("title", nd.get("term", n))
            lines.append(f"- **{_graph_short(n)}** {title}")
    else:
        lines.append("\nBrak bezpośrednich wspólnych sąsiadów.")

    # Shortest path
    try:
        path = nx.shortest_path(GRAPH, a, b)
        lines.append(f"\n### Najkrótsza ścieżka ({len(path)-1} przeskoków)")
        for i in range(len(path) - 1):
            nd = GRAPH.nodes[path[i]]
            title = nd.get("title", nd.get("term", path[i]))
            lines.append(f"  **{_graph_short(path[i])}** {title}")
            # edge label
            edge_data = GRAPH.get_edge_data(path[i], path[i + 1])
            if edge_data:
                rel = list(edge_data.values())[0].get("relation", "→")
                lines.append(f"  ↓ {rel}")
        nd = GRAPH.nodes[path[-1]]
        title = nd.get("title", nd.get("term", path[-1]))
        lines.append(f"  **{_graph_short(path[-1])}** {title}")
    except nx.NetworkXNoPath:
        lines.append("\n❌ Brak ścieżki między tymi węzłami.")

    return "\n".join(lines)


@mcp.tool()
def graph_categories() -> str:
    """
    List all thematic categories with statistics:
    how many SCs and techniques each contains.
    """
    if GRAPH is None:
        return "Graph is not available. Install: pip install networkx"

    lines = ["# Kategorie tematyczne WCAG 2.2\n"]
    for cat_name in sorted(CATEGORIES.keys()):
        cat_node = "CAT:" + cat_name
        sc_ids = CATEGORIES[cat_name]
        # Count techniques assigned to these SCs
        techs = set()
        for sc_id in sc_ids:
            sc_node = "SC:" + sc_id
            for _, neighbor, data in GRAPH.out_edges(sc_node, data=True):
                rel = data.get("relation", "")
                if rel == "has_technique" or rel == "has_failure":
                    techs.add(neighbor)

        sc_pl = []
        for sc_id in sc_ids:
            pl = SC_PL.get(sc_id, "")
            level = SCS.get(sc_id, {}).get("level", "")
            sc_pl.append(f"{sc_id} ({level})")
            if pl:
                sc_pl[-1] += f" — {pl}"

        lines.append(f"## {cat_name}")
        lines.append(f"- **SC:** {len(sc_ids)}  |  **Techniki:** {len(techs)}")
        lines.append(f"- SC: {', '.join(sc_pl)}")
        lines.append("")

    lines.append(f"---\nŁącznie: **{len(CATEGORIES)}** kategorii")
    return "\n".join(lines)


# ─── Helpers ───


def _resolve_graph_node(entity: str) -> str | None:
    """Resolve a user-provided string to a graph node ID (prefixed form)."""
    e = entity.strip()

    # Direct match (already prefixed)
    if e in GRAPH:
        return e

    # Category name
    cat_key = "CAT:" + e
    if cat_key in GRAPH:
        return cat_key

    # Technique ID (uppercase G18, H37, etc.)
    tech_key = "T:" + e.upper()
    if tech_key in GRAPH:
        return tech_key

    # SC by ID
    sc_key = "SC:" + e
    if sc_key in GRAPH:
        return sc_key

    # SC by slug (e.g., "non-text-content")
    sc_id = SLUG_TO_SC_ID.get(e)
    if sc_id:
        return "SC:" + sc_id

    # Partial match by slug
    for slug, sc_id in SLUG_TO_SC_ID.items():
        if e.lower() in slug:
            return "SC:" + sc_id

    # Try as technique without prefix (case-insensitive)
    for tid in TECHNIQUES:
        if e.upper() == tid:
            return "T:" + tid

    return None


def _graph_short(nid: str) -> str:
    """Short display for a graph node."""
    if nid.startswith("SC:"):
        return nid[3:]
    if nid.startswith("T:"):
        return nid[2:]
    if nid.startswith("CAT:"):
        return nid[4:]
    if nid.startswith("DEF:"):
        return nid[4:].replace("_", " ")
    if nid.startswith("PAT:"):
        return nid[4:]
    return nid


def _graph_sort_key(nid: str) -> tuple:
    """Sort key for graph nodes (SC numerics first, then alpha)."""
    if nid.startswith("SC:"):
        parts = nid[3:].split(".")
        return (0, int(parts[0]), int(parts[1]) if len(parts) > 1 else 0, nid)
    return (1, 0, 0, nid)

def main():
    parser = argparse.ArgumentParser(description="WCAG 2.2 MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse", "streamable-http"], default="stdio",
                        help="Transport protocol (default: stdio)")
    parser.add_argument("--host", default="127.0.0.1",
                        help="Host to bind (SSE/HTTP only, default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=9099,
                        help="Port to bind (SSE/HTTP only, default: 9099)")
    args = parser.parse_args()

    log.info("=" * 72)
    log.info(f"  🚀 SERVER START  |  {_fmt_ts()}")
    log.info(f"  Dane: {COUNTS['scs']} SC, {COUNTS['techniques']} technik, "
             f"{COUNTS['definitions']} definicji, {COUNTS['understanding']} dokumentów")
    log.info(f"  Transport: {args.transport}  |  Log: {LOG_FILE}")
    log.info("=" * 72)

    print(f"WCAG 2.2 MCP Server starting...", file=__import__('sys').stderr)
    print(f"  Data: {COUNTS['scs']} SCs, {COUNTS['techniques']} techniques, "
          f"{COUNTS['definitions']} definitions, {COUNTS['understanding']} docs",
          file=__import__('sys').stderr)
    print(f"  Transport: {args.transport}", file=__import__('sys').stderr)
    print(f"  Log: {LOG_FILE}", file=__import__('sys').stderr)

    if args.transport == "sse":
        import uvicorn
        from starlette.middleware.base import BaseHTTPMiddleware
        
        sse_app = mcp.sse_app()
        
        class NoBufferMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request, call_next):
                response = await call_next(request)
                response.headers["X-Accel-Buffering"] = "no"
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Connection"] = "keep-alive"
                return response
        
        app = NoBufferMiddleware(sse_app)
        log.info(f"  Nasłuch: http://{args.host}:{args.port}/sse")
        print(f"  Listening on http://{args.host}:{args.port}/sse", file=__import__('sys').stderr)
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    
    elif args.transport == "streamable-http":
        import uvicorn
        raw_app = mcp.streamable_http_app()
        app = MCPLogMiddleware(raw_app)
        log.info(f"  Nasłuch: http://{args.host}:{args.port}/mcp")
        print(f"  Listening on http://{args.host}:{args.port}/mcp", file=__import__('sys').stderr)
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    
    else:
        # stdio — logowanie ograniczone (brak łatwego hooka w MCP stdio)
        log.warning("  Tryb stdio — logowanie żądań tylko na poziomie serwera")
        print("  Uruchomiono w trybie stdio. Log: " + str(LOG_FILE), file=__import__('sys').stderr)
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
