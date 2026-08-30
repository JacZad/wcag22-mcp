#!/usr/bin/env python3
"""
WCAG 2.2 MCP Server — JSON-backed.
Loads wcag-data.json (built by build_data.py) and serves WCAG 2.2 content
via MCP tools. Logs all requests to ~/.hermes/logs/wcag22-mcp.log.

Usage:
  python3 server.py                          # stdio
  python3 server.py --transport sse --port 9099      # SSE
  python3 server.py --transport streamable-http --port 9099  # Streamable HTTP

API key protection (optional):
  python3 server.py --transport streamable-http --port 9100 --api-key "twoj-klucz"
  # or: export WCAG22_API_KEY="twoj-klucz"
  # Client sends: X-API-Key: twoj-klucz
"""

import argparse
import hmac
import json
import logging
import os
import re
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
    from mcp.server.transport_security import TransportSecuritySettings
except ImportError:
    print("ERROR: mcp package not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

# ── Logging ──

# Cloud Run ustawia K_SERVICE. Tam system plików to tmpfs liczony do limitu
# pamięci, a plik logu i tak nie trafia do Cloud Logging — więc w chmurze
# logujemy wyłącznie na stderr. Lokalnie zostaje plik plus stderr dla ostrzeżeń.
IN_CLOUD_RUN = bool(os.environ.get("K_SERVICE"))

LOG_DIR = Path.home() / ".hermes" / "logs"
LOG_FILE = LOG_DIR / "wcag22-mcp.log"

log = logging.getLogger("wcag22")
log.setLevel(logging.INFO)
# Nie propaguj do root loggera (nie mieszaj z stderr serwera)
log.propagate = False

# stdio używa stdout na protokół, więc stderr jest bezpieczny w każdym trybie.
sh = logging.StreamHandler(sys.stderr)
sh.setLevel(logging.INFO if IN_CLOUD_RUN else logging.WARNING)
sh.setFormatter(logging.Formatter("[wcag22] %(levelname)s: %(message)s"))
log.addHandler(sh)

if not IN_CLOUD_RUN:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
        fh.setLevel(logging.INFO)
        log.addHandler(fh)
    except OSError as e:
        # Katalog domowy bywa niezapisywalny — to nie powód, żeby nie wstać.
        LOG_FILE = None
        log.warning(f"Nie mogę pisać do pliku logu: {e}")


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


# ─── API key middleware ───

class APIKeyMiddleware:
    """
    ASGI middleware sprawdzający nagłówek X-API-Key.
    Jeśli klucz nie pasuje — zwraca 401.
    Jeśli klucz jest pusty (brak zabezpieczenia) — przepuszcza bez sprawdzenia.
    """

    def __init__(self, app, api_key: str):
        self.app = app
        self.api_key = api_key

    async def __call__(self, scope, receive, send):
        # Skip non-HTTP (WebSocket, etc.)
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Jeśli nie ustawiono klucza — przepuść bez sprawdzania
        if not self.api_key:
            await self.app(scope, receive, send)
            return

        # Zbierz nagłówki i znajdź X-API-Key
        headers = dict(scope.get("headers", []))
        request_key = headers.get(b"x-api-key", b"").decode("utf-8", "replace")

        # compare_digest zamiast != — stały czas porównania, bez wycieku
        # informacji o tym, ile znaków klucza się zgadza.
        if not hmac.compare_digest(request_key.encode("utf-8"), self.api_key.encode("utf-8")):
            log.warning(f"  🔒 ODRZUCONE (401)  |  {_fmt_ts()}  |  podany klucz: {_trunc(request_key, 20)}")
            body = json.dumps({
                "error": "Unauthorized",
                "message": "Missing or invalid API key. Provide via X-API-Key header.",
            }).encode()
            await send({
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"x-accel-buffering", b"no"),
                    (b"cache-control", b"no-cache, no-store, must-revalidate"),
                ],
            })
            await send({
                "type": "http.response.body",
                "body": body,
            })
            return

        await self.app(scope, receive, send)


# ─── Middleware dla streamable-HTTP ───

