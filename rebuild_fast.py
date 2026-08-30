#!/usr/bin/env python3
"""
Fast track: take existing embeddings-data.json summaries, attach SC metadata, clean, embed.
"""

import json, re, time, sqlite3, sys
from pathlib import Path

EXISTING = "embeddings/embeddings-data.json"
DATA = "wcag-data.json"
OUT_DIR = Path("embeddings")

print("Loading data...")
with open(EXISTING) as f:
    old = json.load(f)

with open(DATA) as f:
    wcag = json.load(f)

techs = wcag["techniques"]
scs = wcag["scs"]

# Build SC mapping
from collections import defaultdict
sc_by_tech = defaultdict(list)
tbs = wcag.get("indexes", {}).get("tech_by_sc", {})
for raw_sc_id, refs in tbs.items():
    if re.match(r'^\d+\.\d+\.\d+$', raw_sc_id):
        for tid in refs:
            if tid in techs:
                sc_by_tech[tid].append(raw_sc_id)

# Source content_md for more refs
sc_ref = re.compile(r'(?:Success Criterion|success criterion)\s+(\d+\.\d+\.\d+)', re.IGNORECASE)
for tid, t in techs.items():
    for sc_id in sc_ref.findall(t.get("content_md", "")):
        if sc_id not in sc_by_tech[tid]:
            sc_by_tech[tid].append(sc_id)

# Understanding docs
understanding = wcag.get("understanding", {})
tech_pat = re.compile(r'(G|ARIA|H|C|F|SCR|PDF|SVR|SMIL|T|SL|FLASH|PDF)(\d+)')
for slug, u in understanding.items():
    sc_id = u.get("sc_id", "")
    if not re.match(r"^\d+\.\d+\.\d+$", str(sc_id)):
        continue
    for prefix, num in tech_pat.findall(u.get("full_md", "")):
        tid = prefix + num
        if tid in techs and sc_id not in sc_by_tech[tid]:
            sc_by_tech[tid].append(sc_id)

# Deduplicate
for tid in sc_by_tech:
    sc_by_tech[tid] = sorted(set(sc_by_tech[tid]))

print(f"SC mapping: {len(sc_by_tech)} techniques ({sum(len(v) for v in sc_by_tech.values())} edges)")

# Build results
results = []
for key, t in old.get("summaries", {}).items():
    if t.get("type") != "technique":
        continue
    
    tid = t["id"]
    sc_ids = sc_by_tech.get(tid, [])
    applies_to = [{"sc_id": s, "title": scs.get(s, {}).get("title", ""), "level": scs.get(s, {}).get("level", "")} for s in sc_ids]
    
    results.append({
        "id": tid,
        "type": "technique",
        "category": t.get("category", ""),
        "applies_to": applies_to,
        "summary": t.get("summary", ""),
    })

print(f"Structured: {len(results)} techniques ({sum(1 for r in results if r['applies_to'])} with SC)")

# Save structured summaries
with open(OUT_DIR / "tech_summaries_structured.json", "w") as f:
    json.dump({
        "count": len(results),
        "mapped": sum(1 for r in results if r['applies_to']),
        "results": results,
    }, f, indent=2, ensure_ascii=False)

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

# ── Clean + embed ──
print(f"\nCleaning {len(results)} summaries...")
tech_items = []
tech_texts = []
for r in results:
    raw = r["summary"].strip()
    if not raw or len(raw) < 20:
        continue
    cleaned = re.sub(r'^##\s*(?:Summary\s+of\s+)?WCAG\s+Technique\s*\S*\s*(?:\([^)]*\))?:\s*.*?\n\n?', '',
                     raw, count=1, flags=re.MULTILINE)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    cleaned = re.sub(r' {2,}', ' ', cleaned).strip()
    embed_text = cleaned if len(cleaned) > 50 else raw
    tech_items.append({
        "id": r["id"],
        "applies_to": r["applies_to"],
        "summary": raw,
        "embed_text": embed_text,
    })
    tech_texts.append(embed_text)

print(f"  {len(tech_items)} to embed ({sum(1 for i in tech_items if i['applies_to'])} with SC)")

# Embed
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
print(f"  {OUT_DIR / 'tech_index.json'} ({len(tech_items)} items, {with_meta}/{len(tech_items)} with SC)")
print(f"  {OUT_DIR / 'search.db'} (FTS5)")
print(f"Total: {time.time()-t0:.1f}s")
