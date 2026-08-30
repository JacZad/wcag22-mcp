#!/usr/bin/env python3
"""
Test embedders on WCAG retrieval task using summaries.
Usage: python3 test_retrieval.py [embedder]

embedder: all-minilm | nomic | gemma3 | all
"""

import json, sys, time, math
from pathlib import Path

DATA = "wcag-data.json"
SUMMARIES = "embeddings/embeddings-data.json"
QUERIES = "embeddings/test_queries.json"
RESULTS = "embeddings/results.json"

# ── Metrics ──
def hit_rate(results, expected, k):
    """How many queries have at least one expected doc in top-k."""
    hits = 0
    for qid, top_k in results.items():
        top_ids = set((r["type"], r["id"]) for r in top_k[:k])
        expected_set = set(tuple(e) for e in expected.get(qid, {}).get("expected", []))
        if top_ids & expected_set:
            hits += 1
    return hits / len(results) if results else 0

def mrr(results, expected):
    """Mean Reciprocal Rank: how early the first correct doc appears."""
    ranks = []
    for qid, top_k in results.items():
        expected_set = set(tuple(e) for e in expected.get(qid, {}).get("expected", []))
        for i, r in enumerate(top_k):
            if (r["type"], r["id"]) in expected_set:
                ranks.append(1.0 / (i + 1))
                break
        else:
            ranks.append(0.0)
    return sum(ranks) / len(ranks) if ranks else 0

def precision_at_k(results, expected, k):
    """Precision@k: fraction of top-k results that are expected."""
    precisions = []
    for qid, top_k in results.items():
        top_ids = set((r["type"], r["id"]) for r in top_k[:k])
        expected_set = set(tuple(e) for e in expected.get(qid, {}).get("expected", []))
        hits = len(top_ids & expected_set)
        precisions.append(hits / k)
    return sum(precisions) / len(precisions) if precisions else 0


def test_embedder(name, embed_fn, summaries, expected_queries):
    """Test an embedder and return metrics."""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")
    
    # Embed all summaries
    doc_keys = []
    doc_vecs = []
    for key, s in summaries.items():
        txt = s.get("summary", "")
        if not txt or len(txt) < 20:
            continue
        vec = embed_fn(txt)
        if vec is not None:
            doc_keys.append((s.get("type", "?"), s.get("id", key)))
            doc_vecs.append(vec)
    
    n_docs = len(doc_keys)
    print(f"  Documents: {n_docs}")
    
    # Embed each query and find top-K
    results = {}
    t0 = time.time()
    for qid, qdata in expected_queries.items():
        q_vec = embed_fn(qdata["query_en"])
        if q_vec is None:
            continue
        
        # Compute similarities
        sims = [_cosine(q_vec, dv) for dv in doc_vecs]
        
        # Get top 20
        ranked = sorted(zip(sims, doc_keys), key=lambda x: -x[0])
        results[qid] = [
            {"type": dk[0], "id": dk[1], "score": round(float(s), 4)}
            for s, dk in ranked[:20]
        ]
    
    elapsed = time.time() - t0
    print(f"  Query time: {elapsed:.2f}s for {len(expected_queries)} queries")
    
    # Compute metrics
    metrics = {
        "hit_rate@1": hit_rate(results, expected_queries, 1),
        "hit_rate@3": hit_rate(results, expected_queries, 3),
        "hit_rate@5": hit_rate(results, expected_queries, 5),
        "mrr": mrr(results, expected_queries),
        "precision@5": precision_at_k(results, expected_queries, 5),
        "docs_embedded": n_docs,
        "query_time_ms": round(elapsed * 1000 / len(expected_queries), 1),
    }
    
    print(f"  Hit@1: {metrics['hit_rate@1']:.1%}")
    print(f"  Hit@3: {metrics['hit_rate@3']:.1%}")
    print(f"  Hit@5: {metrics['hit_rate@5']:.1%}")
    print(f"  MRR:   {metrics['mrr']:.3f}")
    
    # Show failures
    print(f"\n  --- Failures (not in top-5) ---")
    for qid, top_k in results.items():
        expected_set = set(tuple(e) for e in expected_queries[qid]["expected"])
        top5_ids = set((r["type"], r["id"]) for r in top_k[:5])
        missed = expected_set - top5_ids
        if missed:
            q = expected_queries[qid]
            print(f"  [{qid}] {q['query_pl']}")
            print(f"       missed: {missed}")
            # Show what it found instead
            for r in top_k[:5]:
                marker = "✓" if (r["type"], r["id"]) in expected_set else " "
                print(f"       {marker} #{top_k.index(r)+1}: {r['type']}/{r['id']} ({r['score']})")
    
    return metrics, results