# Ile bajtów odpowiedzi zatrzymać na potrzeby logu
_LOG_BODY_LIMIT = 4096


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
            # Dalej oddajemy sterowanie prawdziwemu receive. Zwracanie tutaj
            # http.disconnect kazało Starlette anulować strumień odpowiedzi,
            # bo nasłuch rozłączenia biegnie równolegle z jej wysyłaniem.
            return await receive()

        # Mierz czas
        start = time.time()
        response_chunks = []
        response_bytes = 0

        async def passthrough_send(msg):
            """Przepuść odpowiedź z anti-buffering headers i zbierz próbkę treści."""
            nonlocal response_chunks, response_bytes

            if msg["type"] == "http.response.start":
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
                chunk = msg.get("body", b"")
                response_bytes += len(chunk)
                # Do logu wystarczy początek — nie kopiujemy całej odpowiedzi,
                # która przy get_understanding(full=True) ma kilkadziesiąt KB.
                if response_bytes <= _LOG_BODY_LIMIT:
                    response_chunks.append(chunk)

            await send(msg)

        try:
            await self.app(scope, replay_receive, passthrough_send)
        except Exception as e:
            elapsed_ms = int((time.time() - start) * 1000)
            log_response(tool_name, elapsed_ms, "", error=str(e))
            raise

        elapsed_ms = int((time.time() - start) * 1000)
        resp_text = b"".join(response_chunks).decode("utf-8", errors="replace")
        log_response(tool_name, elapsed_ms, resp_text, error=None,
                     truncated=response_bytes > _LOG_BODY_LIMIT)


# ── Load data ──

DATA_PATH = Path(__file__).parent / "wcag-data.json"

with open(DATA_PATH, encoding="utf-8") as f:
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

# ── Load search index (FTS5) ──
INDEX_DIR = Path(__file__).parent / "embeddings"
EMB_DIR = INDEX_DIR  # zachowana stara nazwa dla zgodności

SEARCH_DB = None
try:
    import sqlite3
    _db_path = EMB_DIR / "search.db"
    if not _db_path.is_file():
        # sqlite3.connect() na nieistniejącej ścieżce tworzy pustą bazę bez błędu,
        # przez co brak indeksu ujawniał się dopiero jako ciche zero wyników.
        raise FileNotFoundError(f"brak pliku {_db_path}")
    SEARCH_DB = sqlite3.connect(f"{_db_path.as_uri()}?mode=ro", uri=True, check_same_thread=False)
    _n_docs = SEARCH_DB.execute("SELECT count(*) FROM docs").fetchone()[0]
    log.info(f"Loaded FTS5 index: {_n_docs} documents from {_db_path.name}")
except Exception as e:
    SEARCH_DB = None
    log.warning(f"FTS5 index not available: {e}")

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

# ── Lookup indexes ──

_PL_FOLD = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")


