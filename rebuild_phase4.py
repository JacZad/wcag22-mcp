#!/usr/bin/env python3
"""
Phase 4: Clean technique summaries, embed with nomic-embed-text, build search index.
Reads: embeddings/tech_summaries_new.json (or falls back to existing)
Writes: embeddings/tech_embeddings.npy, embeddings/tech_index.json
Also rebuilds FTS5 search.db for SCs + definitions.
"""

import json, re, time, sqlite3, sys
from pathlib import Path

SUMMARIES_NEW = "embeddings/tech_summaries_new.json"
DATA = "wcag-data.json"
OUT_DIR = Path("embeddings")

print("=" * 60)
print("Phase 4: Embed + build search index")
print("=" * 60)

# ── Load summaries ──
try:
    with open(SUMMARIES_NEW) as f:
        data = json.load(f)
    results = data["results"]
    print(f"Loaded {len(results)} new summaries from {SUMMARIES_NEW}")
except FileNotFoundError:
    # Fallback: use existing embeddings-data.json
    print(f"  {SUMMARIES_NEW} not found, falling back to embeddings-data.json")
    with open(OUT_DIR / "embeddings-data.json") as f:
        old = json.load(f)
    results = []
    for key, t in old.get("summaries", {}).items():
        if t.get("type") == "technique":
            results.append({
                "id": t["id"],
                "type": "technique",
                "category": t.get("category", ""),
                "applies_to": [],
                "sc_context": "",
                "summary": t.get("summary", ""),
                "content_len": 0,
            })
    print(f"Loaded {len(results)} existing summaries")

# ── Build FTS5 (same as before) ──
with open(DATA) as f:
    wcag = json.load(f)

print("\nBuilding FTS5 for SCs + definitions...")
t0 = time.time()

db_path = OUT_DIR / "search.db"
if db_path.exists():
    db_path.unlink()

conn = sqlite3.connect(str(db_path))
conn.execute("CREATE VIRTUAL TABLE docs USING fts5(id, type, title, level, text, tokenize='porter ascii')")

for sc_id, sc in wcag["scs"].items():
    title = sc.get("title", "")
    level = sc.get("level", "")
    conn.execute(
        "INSERT INTO docs (id, type, title, level, text) VALUES (?, ?, ?, ?, ?)",
        (sc_id, "sc", title, level, title)
    )

for term, defn in wcag.get("definitions", {}).items():
    if isinstance(defn, dict):
        text = defn.get("definition", "") or defn.get("definition_md", "")
    else:
        text = str(defn)
    conn.execute(
        "INSERT INTO docs (id, type, title, level, text) VALUES (?, ?, ?, ?, ?)",
        (term, "definition", term, "", text)
    )

conn.commit()
conn.execute("INSERT INTO docs(docs) VALUES('optimize')")
conn.close()
print(f"  FTS5: {len(wcag['scs'])} SCs + {len(wcag['definitions'])} definitions ({time.time()-t0:.1f}s)")

# ── Clean summaries + embed ──
print(f"\nCleaning {len(results)} technique summaries...")

tech_items = []
tech_texts = []

for r in results:
    raw = r.get("summary", "").strip()
    if not raw or len(raw) < 20:
        continue
    
    # Clean: remove boilerplate heading
    cleaned = re.sub(
        r'^##\s*(?:Summary\s+of\s+)?WCAG\s+Technique\s*\S*\s*(?:\([^)]*\))?:\s*.*?\n\n?',
        '', raw, count=1, flags=re.MULTILINE
    )
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    cleaned = re.sub(r' {2,}', ' ', cleaned).strip()
    
    embed_text = cleaned if len(cleaned) > 50 else raw
    
    tech_items.append({
        "id": r["id"],
        "applies_to": r.get("applies_to", []),
        "summary": raw,
        "embed_text": embed_text,
    })
    tech_texts.append(embed_text)

print(f"  {len(tech_items)} techniques to embed ({sum(1 for i in tech_items if i['applies_to'])} with SC metadata)")

# Embed with nomic
print(f"\nEmbedding with nomic-embed-text...")
t0 = time.time()

import urllib.request

BATCH_SIZE = 10
all_embeddings = []

for i in range(0, len(tech_texts), BATCH_SIZE):
    batch = tech_texts[i:i+BATCH_SIZE]
    body = json.dumps({
        "model": "nomic-embed-text",
        "input": batch,
    }).encode()
    
    req = urllib.request.Request(
        "http://localhost:11434/api/embed", body,
        {"Content-Type": "application/json"}
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
    
    embs = result.get("embeddings", [])
    all_embeddings.extend(embs)
    
    if (i + BATCH_SIZE) % 50 == 0 or i + BATCH_SIZE >= len(tech_texts):
        print(f"  ... {min(i+BATCH_SIZE, len(tech_texts))}/{len(tech_texts)}")

embed_elapsed = time.time() - t0
print(f"  Embedded {len(all_embeddings)} in {embed_elapsed:.1f}s")

# Save
import numpy as np

emb_array = np.array(all_embeddings, dtype=np.float32)
np.save(OUT_DIR / "tech_embeddings.npy", emb_array)

with open(OUT_DIR / "tech_index.json", "w") as f:
    json.dump({
        "model": "nomic-embed-text",
        "dim": emb_array.shape[1],
        "count": len(tech_items),
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "items": tech_items,
    }, f, indent=2, ensure_ascii=False)

with_meta = sum(1 for i in tech_items if i['applies_to'])
print(f"\nSaved:")
print(f"  {OUT_DIR / 'tech_embeddings.npy'} ({emb_array.shape})")
print(f"  {OUT_DIR / 'tech_index.json'} ({len(tech_items)} items, {with_meta} with SC metadata)")
print(f"  {OUT_DIR / 'search.db'} (FTS5)")
print(f"Total: {time.time()-t0:.1f}s")
