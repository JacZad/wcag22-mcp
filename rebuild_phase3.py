#!/usr/bin/env python3
"""
Phase 3-4: Re-summarize techniques with qwen3:4b, clean, and embed with nomic.
Reads: embeddings/tech_structured.json, wcag-data.json
Writes: embeddings/tech_summaries_new.json, embeddings/tech_index.json, embeddings/tech_embeddings.npy
"""

import json, time, re, sys
from pathlib import Path

DATA = "embeddings/tech_structured.json"
WCAG_DATA = "wcag-data.json"
OUT_DIR = Path("embeddings")

with open(DATA) as f:
    structured = json.load(f)

with open(WCAG_DATA) as f:
    wcag = json.load(f)

techs = structured["techniques"]
scs = wcag["scs"]

print(f"Phase 3: Re-summarizing {len(techs)} techniques with qwen3:4b")
print(f"  Mapped to SC: {structured['mapped']}")
print(f"  Unmapped: {structured['unmapped']}")
print()

BATCH = 1  # one at a time (better summaries)
DELAY = 0.1  # small delay between items

def call_llm(prompt, max_tokens=512):
    """Call Ollama qwen3:4b"""
    import urllib.request
    body = json.dumps({
        "model": "qwen3:4b",
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.2,
            "stop": ["\n\n\n"],
        }
    }).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/generate", body,
        {"Content-Type": "application/json"}
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read())
            return result.get("response", "").strip()
        except Exception as e:
            if attempt == 2:
                print(f"    Error: {e}")
                return ""
            time.sleep(2)

def summarize_technique(tech):
    """Generate a structured summary for one technique."""
    tid = tech["id"]
    cat = tech["category"]
    sc_ctx = tech["sc_context"]
    content = tech["content_md"]
    
    # Truncate content if very long
    if len(content) > 3000:
        content = content[:3000] + "\n... [truncated]"
    
    sc_part = f"Applies to: {sc_ctx}" if sc_ctx else "No specific SC listed"
    
    prompt = f"""Summarize this WCAG technique concisely.

Technique ID: {tid}
Category: {cat}
{sc_part}

Content:
{content}

Write a 3-5 sentence summary covering: what problem this technique solves, how to implement it, and which SCs it relates to."""

    return call_llm(prompt, max_tokens=512)

# ── Summarize ──
results = []
t_start = time.time()

for i, tech in enumerate(techs):
    tid = tech["id"]
    
    print(f"  [{i+1}/{len(techs)}] {tid} ... ", end="", flush=True)
    
    summary = summarize_technique(tech)
    
    if summary:
        print(f"✓ ({len(summary)} chars)")
    else:
        print(f"✗ (empty)")
        summary = f"Technique {tid} ({tech['category']}): address accessibility requirements."
    
    results.append({
        "id": tid,
        "type": "technique",
        "category": tech["category"],
        "applies_to": tech["applies_to"],
        "sc_context": tech["sc_context"],
        "summary": summary,
        "content_len": tech["content_len"],
    })
    
    # Save checkpoint every 50
    if (i + 1) % 50 == 0:
        checkpoint = {
            "count": i + 1,
            "model": "qwen3:4b",
            "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed": f"{time.time()-t_start:.0f}s",
            "results": results,
        }
        with open(OUT_DIR / f"checkpoint_{i+1}.json", "w") as f:
            json.dump(checkpoint, f, indent=2, ensure_ascii=False)
        print(f"  --- Checkpoint saved: {i+1} techniques in {time.time()-t_start:.0f}s ---")
    
    time.sleep(DELAY)

elapsed = time.time() - t_start
print(f"\nPhase 3 done: {len(results)} techniques summarized in {elapsed:.0f}s ({elapsed/len(results):.1f}s/tech)")

# ── Save all summaries ──
with open(OUT_DIR / "tech_summaries_new.json", "w") as f:
    json.dump({
        "model": "qwen3:4b",
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(results),
        "elapsed": f"{elapsed:.0f}s",
        "results": results,
    }, f, indent=2, ensure_ascii=False)

print(f"Saved: {OUT_DIR / 'tech_summaries_new.json'}")

# ── Phase 4: Clean and embed ──
print("\n" + "=" * 60)
print("Phase 4: Clean summaries and embed with nomic-embed-text")
print("=" * 60)

# Clean summaries for embedding
tech_items = []
tech_texts = []

for r in results:
    raw = r["summary"]
    if not raw or len(raw) < 20:
        continue
    
    # Clean: remove technique prefix boilerplate
    cleaned = re.sub(
        r'^##\s*(?:Summary\s+of\s+)?WCAG\s+Technique\s+\S+\s*(?:\([^)]*\))?:\s*.*?\n\n?',
        '', raw, count=1, flags=re.MULTILINE
    )
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    cleaned = re.sub(r' {2,}', ' ', cleaned).strip()
    
    # Use cleaned if long enough, else raw
    embed_text = cleaned if len(cleaned) > 50 else raw
    
    # Build applies_to metadata (already structured)
    applies_to = r["applies_to"]
    
    tech_items.append({
        "id": r["id"],
        "applies_to": applies_to,
        "summary": raw,
        "embed_text": embed_text,
    })
    tech_texts.append(embed_text)

print(f"  {len(tech_items)} techniques ready for embedding")

# Embed with nomic
print(f"\n  Embedding with nomic-embed-text...")
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
                print(f"    Error at batch {i}: {e}")
                sys.exit(1)
            time.sleep(2)
    
    embs = result.get("embeddings", [])
    all_embeddings.extend(embs)
    
    if (i + BATCH_SIZE) % 50 == 0 or i + BATCH_SIZE >= len(tech_texts):
        print(f"    ... {min(i+BATCH_SIZE, len(tech_texts))}/{len(tech_texts)}")

embed_elapsed = time.time() - t0
print(f"  Embedded {len(all_embeddings)} techniques in {embed_elapsed:.1f}s")

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

print(f"\nSaved:")
print(f"  {OUT_DIR / 'tech_embeddings.npy'} ({emb_array.shape})")
print(f"  {OUT_DIR / 'tech_index.json'} ({len(tech_items)} items)")

# Stats
with_meta = sum(1 for i in tech_items if i['applies_to'])
without_meta = sum(1 for i in tech_items if not i['applies_to'])
print(f"\nFinal stats:")
print(f"  With SC metadata: {with_meta}")
print(f"  Without SC metadata: {without_meta}")
print(f"  Total time: {time.time()-t_start:.0f}s")
