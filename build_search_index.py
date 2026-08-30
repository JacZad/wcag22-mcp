#!/usr/bin/env python3
"""
build_search_index.py — Rebuild search indices for WCAG 2.2 MCP Server.

1. FTS5 (search.db) — rebuilds with understanding_short_md as SC text
2. Understanding embeddings (nomic-embed-text) — for semantic search

Usage:
  python3 build_search_index.py          # rebuild both
  python3 build_search_index.py --fts5   # FTS5 only
  python3 build_search_index.py --embed  # embeddings only
"""

import json
import re
import sqlite3
import sys
import time
from pathlib import Path

DATA = Path(__file__).parent / "wcag-data.json"
EMBED_DIR = Path(__file__).parent / "embeddings"
EMBED_DIR.mkdir(exist_ok=True)

# ── Load data ──
print("Loading data...")
with open(DATA) as f:
    wcag = json.load(f)

scs = wcag["scs"]
definitions = wcag["definitions"]
techniques = wcag["techniques"]

# ── 1. FTS5 ──
def build_fts5():
    db_path = EMBED_DIR / "search.db"
    if db_path.exists():
        db_path.unlink()
        print("  Removed old search.db")

    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "CREATE VIRTUAL TABLE docs USING fts5("
        "id, type, title, level, text, "
        "tokenize='porter ascii')"
    )

    n_scs = 0
    for sc_id, sc in scs.items():
        short_md = sc.get("understanding_short_md", "")
        # Combine title + understanding_short_md for richer searching
        text = sc.get("title", "") + "\n" + short_md
        if text.strip():
            conn.execute(
                "INSERT INTO docs (id, type, title, level, text) VALUES (?, ?, ?, ?, ?)",
                (sc_id, "sc", sc.get("title", ""), sc.get("level", ""), text.strip()),
            )
            n_scs += 1

    n_defs = 0
    for term, defn in definitions.items():
        text = defn.get("definition_md", "") if isinstance(defn, dict) else str(defn)
        if text.strip():
            conn.execute(
                "INSERT INTO docs (id, type, title, level, text) VALUES (?, ?, ?, ?, ?)",
                (term, "definition", term, "", text.strip()),
            )
            n_defs += 1

    conn.commit()
    conn.execute("INSERT INTO docs(docs) VALUES('optimize')")
    conn.close()
    print(f"  FTS5: {n_scs} SCs + {n_defs} definitions")


# ── 2. Understanding embeddings ──
def build_understanding_embeddings():
    import numpy as np
    import urllib.request

    # Collect understanding texts
    items = []
    texts = []
    for sc_id, sc in scs.items():
        short_md = sc.get("understanding_short_md", "").strip()
        if len(short_md) < 20:
            continue
        items.append({
            "id": sc_id,
            "title": sc.get("title", ""),
            "level": sc.get("level", ""),
            "text_len": len(short_md),
            "short_md": short_md,
        })
        texts.append(short_md)

    print(f"  Understanding docs to embed: {len(items)}")

    if not items:
        print("  No understanding docs to embed — done.")
        return

    BATCH_SIZE = 10
    all_embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        body = json.dumps({"model": "nomic-embed-text", "input": batch}).encode()
        req = urllib.request.Request(
            "http://localhost:11434/api/embed",
            body,
            {"Content-Type": "application/json"},
        )
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    result = json.loads(resp.read())
                break
            except Exception as e:
                if attempt == 2:
                    print(f"  Error at batch {i}: {e}")
                    sys.exit(1)
                time.sleep(2)
        all_embeddings.extend(result.get("embeddings", []))
        if (i + BATCH_SIZE) % 30 == 0 or i + BATCH_SIZE >= len(texts):
            print(f"  ... {min(i + BATCH_SIZE, len(texts))}/{len(texts)}")

    emb_array = np.array(all_embeddings, dtype=np.float32)
    np.save(EMBED_DIR / "und_embeddings.npy", emb_array)

    with open(EMBED_DIR / "und_index.json", "w") as f:
        json.dump(
            {
                "model": "nomic-embed-text",
                "dim": emb_array.shape[1],
                "count": len(items),
                "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
                "items": items,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"  Saved: {EMBED_DIR / 'und_embeddings.npy'} ({emb_array.shape})")
    print(f"  Saved: {EMBED_DIR / 'und_index.json'} ({len(items)} items)")


# ── Main ──
if __name__ == "__main__":
    do_fts5 = True
    do_embed = True

    if len(sys.argv) > 1:
        do_fts5 = "--fts5" in sys.argv
        do_embed = "--embed" in sys.argv

    t0 = time.time()

    if do_fts5:
        print("=" * 50)
        print("FTS5 rebuild")
        print("=" * 50)
        build_fts5()

    if do_embed:
        print()
        print("=" * 50)
        print("Understanding embeddings")
        print("=" * 50)
        build_understanding_embeddings()

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s")