def _norm_key(text):
    """
    Klucz porównawczy: małe litery ASCII, bez spacji i interpunkcji.

    Polskie znaki są transliterowane, nie usuwane — inaczej "pominięcia"
    zwijałoby się do "pominicia" i łapało przypadkowe zapytania.
    """
    folded = unicodedata.normalize("NFKD", str(text).translate(_PL_FOLD))
    folded = "".join(c for c in folded if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", folded.lower())


# Techniki po znormalizowanym ID. Klucze z prefiksem "@@" (artefakt parsera)
# ustępują pierwszeństwa normalnym, dlatego sortujemy je na koniec.
TECH_BY_NORM = {}
for _tid in sorted(TECHNIQUES, key=lambda k: (k.startswith("@@"), k)):
    TECH_BY_NORM.setdefault(_norm_key(_tid), _tid)

# Tytuły technik — pierwszy nagłówek "# ..." w treści. Techniki nie mają
# osobnego pola z tytułem, a bez niego graf pokazywał tylko surowe ID.
_TECH_TITLE_RE = re.compile(r"^\s*#\s+(.+?)\s*$", re.MULTILINE)
TECH_TITLES = {}
for _tid, _tech in TECHNIQUES.items():
    _m = _TECH_TITLE_RE.search(_tech.get("content_md", ""))
    TECH_TITLES[_tid] = _m.group(1).strip() if _m else _tid

# Kryteria po ID, slugu oraz tytule angielskim i polskim.
SC_BY_NORM = {}
# Poszczególne słowa aliasów — do dopasowania częściowego. Dopasowujemy tylko
# początek słowa, bo szukanie podciągu w całym aliasie dawało trafienia
# przypadkowe ("nic" wewnątrz "ograniczeń").
SC_ALIAS_WORDS = []
for _sc_id, _sc in SCS.items():
    for _alias in (_sc_id, _sc.get("slug", ""), _sc.get("title", ""), SC_PL.get(_sc_id, "")):
        if not _alias:
            continue
        _norm_alias = _norm_key(_alias)
        if not _norm_alias:
            continue
        SC_BY_NORM.setdefault(_norm_alias, _sc_id)
        for _word in re.split(r"[\s\-_/(),.]+", _alias):
            _norm_word = _norm_key(_word)
            if _norm_word:
                SC_ALIAS_WORDS.append((_norm_word, len(_norm_alias), _sc_id))


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
                   title=TECH_TITLES.get(tid, tid),
                   category=tech.get("category", ""),
                   tech_type=tech.get("type", ""),
                   wid=tid)
        # Edge: technique → SC
        for sc_id in tech.get("applies_to", []):
            if sc_id in SCS:
                G.add_edge("T:" + tid, "SC:" + sc_id, relation="applies_to")

    # Add SC → technique edges (reverse). Indeks tech_by_sc zawiera także błędy,
    # więc wykluczamy je tutaj, żeby jedna technika nie dostała dwóch krawędzi.
    for sc_id, tech_ids in INDEXES.get("tech_by_sc", {}).items():
        if sc_id not in SCS:
            continue
        failures_here = set(INDEXES.get("failures_by_sc", {}).get(sc_id, []))
        for tid in tech_ids:
            if tid in TECHNIQUES and tid not in failures_here:
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

    # Edge: SC → definition. Bierzemy też exceptions_md, bo dla 17 kryteriów
    # to tam wylądowała treść normatywna (błąd podziału w build_data.py).
    def _sc_haystack(sc):
        return " ".join((
            sc.get("normative_md", ""),
            sc.get("exceptions_md", ""),
            sc.get("understanding_full_md", ""),
        )).lower()

    for sc_id, sc in SCS.items():
        haystack = _sc_haystack(sc)
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
        haystack = _sc_haystack(sc)
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
    """
    Zamień ID ('1.1.1'), slug ('non-text-content') albo tytuł — angielski lub
    polski ('Kontrast (minimalny)') — na ID kryterium sukcesu.
    """
    raw = str(identifier).strip()
    if raw in SCS:
        return raw

    key = _norm_key(raw)
    if not key:
        return None
    if key in SC_BY_NORM:
        return SC_BY_NORM[key]

    # Dopasowanie częściowe: zapytanie musi być początkiem któregoś słowa tytułu
    # lub slugu. Wygrywa najkrótszy alias, przy remisie najniższe ID — żeby wynik
    # był powtarzalny, a nie zależny od kolejności w słowniku.
    # Krótkie klucze pomijamy: "1" to zasada, a nie kryterium (patrz get_hierarchy).
    if len(key) < 3:
        return None
    candidates = [(alias_len, sc_id) for word, alias_len, sc_id in SC_ALIAS_WORDS
                  if word.startswith(key)]
    return min(candidates)[1] if candidates else None


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
    # Bez tego FastMCP trzyma sesję w pamięci instancji. Na Cloud Run przy
    # kilku instancjach i bez session affinity kolejne żądanie tego samego
    # klienta trafia gdzie indziej i dostaje "No valid session ID". Wszystkie
    # narzędzia tutaj są bezstanowe, więc nie tracimy niczego.
    stateless_http=True,
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
    lines.append("")
    lines.append(f'💡 Objaśnienie i przykłady: get_understanding("{sc["id"]}")')
    lines.append(f'🔧 Techniki: get_techniques("{sc["id"]}")')
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
    raw = term.strip()
    words = [w for w in re.split(r"[^a-z0-9]+", raw.lower()) if w]

    # 1. trafienie dokładne, 2. po pominięciu spacji i interpunkcji
    defn = DEFINITIONS.get(raw.lower())
    if not defn:
        exact_norm = next((t for t in DEFINITIONS if _norm_key(t) == _norm_key(raw)), None)
        if exact_norm:
            defn = DEFINITIONS[exact_norm]

    # 3. wszystkie słowa zapytania muszą wystąpić jako pełne słowa hasła —
    #    dopasowanie po podciągu myliło np. "AT" z "focus indic-at-or"
    if not defn and words and any(len(w) > 1 for w in words):
        matches = []
        for candidate in DEFINITIONS:
            cand_words = [w for w in re.split(r"[^a-z0-9]+", candidate.lower()) if w]
            if all(w in cand_words for w in words):
                matches.append((len(cand_words), len(candidate), candidate))
        if matches:
            defn = DEFINITIONS[min(matches)[2]]

    if not defn:
        near = sorted({t for t in DEFINITIONS for w in words if w in t.lower()})[:6]
        hint = f" Podobne hasła: {', '.join(near)}." if near else ""
        return f"Term '{term}' not found.{hint}"
    
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
            lines.append(f"- **{tid}** ({cat}) — {TECH_TITLES.get(tid, '')}")

    if failures:
        lines.append("")
        lines.append("## Common Failures")
        for fid in sorted(failures):
            tech = TECHNIQUES.get(fid, {})
            cat = tech.get("category", "")
            lines.append(f"- **{fid}** ({cat}) — {TECH_TITLES.get(fid, '')}")
    
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
        # Dopasowanie bez względu na wielkość liter i separatory (g18, ARIA-1, @@G210).
        resolved = TECH_BY_NORM.get(_norm_key(tid))
        if resolved:
            tid, tech = resolved, TECHNIQUES[resolved]
    if not tech:
        return (f"Technique '{technique_id}' not found. Expected an id such as "
                f"G18, H37, ARIA1, C45 or F78 — use get_techniques(\"<kryterium>\") "
                f"to list the techniques for a success criterion.")
    
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
    parsed = {}
    for name, raw in (("foreground", foreground), ("background", background)):
        value = raw.strip().lstrip('#')
        if re.fullmatch(r'[0-9A-Fa-f]{3}', value):
            value = ''.join(c * 2 for c in value)   # #fff → #ffffff
        if not re.fullmatch(r'[0-9A-Fa-f]{6}', value):
            return (f"Invalid {name} color '{raw}'. "
                    f"Use 3- or 6-digit hex (e.g. #047857, 047857, #fff).")
        parsed[name] = value.upper()

    fg, bg = parsed["foreground"], parsed["background"]
    ratio = _contrast_ratio(f'#{fg}', f'#{bg}')

    def verdict(threshold):
        return f"{'✅' if ratio >= threshold else '❌'} wymagane {threshold}:1"

    return "\n".join([
        f"# Kontrast: {ratio:.2f}:1",
        "",
        "| | Kolor |",
        "|---|---|",
        f"| Tekst | `#{fg}` |",
        f"| Tło | `#{bg}` |",
        "",
        "## Wynik (WCAG 2.2)",
        "",
        "| Poziom | Tekst zwykły | Tekst duży | Elementy nietekstowe |",
        "|---|---|---|---|",
        f"| **AA** | {verdict(4.5)} | {verdict(3)} | {verdict(3)} |",
        f"| **AAA** | {verdict(7)} | {verdict(4.5)} | — |",
        "",
        "*Tekst duży = od 18 pt (ok. 24 px) lub od 14 pt pogrubiony (ok. 18,66 px).*",
        "*Elementy nietekstowe (1.4.11): komponenty interfejsu i elementy graficzne.*",
    ])


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
    header = f"# Common Failures for {title}\n"
    
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
def get_understanding(identifier: str, full: bool = False) -> str:
    """
    Get the Understanding document for a WCAG 2.2 success criterion.

    By default returns a condensed summary (about 2 KB). Pass full=True for the
    complete W3C document, which can run to 40 KB — ask for it only when the
    summary is not enough.

    Examples: get_understanding("1.4.3"), get_understanding("2.4.11", full=True)
    """
    sc_id = _resolve(identifier) or identifier
    sc = SCS.get(sc_id)

    if not sc:
        return f"SC '{identifier}' not found."

    title = sc.get("title", "")
    pl_title = SC_PL.get(sc_id, "")
    heading = f"# {sc_id} — {title}" + (f"  |  {pl_title}" if pl_title else "")
    url = sc.get("w3c_url", "#")

    short_md = sc.get("understanding_short_md", "")
    full_md = sc.get("understanding_full_md", "")

    if full:
        body = full_md or short_md
        if not body:
            return f"No understanding document for '{identifier}'."
        return f"{heading}\n\n{body}\n\n📖 [Full understanding]({url})"

    if short_md:
        hint = ""
        if full_md and len(full_md) > len(short_md):
            hint = (f'\n\n💡 To streszczenie ({len(short_md)} znaków). '
                    f'Pełny dokument ({len(full_md)} znaków): '
                    f'get_understanding("{sc_id}", full=True)')
        return f"{heading} — streszczenie\n\n{short_md}{hint}\n\n📖 [Full understanding]({url})"

    if full_md:
        return f"{heading}\n\n{full_md}\n\n📖 [Full understanding]({url})"

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
    lines.append('💡 Użyj `get_pattern("nazwa")` aby zobaczyć pełny wzorzec.')

    return "\n".join(lines)