# ── Embedders ──

def _cosine(a, b):
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(x*x for x in b))
    if na < 1e-10 or nb < 1e-10:
        return 0.0
    return dot / (na * nb)


def make_all_minilm():
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    def embed(texts):
        if isinstance(texts, str):
            texts = [texts]
        vecs = model.encode(texts, normalize_embeddings=True)
        if len(vecs) == 1:
            return list(vecs[0])
        return [list(v) for v in vecs]
    return embed


def make_nomic():
    import urllib.request, json as j
    def embed(texts):
        if isinstance(texts, str):
            texts = [texts]
        body = j.dumps({
            "model": "nomic-embed-text",
            "input": texts,
        }).encode()
        req = urllib.request.Request(
            "http://localhost:11434/api/embed", body,
            {"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = j.loads(resp.read())
            embeddings = result.get("embeddings", [])
        if len(embeddings) == 1:
            return embeddings[0]
        return [list(v) for v in embeddings]
    return embed


def make_gemma3():
    import mlx.core as mx
    from mlx_lm import load
    
    MODEL = "thedarkstar/KaLM-Embedding-Gemma3-12B-2511-mlx-4Bit"
    print(f"  Loading {MODEL}...")
    model, tokenizer = load(MODEL)
    inner = model.model if hasattr(model, 'model') else model
    
    def embed(texts):
        if isinstance(texts, str):
            texts = [texts]
            single = True
        else:
            single = False
        
        vecs = []
        for text in texts:
            tokens = tokenizer.encode(text)
            if len(tokens) > 1024:
                tokens = tokens[:1024]
            x = mx.array([tokens])
            
            h = inner.embed_tokens(x)
            for layer in inner.layers:
                h = layer(h, mask=None)
            h = inner.norm(h)
            emb = h.mean(axis=1)
            vecs.append(emb[0].tolist())
        
        return vecs[0] if single else vecs
    
    return embed


# ── Main ──
if __name__ == "__main__":
    # Load data
    with open(SUMMARIES) as f:
        summ_data = json.load(f)
    with open(QUERIES) as f:
        query_data = json.load(f)
    
    summaries = summ_data.get("summaries", {})
    expected = query_data.get("queries", {})
    
    print(f"Loaded {len(summaries)} summaries, {len(expected)} queries")
    
    # Decide which embedder to test
    chosen = sys.argv[1] if len(sys.argv) > 1 else "all"
    embedders = []
    
    if chosen in ("all-minilm", "all"):
        embedders.append(("all-MiniLM-L6-v2", make_all_minilm))
    if chosen in ("nomic", "all"):
        embedders.append(("nomic-embed-text", make_nomic))
    if chosen in ("gemma3", "all"):
        embedders.append(("KaLM-Embedding-Gemma3-12B", make_gemma3))
    
    all_metrics = {}
    all_results = {}
    
    for name, maker in embedders:
        try:
            embed_fn = maker()
            metrics, results = test_embedder(name, embed_fn, summaries, expected)
            all_metrics[name] = metrics
            all_results[name] = results
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    # Save results
    with open(RESULTS, "w") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "n_summaries": len(summaries),
            "n_queries": len(expected),
            "metrics": all_metrics,
            "queries": query_data,
        }, f, indent=2, ensure_ascii=False)
    
    # Summary table
    if all_metrics:
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"{'Embedder':30s} {'Hit@1':>8s} {'Hit@3':>8s} {'Hit@5':>8s} {'MRR':>8s} {'P@5':>8s}")
        print("-"*70)
        for name, m in sorted(all_metrics.items()):
            print(f"{name:30s} {m['hit_rate@1']:7.1%} {m['hit_rate@3']:7.1%} {m['hit_rate@5']:7.1%} {m['mrr']:7.3f} {m['precision@5']:7.1%}")
