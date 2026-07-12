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

        async def passthrough_send(msg):
            """Przepuść odpowiedź bez buforowania (streamable HTTP używa chunked encoding)."""
            await send(msg)

        try:
            await self.app(scope, replay_receive, passthrough_send)
        except Exception as e:
            elapsed_ms = int((time.time() - start) * 1000)
            log_response(tool_name, elapsed_ms, "", error=str(e))
            raise

        elapsed_ms = int((time.time() - start) * 1000)
        # Log response — tylko statystyki, treść pomijamy (chunked streaming)
        if tool_name:
            log.info(f"  📤 ODPOWIEDŹ  |  {_fmt_ts()}  |  ✅ OK  |  {elapsed_ms}ms")
            log.info("=" * 72)


# ── Load data ──

DATA_PATH = Path(__file__).parent / "wcag-data.json"

with open(DATA_PATH) as f:
    DATA = json.load(f)

SCS = DATA["scs"]
TECHNIQUES = DATA["techniques"]
DEFINITIONS = DATA["definitions"]
UNDERSTANDING = DATA["understanding"]
PRINCIPLES = DATA["principles"]
GUIDELINES = DATA["guidelines"]
INDEXES = DATA["indexes"]
COUNTS = DATA["counts"]

# Build reverse maps
SC_ID_TO_SLUG = {sc["id"]: sc["slug"] for sc in SCS.values()}
SLUG_TO_SC_ID = {sc["slug"]: sc["id"] for sc in SCS.values()}


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
    lines = [
        f"# {sc['id']} — {sc['title']}",
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
    Returns a list of sufficient/advisory techniques and common failures.
    """
    sc_id = _resolve(identifier) or identifier
    sc = SCS.get(sc_id, {})
    
    title = f"{sc.get('id', '')} — {sc.get('title', identifier)}" if sc else identifier
    header = f"# Techniques for {title}\n"
    
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
    
    return "\n".join(lines)


@mcp.tool()
def get_failures(identifier: str) -> str:
    """
    Get common failures for a WCAG 2.2 success criterion.
    
    Examples: "1.3.2", "focus-visible", "2.4.7"
    """
    sc_id = _resolve(identifier) or identifier
    sc = SCS.get(sc_id, {})
    
    title = f"{sc.get('id', '')} — {sc.get('title', identifier)}" if sc else identifier
    header = f"# Common Failures for {title}\n"
    
    failures = INDEXES.get("failures_by_sc", {}).get(sc_id, [])
    
    if not failures:
        return header + "\nNo documented failures for this success criterion."
    
    lines = [header]
    for fid in sorted(failures):
        tech = TECHNIQUES.get(fid, {})
        lines.append(f"- **{fid}** ({tech.get('category', '')})")
    
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
    
    slug = sc["slug"]
    
    if sc.get("understanding_md"):
        return f"# {sc.get('title', '')}\n\n{sc['understanding_md']}\n\n📖 [Full understanding]({sc.get('w3c_url', '#')})"
    
    und = UNDERSTANDING.get(slug)
    if und:
        return f"# {sc.get('title', '')}\n\n{und['full_md']}\n\n📖 [Full understanding]({sc.get('w3c_url', '#')})"
    
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
def search(query: str) -> str:
    """
    Search across all WCAG 2.2 content: success criteria, definitions, and techniques.
    
    Examples: "contrast", "keyboard focus", "text alternative"
    Returns matching results with snippets.
    """
    q = query.lower().strip()
    if not q:
        return "Empty query."
    
    results = []
    
    # SCs — use search_index for fast lookup + fallback to text search
    words = q.split()
    matched_ids = set()
    for word in words:
        if word in INDEXES.get("search_index", {}):
            matched_ids.update(INDEXES["search_index"][word])
    
    # Also text-search through all SCs
    for sc_id, sc in SCS.items():
        if sc_id in matched_ids:
            score = 5
        else:
            haystack = (sc.get("title", "") + " " + sc.get("normative_md", "")).lower()
            score = haystack.count(q) * 2
            if q in sc.get("title", "").lower():
                score += 5
        if score > 0:
            results.append({
                "type": "sc", "id": sc_id,
                "title": sc.get("title", ""),
                "level": sc.get("level", ""),
                "snippet": _snippet(sc.get("normative_md", ""), query),
                "score": score,
            })
    
    # Definitions
    for term, defn in DEFINITIONS.items():
        if q in term:
            results.append({
                "type": "definition", "id": term,
                "title": defn.get("term", ""),
                "snippet": _snippet(defn.get("definition_md", ""), query),
                "score": 4,
            })
    
    # Techniques
    for tid, tech in list(TECHNIQUES.items())[:100]:
        if q in tid.lower() or q in tech.get("content_md", "").lower()[:200]:
            results.append({
                "type": "technique", "id": tid,
                "title": f"{tid} ({tech.get('category', '')})",
                "score": 2,
            })
    
    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:20]
    
    lines = [f"# Search results for \"{query}\" ({len(results)} matches)\n"]
    for r in results:
        icon = {"sc": "🎯", "definition": "📖", "technique": "🔧"}.get(r["type"], "•")
        if r["type"] == "sc":
            lines.append(f"{icon} **{r['id']}** — {r['title']} ({r.get('level', '')})")
        elif r["type"] == "definition":
            lines.append(f"{icon} **{r['title']}**")
        elif r["type"] == "technique":
            lines.append(f"{icon} **{r['id']}**")
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
        f"**Data size:** {os.path.getsize(DATA_PATH) / 1024:.0f} KB\n"
        f"\n"
        f"### Tools\n"
        f"- `get_sc(identifier)` — Get a success criterion\n"
        f"- `get_definition(term)` — Get a term definition\n"
        f"- `get_techniques(identifier)` — Get techniques for an SC\n"
        f"- `get_failures(identifier)` — Get failures for an SC\n"
        f"- `get_understanding(identifier)` — Get understanding doc\n"
        f"- `get_principle(id)` — Get a principle (1-4)\n"
        f"- `get_guideline(id)` — Get a guideline (e.g. 2.4)\n"
        f"- `list_scs(level)` — List SCs, filter by A/AA/AAA\n"
        f"- `search(query)` — Search across all content\n"
        f"- `status()` — This status message"
    )


# ─── Main ───

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