# Wagi bm25 kolumn indeksu: id, type, title, title_pl, level, category, text
_BM25 = "bm25(docs, 5.0, 0.0, 10.0, 10.0, 0.0, 0.0, 1.0)"
_FTS_STRIP = re.compile(r"[^\w-]+", re.UNICODE)
_SEARCH_LIMITS = {"sc": 8, "definition": 4, "technique": 8}
_SEARCH_HEADINGS = {
    "sc": ("🎯", "Kryteria sukcesu"),
    "definition": ("📖", "Definicje"),
    "technique": ("🔧", "Techniki i błędy"),
}


def _fts_query(raw):
    """Zamień zapytanie użytkownika na bezpieczne wyrażenie FTS5 (prefiksowe OR)."""
    words = [w for w in _FTS_STRIP.sub(" ", raw).split() if len(w) > 1]
    return " OR ".join(f'"{w}"*' for w in words)


def _search_fallback(query, started_at):
    """Wyszukiwanie awaryjne, gdy indeks FTS5 jest niedostępny."""
    needle = query.lower()
    scs, techs = [], []

    for sc_id, sc in SCS.items():
        title = sc.get("title", "")
        pl_title = SC_PL.get(sc_id, "")
        haystack = " ".join((title, pl_title, sc.get("normative_md", ""),
                             sc.get("exceptions_md", ""))).lower()
        score = haystack.count(needle) * 2
        if needle in title.lower() or needle in pl_title.lower():
            score += 5
        if score:
            scs.append((score, sc_id, title, pl_title, sc.get("level", "")))

    for tid, tech in TECHNIQUES.items():
        if needle in tid.lower() or needle in tech.get("content_md", "").lower():
            techs.append((tid, tech.get("category", "")))

    scs.sort(reverse=True)
    scs = scs[:_SEARCH_LIMITS["sc"]]
    techs = sorted(techs)[:_SEARCH_LIMITS["technique"]]

    elapsed_ms = (time.time() - started_at) * 1000
    lines = [f'# Search: "{query}" — {len(scs) + len(techs)} matches '
             f'({elapsed_ms:.0f}ms, tryb awaryjny bez indeksu)']
    if scs:
        lines += ["", "## Kryteria sukcesu"]
        for _score, sc_id, title, pl_title, level in scs:
            label = f"{title} / {pl_title}" if pl_title else title
            lines.append(f"🎯 **{sc_id}** — {label} ({level})")
    if techs:
        lines += ["", "## Techniki i błędy"]
        for tid, category in techs:
            lines.append(f"🔧 **{tid}** ({category})")
    if not scs and not techs:
        lines += ["", "Nic nie znaleziono."]
    return "\n".join(lines)


