#!/usr/bin/env python3
"""Test hybrid WCAG search (FTS5 + embedding)."""

import json, sqlite3, time, sys
import urllib.request
import numpy as np
from pathlib import Path

BASE = Path(__file__).parent
with open(BASE / "embeddings" / "test_queries.json") as f:
    queries = json.load(f)["queries"]

# Load FTS5
db = sqlite3.connect(str(BASE / "embeddings" / "search.db"))

# Load embedding index
tech_embs = np.load(str(BASE / "embeddings" / "tech_embeddings.npy"))
with open(BASE / "embeddings" / "tech_index.json") as f:
    tech_idx = json.load(f)

# Load SC_PL for display
with open(BASE / "server.py") as f:
    code = f.read()
import re
m = re.search(r'SC_PL\s*=\s*\{([^}]+)\}', code, re.DOTALL)
SC_PL = {}
if m:
    for line in m.group(1).split('\n'):
        line = line.strip()
        if "': '" in line:
            sc_id, title = line.split("': '", 1)
            sc_id = sc_id.strip().strip("'")
            title = title.strip().strip("',")
            SC_PL[sc_id] = title

def hybrid_search(query):
    """Replicate the new server search logic."""
    results = []
    
    # FTS5
    fts_query = " OR ".join(f'"{w}"*' for w in query.split() if len(w) > 1)
    if fts_query:
        cursor = db.execute(
            "SELECT id, type, title, level, rank FROM docs WHERE docs MATCH ? ORDER BY rank LIMIT 10",
            (fts_query,)
        )
        for row in cursor.fetchall():
            sc_id, typ, title, level, rank = row
            score = max(0, 10 + rank)
            if typ == "sc":
                pl_title = SC_PL.get(sc_id, title)
                results.append({
                    "type": "sc", "id": sc_id,
                    "title": f"{title} / {pl_title}",
                    "level": level, "score": 5 + score,
                })
            else:
                results.append({
                    "type": "definition", "id": sc_id,
                    "title": title, "score": 3 + score,
                })
    
    # Embedding
    body = json.dumps({"model": "nomic-embed-text", "input": [query]}).encode()
    req = urllib.request.Request("http://localhost:11434/api/embed", body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        emb = json.loads(resp.read())
    q_vec = emb["embeddings"][0]
    
    sims = np.dot(tech_embs, q_vec)
    top7 = np.argsort(sims)[-7:][::-1]
    for idx in top7:
        item = tech_idx["items"][idx]
        score = float(sims[idx])
        if score > 0.3:
            results.append({
                "type": "technique", "id": item["id"],
                "score": 2 + score * 2,
                "snippet": item["summary"][:120],
            })
    
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:15]

# ── Evaluate ──
def hit_rate(results_dict, expected, k):
    hits = 0
    for qid, top_k in results_dict.items():
        top_ids = set((r["type"], r["id"]) for r in top_k[:k])
        exp_set = set(tuple(e) for e in expected.get(qid, {}).get("expected", []))
        if top_ids & exp_set:
            hits += 1
    return hits / len(results_dict) if results_dict else 0

def mrr(results_dict, expected):
    ranks = []
    for qid, top_k in results_dict.items():
        exp_set = set(tuple(e) for e in expected.get(qid, {}).get("expected", []))
        for i, r in enumerate(top_k):
            if (r["type"], r["id"]) in exp_set:
                ranks.append(1.0 / (i + 1))
                break
        else:
            ranks.append(0.0)
    return sum(ranks) / len(ranks) if ranks else 0

# Run
results = {}
t0 = time.time()

for qid, qdata in queries.items():
    res = hybrid_search(qdata["query_en"])
    results[qid] = res
    time.sleep(0.1)  # gentle rate limit

elapsed = time.time() - t0

print(f"Hybrid search: {len(queries)} queries in {elapsed:.1f}s ({elapsed*1000/len(queries):.0f}ms/query)")
print(f"\n{'='*60}")
print(f"RESULTS")
print(f"{'='*60}")
print(f"{'Metric':20s} {'Value':>10s}")
print(f"{'─'*30}")
print(f"{'Hit@1':20s} {hit_rate(results, queries, 1):8.1%}")
print(f"{'Hit@3':20s} {hit_rate(results, queries, 3):8.1%}")
print(f"{'Hit@5':20s} {hit_rate(results, queries, 5):8.1%}")
print(f"{'MRR':20s} {mrr(results, queries):8.3f}")

# Show failures
print(f"\n  --- Failures (not in top-5) ---")
for qid, top_k in results.items():
    exp_set = set(tuple(e) for e in queries[qid]["expected"])
    top5_ids = set((r["type"], r["id"]) for r in top_k[:5])
    missed = exp_set - top5_ids
    if missed:
        print(f"\n  [{qid}] {queries[qid]['query_pl']}")
        print(f"       missed: {missed}")
        for r in top_k[:5]:
            m = "✓" if (r["type"], r["id"]) in exp_set else " "
            print(f"       {m} #{top_k.index(r)+1}: {r['type']}/{r['id']} ({r['score']:.2f})")

# Comparisons
print(f"\n{'='*60}")
print("COMPARISON")
print(f"{'='*60}")
print(f"{'Embedder':40s} {'Hit@1':>8s} {'Hit@3':>8s} {'MRR':>8s}")
print(f"{'─'*64}")
print(f"{'Hybrid FTS5+nomic':40s} {hit_rate(results, queries, 1):7.1%} {hit_rate(results, queries, 3):7.1%} {mrr(results, queries):7.3f}")
print(f"{'nomic-embed-text (pure)':40s} {8.3:>7} {33.3:>7} {0.257:>7}")
print(f"{'all-MiniLM-L6-v2 (pure)':40s} {16.7:>7} {29.2:>7} {0.305:>7}")
