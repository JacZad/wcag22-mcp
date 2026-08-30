#!/usr/bin/env python3
"""
Phase 3 (parallel batch): Re-summarize techniques with SC context using qwen3:4b.
Batches multiple techniques per prompt to be efficient.
"""

import json, time, re, sys
from pathlib import Path

STRUCTURED = "embeddings/tech_structured.json"
EXISTING = "embeddings/embeddings-data.json"
OUT = "embeddings/tech_summaries_new.json"
OUT_DIR = Path("embeddings")

with open(STRUCTURED) as f:
    data = json.load(f)

with open(EXISTING) as f:
    existing_data = json.load(f)

# Build existing summary lookup
existing = {}
for key, t in existing_data.get("summaries", {}).items():
    if t.get("type") == "technique":
        existing[t["id"]] = t.get("summary", "")

techs = data["techniques"]
print(f"Total: {len(techs)}, mapped: {data['mapped']}, unmapped: {data['unmapped']}")

def call_llm(prompt, max_tokens=1024):
    import urllib.request
    body = json.dumps({
        "model": "qwen3:4b-q4_K_M-ctx256k",
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.15,
        }
    }).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/generate", body,
        {"Content-Type": "application/json"}
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())
            return result.get("response", "").strip()
        except Exception as e:
            if attempt == 2:
                return ""
            time.sleep(3)

# Strategy: only re-summarize techniques that HAVE SC mapping (126 total).
# For the rest (394), keep existing summaries but still attach metadata.
# Batch 5 techniques per prompt for efficiency.

mapped_techs = [t for t in techs if t["applies_to"]]
unmapped_techs = [t for t in techs if not t["applies_to"]]

print(f"\nRe-summarizing {len(mapped_techs)} mapped techniques in batches...")
print(f"Keeping existing summaries for {len(unmapped_techs)} unmapped techniques")
print()

BATCH = 5
results = []
t_start = time.time()

for i in range(0, len(mapped_techs), BATCH):
    batch = mapped_techs[i:i+BATCH]
    
    # Build prompt for batch
    prompt_parts = []
    for t in batch:
        tid = t["id"]
        cat = t["category"]
        sc = t["sc_context"]
        content = t["content_md"][:2500]  # truncate
        prompt_parts.append(f"--- TECHNIQUE {tid} (Category: {cat}, Applies to: {sc}) ---\n{content}")
    
    full_prompt = f"""For each technique below, write a 2-3 sentence summary.
Start each summary with just the technique ID on its own line, THEN the summary text.
Include which SCs it applies to in the summary.

{chr(10).join(prompt_parts)}

Output format for each:
TECH_ID
summary text here

Example:
ARIA11
Uses ARIA landmarks to identify page regions. Applies to SC 1.3.1 Info and Relationships. Add role attributes like banner, navigation, main to structural containers."""

    resp = call_llm(full_prompt, max_tokens=1024)
    
    if resp:
        # Parse responses - split by TECH_ID pattern
        lines = resp.split('\n')
        current_id = None
        current_summary = []
        batch_results = {}
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            # Check if this line is a technique ID
            if any(t["id"] == stripped for t in batch):
                if current_id and current_summary:
                    batch_results[current_id] = ' '.join(current_summary).strip()
                current_id = stripped
                current_summary = []
            elif current_id:
                current_summary.append(stripped)
        
        if current_id and current_summary:
            batch_results[current_id] = ' '.join(current_summary).strip()
        
        # Build results for batch
        for t in batch:
            tid = t["id"]
            summary = batch_results.get(tid, "")
            if not summary or len(summary) < 30:
                # Fallback: use existing summary if available
                summary = existing.get(tid, f"Technique {tid} ({t['category']}). {t['sc_context']}")
            results.append({
                "id": tid,
                "type": "technique",
                "category": t["category"],
                "applies_to": t["applies_to"],
                "sc_context": t["sc_context"],
                "summary": summary,
                "content_len": t["content_len"],
            })
        
        print(f"  Batch {i//BATCH+1}/{(len(mapped_techs)+BATCH-1)//BATCH}: {len(batch)} techs ✓")
    else:
        # Fallback
        for t in batch:
            summary = existing.get(t["id"], f"Technique {t['id']} ({t['category']}). {t['sc_context']}")
            results.append({
                "id": t["id"],
                "type": "technique",
                "category": t["category"],
                "applies_to": t["applies_to"],
                "sc_context": t["sc_context"],
                "summary": summary,
                "content_len": t["content_len"],
            })
        print(f"  Batch {i//BATCH+1}: ✗ (LLM failed, used existing)")
    
    time.sleep(0.2)

# Add unmapped techniques with existing summaries
for t in unmapped_techs:
    summary = existing.get(t["id"], f"Technique {t['id']} ({t['category']}).")
    results.append({
        "id": t["id"],
        "type": "technique",
        "category": t["category"],
        "applies_to": t["applies_to"],
        "sc_context": "",
        "summary": summary,
        "content_len": t["content_len"],
    })

elapsed = time.time() - t_start
print(f"\nDone: {len(results)} techniques ({len(mapped_techs)} re-summarized, {len(unmapped_techs)} kept) in {elapsed:.0f}s")

# Save
with open(OUT, "w") as f:
    json.dump({
        "model": "qwen3:4b-q4_K_M-ctx256k",
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(results),
        "elapsed": f"{elapsed:.0f}s",
        "re_summarized": len(mapped_techs),
        "kept_existing": len(unmapped_techs),
        "results": results,
    }, f, indent=2, ensure_ascii=False)

print(f"Saved: {OUT}")
