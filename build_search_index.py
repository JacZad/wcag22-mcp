#!/usr/bin/env python3
"""
build_search_index.py — Build the FTS5 search index (embeddings/search.db).

Indexes four kinds of documents into a single FTS5 table:

  sc          success criteria — English title, Polish title, normative text,
              exceptions and the short Understanding summary
  definition  glossary terms
  technique   techniques and failures — id, category, applied SCs and the
              technique body
  aria        WAI-ARIA 1.2 roles, states and properties — RFC 2119
              statements and definition (from aria-data.json, if present)

The Polish titles are read straight out of server.py so there is one source of
truth for them. Queries therefore work in both languages.

Usage:
  python3 build_search_index.py
"""

import ast
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "wcag-data.json"
ARIA_DATA = ROOT / "aria-data.json"
SERVER = ROOT / "server.py"
INDEX_DIR = ROOT / "embeddings"

INDEX_DIR.mkdir(exist_ok=True)


def load_sc_pl():
    """
    Read the SC_PL dict out of server.py without importing it.

    Importing would load the whole server, which opens search.db and on Windows
    would block us from replacing the file we are about to rebuild.
    """
    tree = ast.parse(SERVER.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "SC_PL":
                    return ast.literal_eval(node.value)
    raise RuntimeError("SC_PL not found in server.py")


def strip_markdown(md, limit=1500):
    """Flatten markdown to plain-ish text so FTS tokens are not stuck to syntax."""
    text = re.sub(r"```.*?```", " ", md, flags=re.DOTALL)
    text = re.sub(r"[#*`>\[\]()|_]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()[:limit]


def build():
    with open(DATA, encoding="utf-8") as f:
        wcag = json.load(f)

    scs = wcag["scs"]
    definitions = wcag["definitions"]
    techniques = wcag["techniques"]
    sc_pl = load_sc_pl()

    db_path = INDEX_DIR / "search.db"

    # Budujemy w pamięci i kopiujemy przez backup API zamiast kasować plik:
    # na Windows działający serwer trzyma search.db otwarty i unlink() się wywraca.
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE VIRTUAL TABLE docs USING fts5("
        "  id,"
        "  type UNINDEXED,"
        "  title,"
        "  title_pl,"
        "  level UNINDEXED,"
        "  category UNINDEXED,"
        "  text,"
        "  tokenize='porter unicode61 remove_diacritics 2'"
        ")"
    )

    def add(doc_id, doc_type, title, title_pl, level, category, text):
        conn.execute(
            "INSERT INTO docs (id, type, title, title_pl, level, category, text)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (doc_id, doc_type, title, title_pl, level, category, text.strip()),
        )

    # ── success criteria ──
    n_sc = 0
    for sc_id, sc in scs.items():
        parts = [
            sc.get("title", ""),
            strip_markdown(sc.get("normative_md", "")),
            strip_markdown(sc.get("items_md", "")),
            strip_markdown(" ".join(sc.get("notes", []))),
            strip_markdown(sc.get("understanding_short_md", "")),
        ]
        text = "\n".join(p for p in parts if p)
        if text.strip():
            add(sc_id, "sc", sc.get("title", ""), sc_pl.get(sc_id, ""),
                sc.get("level", ""), "", text)
            n_sc += 1

    # ── glossary ──
    n_def = 0
    for term, defn in definitions.items():
        body = defn.get("definition_md", "") if isinstance(defn, dict) else str(defn)
        display = defn.get("term", term) if isinstance(defn, dict) else term
        text = f"{display}\n{strip_markdown(body)}"
        if text.strip():
            add(term, "definition", display, "", "", "", text)
            n_def += 1

    # ── techniques and failures ──
    n_tech = 0
    for tid, tech in techniques.items():
        applied = []
        for sc_id in tech.get("applies_to", []):
            sc = scs.get(sc_id, {})
            applied.append(f"{sc_id} {sc.get('title', '')} {sc_pl.get(sc_id, '')}".strip())

        body = strip_markdown(tech.get("content_md", ""))

        parts = [tid, tech.get("category", ""), " ".join(applied), body]
        text = "\n".join(p for p in parts if p)
        if text.strip():
            add(tid, "technique", tid, "", "", tech.get("category", ""), text)
            n_tech += 1

    # ── WAI-ARIA 1.2 roles, states and properties (build_aria.py) ──
    n_aria = 0
    if ARIA_DATA.exists():
        aria = json.loads(ARIA_DATA.read_text(encoding="utf-8"))
        for entry in [*aria["roles"].values(), *aria["attributes"].values()]:
            rfc = " ".join(f"{st['keyword']}: {st['text']}" for st in entry["rfc"])
            parts = [entry["name"], entry["kind"], rfc, strip_markdown(entry["description_md"])]
            add(entry["name"], "aria", entry["name"], "", "", entry["kind"],
                "\n".join(p for p in parts if p))
            n_aria += 1

    conn.commit()
    conn.execute("INSERT INTO docs(docs) VALUES('optimize')")
    conn.commit()
    conn.isolation_level = None  # VACUUM cannot run inside a transaction
    conn.execute("VACUUM")
    dest = sqlite3.connect(str(db_path))
    conn.backup(dest)
    dest.close()
    conn.close()

    size_kb = db_path.stat().st_size / 1024
    print(f"  SCs:         {n_sc}")
    print(f"  Definitions: {n_def}")
    print(f"  Techniques:  {n_tech}")
    print(f"  ARIA:        {n_aria}")
    print(f"  Written:     {db_path} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    t0 = time.time()
    print("=" * 50)
    print("FTS5 index rebuild")
    print("=" * 50)
    build()
    print(f"\nDone in {time.time() - t0:.1f}s")