@mcp.tool()
def search(query: str) -> str:
    """
    Search WCAG 2.2 content: success criteria, glossary terms and techniques.

    Full-text search (SQLite FTS5) over the criteria, their Understanding
    summaries, the glossary and the technique summaries. English works
    everywhere; the Polish titles of the success criteria are indexed as well,
    so "kontrast" or "przeciaganie" find the right criterion too. Diacritics
    are optional.

    Examples: "contrast", "keyboard focus", "text alternative", "kontrast"
    Returns matches grouped by kind, each with a snippet showing the hit.
    """
    q = query.strip()
    if not q:
        return "Empty query."

    started_at = time.time()

    if SEARCH_DB is None:
        return _search_fallback(q, started_at)

    fts = _fts_query(q)
    if not fts:
        return f'Query "{query}" contains no searchable words.'

    try:
        rows = SEARCH_DB.execute(
            "SELECT type, id, title, title_pl, level, category,"
            "       snippet(docs, 6, '', '', '…', 14) AS snip,"
            f"      {_BM25} AS score"
            "  FROM docs WHERE docs MATCH ? ORDER BY score LIMIT 60",
            (fts,),
        ).fetchall()
    except Exception as e:
        log.warning(f"search: FTS5 lookup failed for {query!r}: {e}")
        return _search_fallback(q, started_at)

    buckets = {kind: [] for kind in _SEARCH_HEADINGS}
    for row in rows:
        bucket = buckets.get(row[0])
        if bucket is not None and len(bucket) < _SEARCH_LIMITS[row[0]]:
            bucket.append(row)

    total = sum(len(b) for b in buckets.values())
    elapsed_ms = (time.time() - started_at) * 1000
    lines = [f'# Search: "{query}" — {total} matches ({elapsed_ms:.0f}ms)']

    for kind, (icon, heading) in _SEARCH_HEADINGS.items():
        if not buckets[kind]:
            continue
        lines += ["", f"## {heading}"]
        for _t, doc_id, title, title_pl, level, category, snip, _score in buckets[kind]:
            if kind == "sc":
                label = f"{title} / {title_pl}" if title_pl else title
                lines.append(f"{icon} **{doc_id}** — {label} ({level})")
            elif kind == "definition":
                lines.append(f"{icon} **{title}**")
            else:
                lines.append(f"{icon} **{doc_id}** ({category})")
            snip = " ".join(snip.split()) if snip else ""
            if snip:
                lines.append(f"  > {snip}")

    if total == 0:
        lines += ["", "Nic nie znaleziono. Spróbuj innego słowa kluczowego."]

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
    _title = _graph_title(node_id)
    _head = f"{_graph_short(node_id)} — {_title}" if _title else _graph_short(node_id)
    lines = [f"# {_head} ({ntype})"]

    if ntype == "sc":
        lines.append(f"**Poziom:** {node_data.get('level', '')}")
        pl = node_data.get("pl_title", "")
        if pl:
            lines.append(f"**PL:** {pl}")
    elif ntype == "technique":
        lines.append(f"**Kategoria:** {node_data.get('category', '')}  "
                     f"**Typ:** {node_data.get('tech_type', '')}")
    elif ntype == "category":
        lines.append("**Kategoria tematyczna** — grupuje kryteria wokół jednego zagadnienia")
    elif ntype == "pattern":
        lines.append("**Wzorzec deweloperski** — pełna treść: get_pattern(\"%s\")" % node_id[4:])
    elif ntype == "definition":
        lines.append("**Hasło glosariusza**")

    alt = _graph_alt_node(node_id)
    if alt:
        lines.append(f"ℹ️ Istnieje też węzeł o tej nazwie: `{alt}`")

    lines.append("")

    # Grupuj sąsiadów po relacji, zachowując wagę właściwej krawędzi
    to_neighbors, from_neighbors = {}, {}
    for _, neighbor, data in GRAPH.out_edges(node_id, data=True):
        to_neighbors.setdefault(data.get("relation", "?"), []).append(
            (neighbor, data.get("weight")))
    for neighbor, _, data in GRAPH.in_edges(node_id, data=True):
        from_neighbors.setdefault(data.get("relation", "?"), []).append(
            (neighbor, data.get("weight")))

    def render(groups, labels, arrow, heading):
        if not groups:
            return
        lines.append(f"### {heading}")
        for rel, entries in sorted(groups.items()):
            label = labels.get(rel, rel)
            entries = sorted(set(entries), key=lambda e: _graph_sort_key(e[0]))
            shown = entries[:_GRAPH_MAX_NEIGHBOURS]
            for neighbor, weight in shown:
                suffix = f" (wspólnych: {weight})" if weight else ""
                lines.append(f"- {arrow} {label}: {_graph_label(neighbor)}{suffix}")
            if len(entries) > len(shown):
                lines.append(f"- {arrow} {label}: … i {len(entries) - len(shown)} więcej")

    render(to_neighbors, _REL_OUT, "→", "Krawędzie wychodzące")
    render(from_neighbors, _REL_IN, "←", "Krawędzie przychodzące")

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

    lines = [f"# Połączenia: {_graph_label(a)} ↔ {_graph_label(b)}"]

    # Wspólni sąsiedzi
    neighbours_a = set(GRAPH.predecessors(a)) | set(GRAPH.successors(a))
    neighbours_b = set(GRAPH.predecessors(b)) | set(GRAPH.successors(b))
    shared = sorted(neighbours_a & neighbours_b, key=_graph_sort_key)

    if shared:
        lines.append(f"\n### Wspólni sąsiedzi ({len(shared)})")
        by_kind = {}
        for n in shared:
            by_kind.setdefault(GRAPH.nodes[n].get("type", "?"), []).append(n)
        for kind in ("technique", "definition", "category", "pattern", "sc"):
            group = by_kind.get(kind)
            if not group:
                continue
            lines.append(f"\n**{_GRAPH_KIND_NAME.get(kind, kind)}** ({len(group)})")
            for n in group[:_GRAPH_MAX_NEIGHBOURS]:
                lines.append(f"- {_graph_label(n)}")
            if len(group) > _GRAPH_MAX_NEIGHBOURS:
                lines.append(f"- … i {len(group) - _GRAPH_MAX_NEIGHBOURS} więcej")
    else:
        lines.append("\nBrak bezpośrednich wspólnych sąsiadów.")

    # Najkrótsza ścieżka
    try:
        path = nx.shortest_path(GRAPH, a, b)
        lines.append(f"\n### Najkrótsza ścieżka ({len(path) - 1} przeskoków)")
        for i, node in enumerate(path):
            lines.append(f"  {_graph_label(node)}")
            if i < len(path) - 1:
                edge_data = GRAPH.get_edge_data(node, path[i + 1]) or {}
                rel = next(iter(edge_data.values()), {}).get("relation", "→")
                lines.append(f"  ↓ {_REL_OUT.get(rel, rel)}")
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
    """
    Resolve a user-provided string to a graph node ID (prefixed form).

    Kolejność: węzeł podany wprost → kryterium → technika → wzorzec → kategoria.
    Wzorce mają pierwszeństwo przed kategoriami o tej samej nazwie (np. "combobox"),
    bo niosą treść deweloperską; _graph_alt_node() podpowiada tę drugą.
    """
    e = entity.strip()
    if not e:
        return None

    # 1. węzeł podany wprost, z prefiksem
    if e in GRAPH:
        return e

    # 2. kryterium sukcesu — ID, slug, tytuł angielski lub polski
    sc_id = _resolve(e)
    if sc_id and "SC:" + sc_id in GRAPH:
        return "SC:" + sc_id

    # 3. technika — bez względu na wielkość liter i separatory
    tid = TECH_BY_NORM.get(_norm_key(e))
    if tid and "T:" + tid in GRAPH:
        return "T:" + tid

    # 4. wzorzec deweloperski (klucze są zapisane małymi literami)
    pat_key = "PAT:" + e.lower()
    if pat_key in GRAPH:
        return pat_key

    # 5. kategoria tematyczna, bez względu na wielkość liter
    cat_norm = _norm_key(e)
    for cat_name in CATEGORIES:
        if _norm_key(cat_name) == cat_norm:
            return "CAT:" + cat_name

    return None


