#!/usr/bin/env python3
"""Final step: load gemma4:e2b summaries, attach SC mapping from W3C scrape, embed with nomic."""

import json, re, time, sqlite3, sys
from pathlib import Path

GEMMA_SUMMARIES = "embeddings/tech_summaries_gemma.json"
MAPPING = "embeddings/sc_tech_mapping.json"
DATA = "wcag-data.json"
OUT_DIR = Path("embeddings")

print("=" * 60)
print("Final: gemma summaries + W3C mapping → embed")
print("=" * 60)

# Load
with open(GEMMA_SUMMARIES) as f:
    gemma = json.load(f)
with open(MAPPING) as f:
    map_data = json.load(f)
with open(DATA) as f:
    wcag = json.load(f)

scs = wcag["scs"]
results = gemma["results"]
tech_to_scs = map_data["tech_to_scs"]
sc_to_techs = map_data["sc_to_techs"]

print(f"Gemma summaries: {len(results)}")
print(f"SC→technique mapping: {len(sc_to_techs)} SCs, {sum(len(v) for v in sc_to_techs.values())} edges")
print(f"Technique→SC mapping: {len(tech_to_scs)} techniques")

# ── Build FTS5 ──
print("\nBuilding FTS5...")
t0 = time.time()
db_path = OUT_DIR / "search.db"
if db_path.exists():
    db_path.unlink()
conn = sqlite3.connect(str(db_path))
conn.execute("CREATE VIRTUAL TABLE docs USING fts5(id, type, title, level, text, tokenize='porter ascii')")
for sc_id, sc in wcag["scs"].items():
    conn.execute("INSERT INTO docs (id, type, title, level, text) VALUES (?, ?, ?, ?, ?)",
                 (sc_id, "sc", sc.get("title",""), sc.get("level",""), sc.get("title","")))
for term, defn in wcag.get("definitions", {}).items():
    text = defn.get("definition", "") if isinstance(defn, dict) else str(defn)
    conn.execute("INSERT INTO docs (id, type, title, level, text) VALUES (?, ?, ?, ?, ?)",
                 (term, "definition", term, "", text))
conn.commit()
conn.execute("INSERT INTO docs(docs) VALUES('optimize')")
conn.close()
print(f"  FTS5: {len(wcag['scs'])} SCs + {len(wcag['definitions'])} defs ({time.time()-t0:.1f}s)")

# ── Clean + attach SC metadata ──
print(f"\nCleaning {len(results)} gemma summaries...")
tech_items = []
tech_texts = []

for r in results:
    tid = r["id"]
    raw = r.get("summary", "").strip()
    if not raw or len(raw) < 20:
        continue
    
    # Attach SC mapping from W3C scrape
    sc_ids = tech_to_scs.get(tid, [])
    applies_to = []
    for sc_id in sc_ids:
        sc = scs.get(sc_id, {})
        applies_to.append({
            "sc_id": sc_id,
            "title": sc.get("title", ""),
            "level": sc.get("level", ""),
        })
    
    # Clean: remove boilerplate heading
    cleaned = re.sub(
        r'^##\s*(?:Summary\s+of\s+)?WCAG\s+Technique\s*\S*\s*(?:\([^)]*\))?:\s*.*?\n\n?',
        '', raw, count=1, flags=re.MULTILINE
    )
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    cleaned = re.sub(r' {2,}', ' ', cleaned).strip()
    embed_text = cleaned if len(cleaned) > 50 else raw
    
    tech_items.append({
        "id": tid,
        "category": r.get("category", ""),
        "applies_to": applies_to,
        "summary": raw,
        "embed_text": embed_text,
    })
    tech_texts.append(embed_text)

with_meta = sum(1 for i in tech_items if i['applies_to'])
without_meta = sum(1 for i in tech_items if not i['applies_to'])
print(f"  {len(tech_items)} to embed ({with_meta} with SC, {without_meta} without)")

# ── Embed with nomic ──
print(f"\nEmbedding with nomic-embed-text...")
t0 = time.time()
import urllib.request

BATCH_SIZE = 10
all_embeddings = []
for i in range(0, len(tech_texts), BATCH_SIZE):
    batch = tech_texts[i:i+BATCH_SIZE]
    body = json.dumps({"model": "nomic-embed-text", "input": batch}).encode()
    req = urllib.request.Request("http://localhost:11434/api/embed", body, {"Content-Type": "application/json"})
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
    if (i + BATCH_SIZE) % 50 == 0 or i + BATCH_SIZE >= len(tech_texts):
        print(f"  ... {min(i+BATCH_SIZE, len(tech_texts))}/{len(tech_texts)}")

elapsed = time.time() - t0
print(f"  Embedded {len(all_embeddings)} in {elapsed:.1f}s")

# ── Save ──
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

print(f"\nSaved:")
print(f"  {OUT_DIR / 'tech_embeddings.npy'} ({emb_array.shape})")
print(f"  {OUT_DIR / 'tech_index.json'} ({len(tech_items)} items)")
print(f"  With SC metadata: {with_meta}/{len(tech_items)}")
print(f"  Unique SCs: {len(set(s['sc_id'] for i in tech_items for s in i['applies_to']))}")
print(f"Total: {time.time()-t0:.1f}s")