def _graph_alt_node(node_id: str) -> str | None:
    """Węzeł o tej samej nazwie w drugiej rodzinie (wzorzec ↔ kategoria)."""
    if node_id.startswith("PAT:"):
        name = node_id[4:]
        for cat_name in CATEGORIES:
            if _norm_key(cat_name) == _norm_key(name):
                return "CAT:" + cat_name
    elif node_id.startswith("CAT:"):
        pat_key = "PAT:" + node_id[4:].lower()
        if pat_key in GRAPH:
            return pat_key
    return None


# Ile sąsiadów jednej relacji wypisać, zanim skrócimy listę
_GRAPH_MAX_NEIGHBOURS = 12

_GRAPH_KIND_LABEL = {"sc": "SC", "technique": "T", "category": "KAT",
                     "definition": "DEF", "pattern": "WZ"}

_GRAPH_KIND_NAME = {"sc": "Kryteria sukcesu", "technique": "Techniki",
                    "category": "Kategorie", "definition": "Definicje",
                    "pattern": "Wzorce"}

# Etykiety zależą od kierunku krawędzi — wcześniej jedna mapa opisywała oba,
# przez co krawędzie wychodzące dostawały opis przychodzących.
_REL_OUT = {
    "applies_to": "dotyczy kryterium",
    "has_technique": "ma technikę",
    "has_failure": "ma błąd (failure)",
    "in_category": "należy do kategorii",
    "in_pattern": "występuje we wzorcu",
    "has_sc": "zawiera kryterium",
    "related_to": "powiązana technika",
    "references": "odwołuje się do definicji",
    "shares_techniques": "dzieli techniki z",
    "shares_definitions": "dzieli definicje z",
}

_REL_IN = {
    "applies_to": "jest wskazywane przez technikę",
    "has_technique": "jest techniką dla",
    "has_failure": "jest błędem dla",
    "in_category": "kategoria obejmuje",
    "in_pattern": "wzorzec obejmuje",
    "has_sc": "należy do",
    "related_to": "jest wskazywana przez",
    "references": "jest przywoływana przez",
    "shares_techniques": "dzieli techniki z",
    "shares_definitions": "dzieli definicje z",
}


def _graph_title(nid: str) -> str:
    """Nazwa węzła do wyświetlenia; pusta, gdy powtarzałaby identyfikator."""
    nd = GRAPH.nodes.get(nid, {})
    title = nd.get("title") or nd.get("term") or ""
    return "" if _norm_key(title) == _norm_key(_graph_short(nid)) else title


def _graph_label(nid: str) -> str:
    """'SC 1.4.3 Contrast (Minimum)' — identyfikator z nazwą, jeśli wnosi coś nowego."""
    kind = _GRAPH_KIND_LABEL.get(GRAPH.nodes.get(nid, {}).get("type", ""), "?")
    title = _graph_title(nid)
    label = f"**{kind} {_graph_short(nid)}**"
    return f"{label} {title}" if title else label


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


def _subsystem_status_lines():
    """
    Stan podsystemów opcjonalnych — pozwala po wdrożeniu jednym spojrzeniem sprawdzić,
    czy obraz zawiera networkx i indeks embeddings/search.db.
    """
    def mark(active):
        return "✅" if active else "❌"

    graph_desc = (f"{GRAPH.number_of_nodes()} węzłów, {GRAPH.number_of_edges()} krawędzi"
                  if GRAPH is not None else "WYŁĄCZONY — brak networkx")

    if SEARCH_DB is None:
        fts_desc = "WYŁĄCZONY — brak embeddings/search.db, search() działa awaryjnie"
    else:
        counts = dict(SEARCH_DB.execute("SELECT type, count(*) FROM docs GROUP BY type"))
        fts_desc = (f"{sum(counts.values())} dokumentów "
                    f"({counts.get('sc', 0)} SC, {counts.get('definition', 0)} definicji, "
                    f"{counts.get('technique', 0)} technik)")

    return [
        f"{mark(GRAPH is not None)} Graf wiedzy:  {graph_desc}",
        f"{mark(SEARCH_DB is not None)} Indeks FTS5:  {fts_desc}",
    ]


def main():
    parser = argparse.ArgumentParser(description="WCAG 2.2 MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse", "streamable-http"], default="stdio",
                        help="Transport protocol (default: stdio)")
    parser.add_argument("--host", default="127.0.0.1",
                        help="Host to bind (SSE/HTTP only, default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=9099,
                        help="Port to bind (SSE/HTTP only, default: 9099)")
    parser.add_argument("--api-key", default="",
                        help="API key for authentication. Also read from WCAG22_API_KEY env var.")
    args = parser.parse_args()

    # Resolve API key: arg > env var > no auth
    api_key = args.api_key or os.environ.get("WCAG22_API_KEY", "")

    def banner(line):
        """
        Baner startowy. W Cloud Run log.info trafia na stderr, więc dodatkowy
        print tylko by go zdublował; lokalnie stderr przyjmuje dopiero ostrzeżenia,
        więc print jest jedynym sposobem, żeby użytkownik to zobaczył.
        """
        log.info(line)
        if not IN_CLOUD_RUN:
            print(line, file=sys.stderr)

    log_target = "stderr (Cloud Run)" if IN_CLOUD_RUN else (LOG_FILE or "stderr")

    banner("=" * 72)
    banner(f"  🚀 SERVER START  |  {_fmt_ts()}")
    banner(f"  Dane: {COUNTS['scs']} SC, {COUNTS['techniques']} technik, "
           f"{COUNTS['definitions']} definicji, {COUNTS['understanding']} dokumentów")
    banner(f"  Transport: {args.transport}  |  Log: {log_target}")
    for _line in _subsystem_status_lines():
        banner(f"  {_line}")
    if api_key:
        banner("  🔒 API key: włączony (klient musi wysłać nagłówek X-API-Key)")
    else:
        banner("  🔓 API key: wyłączony — serwer jest otwarty")
    banner("=" * 72)

    if args.transport == "sse":
        import uvicorn
        from starlette.middleware.base import BaseHTTPMiddleware
        
        sse_app = mcp.sse_app()
        
        class NoBufferMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request, call_next):
                # Check API key for SSE
                if api_key:
                    request_key = request.headers.get("x-api-key", "")
                    if request_key != api_key:
                        from starlette.responses import JSONResponse
                        log.warning(f"  🔒 ODRZUCONE (401) | {_fmt_ts()} | SSE | {request.client.host if request.client else '?'}")
                        return JSONResponse(
                            {"error": "Unauthorized", "message": "Missing or invalid API key."},
                            status_code=401,
                        )
                response = await call_next(request)
                response.headers["X-Accel-Buffering"] = "no"
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Connection"] = "keep-alive"
                return response
        
        app = NoBufferMiddleware(sse_app)
        banner(f"  Nasłuch: http://{args.host}:{args.port}/sse")
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    
    elif args.transport == "streamable-http":
        import uvicorn
        raw_app = mcp.streamable_http_app()
        # Kolejność: API key (zewnętrzna) → logowanie → aplikacja MCP
        app = APIKeyMiddleware(MCPLogMiddleware(raw_app), api_key)
        banner(f"  Nasłuch: http://{args.host}:{args.port}/mcp")
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    
    else:
        # stdio — logowanie ograniczone (brak łatwego hooka w MCP stdio)
        log.warning("  Tryb stdio — logowanie żądań tylko na poziomie serwera")
        banner(f"  Tryb stdio. Log: {log_target}")
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
