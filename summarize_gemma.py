#!/usr/bin/env python3
"""Prepare structured technique data: attach full SC mapping + categories, then summarize with gemma4:e2b."""

import json, re, time, sys
from pathlib import Path

DATA = "wcag-data.json"
MAPPING = "embeddings/sc_tech_mapping.json"
SUMMARIES_OUT = "embeddings/tech_summaries_gemma.json"

with open(DATA) as f:
    wcag = json.load(f)
with open(MAPPING) as f:
    mapping = json.load(f)

techs = wcag["techniques"]
scs = wcag["scs"]
tech_to_scs = mapping["tech_to_scs"]  # technique → list of SC IDs

# ── Category mapping ──
def get_category(tid):
    """Determine category from technique ID prefix."""
    tid_upper = tid.upper()
    if tid_upper.startswith("ARIA") or tid_upper == "ARIA":
        return "ARIA"
    if tid_upper.startswith("C"):
        if tid[1:].isdigit():
            return "CSS"
    if tid_upper.startswith("F"):
        if tid[1:].isdigit():
            return "Failure"
    if tid_upper.startswith("FLASH"):
        return "Flash"
    if tid_upper.startswith("G"):
        if tid[1:].isdigit() or tid.startswith("@@"):
            return "General"
    if tid_upper.startswith("H"):
        if tid[1:].isdigit():
            return "HTML"
    if tid_upper.startswith("PDF"):
        return "PDF"
    if tid_upper.startswith("SCR"):
        if len(tid) > 3 and tid[3:].isdigit():
            return "Client-side Script"
    if tid_upper.startswith("SL"):
        return "Silverlight"
    if tid_upper.startswith("SM"):
        return "SMIL"
    if tid_upper.startswith("SVR"):
        return "Server-side Script"
    if tid_upper.startswith("T"):
        return "Plain Text"
    if tid_upper.startswith("W"):
        return "Other"
    # Fallback to wcag-data.json category
    tech = techs.get(tid, {})
    cat = tech.get("category", "other")
    cat_map = {
        "general": "General",
        "html": "HTML",
        "css": "CSS",
        "aria": "ARIA",
        "client-side-script": "Client-side Script",
        "failures": "Failure",
        "flash": "Flash",
        "pdf": "PDF",
        "server-side-script": "Server-side Script",
        "silverlight": "Silverlight",
        "smil": "SMIL",
        "text": "Plain Text",
    }
    return cat_map.get(cat, cat.capitalize())

# ── Build structured tech data ──
structured = []
for tid, t in techs.items():
    sc_ids = tech_to_scs.get(tid, [])
    applies_to = []
    for sc_id in sc_ids:
        sc = scs.get(sc_id, {})
        applies_to.append({
            "sc_id": sc_id,
            "title": sc.get("title", ""),
            "level": sc.get("level", ""),
        })
    
    category = get_category(tid)
    content = t.get("content_md", "")
    
    structured.append({
        "id": tid,
        "category": category,
        "applies_to": applies_to,
        "sc_context": "; ".join(f"{s['sc_id']} {s['title']} ({s['level']})" for s in applies_to),
        "content_md": content,
        "content_len": len(content),
    })

# Sort: mapped first, then by ID
structured.sort(key=lambda x: (0 if x["applies_to"] else 1, x["id"]))

print(f"Structured {len(structured)} techniques:")
print(f"  With SC mapping: {sum(1 for s in structured if s['applies_to'])}")
print(f"  Without: {sum(1 for s in structured if not s['applies_to'])}")
print(f"  Total SC edges: {sum(len(s['applies_to']) for s in structured)}")

# Categories
from collections import Counter
cats = Counter(s["category"] for s in structured)
print(f"\nCategories:")
for cat, cnt in sorted(cats.items(), key=lambda x: -x[1]):
    mapped = sum(1 for s in structured if s["category"] == cat and s["applies_to"])
    print(f"  {cat}: {cnt} ({mapped} mapped)")

# ── Check if we need to save for next step ──
# We'll proceed directly to summarization

import urllib.request

def call_gemma(prompt, max_tokens=600):
    """Call gemma4:e2b for summarization."""
    body = json.dumps({
        "model": "gemma4:e2b",
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
            with urllib.request.urlopen(req, timeout=180) as resp:
                result = json.loads(resp.read())
            text = result.get("response", "").strip()
            if text:
                return text
        except Exception as e:
            if attempt == 2:
                return ""
            time.sleep(3)

def summarize(tech):
    """Generate a concise summary with SC context."""
    tid = tech["id"]
    cat = tech["category"]
    sc_ctx = tech["sc_context"]
    content = tech["content_md"]
    
    # Truncate content if very long
    if len(content) > 3500:
        # Keep first ~2500 and last ~800
        content = content[:2500] + "\n... [środek pominięty] ...\n" + content[-800:]
    
    prompt = f"""Technique: {tid}
Category: {cat}
Applies to: {sc_ctx if sc_ctx else '(not specified in W3C data)'}

Content:
{content}

Write a concise 4-6 sentence summary in English:
1. What problem this technique solves
2. How to implement it briefly
3. Which SCs it relates to (if any)"""
    
    return call_gemma(prompt, max_tokens=600)

OUT_DIR = Path("embeddings")
OUT_DIR.mkdir(exist_ok=True)

# ── Summarize (mapped first, then unmapped) ──
results = []
t_start = time.time()

print(f"\n{'='*60}")
print(f"Summarizing {len(structured)} techniques with gemma4:e2b (one at a time)")
print(f"{'='*60}")

for i, tech in enumerate(structured):
    tid = tech["id"]
    elapsed_total = time.time() - t_start
    
    # ETA
    if i > 0:
        avg = elapsed_total / i
        remaining = avg * (len(structured) - i)
        eta = time.strftime("%H:%M", time.localtime(time.time() + remaining))
    else:
        eta = "?"
    
    print(f"  [{i+1}/{len(structured)}] {tid:12s} ({tech['category']:18s}) ... ", end="", flush=True)
    
    summary = summarize(tech)
    
    if summary:
        sc_info = f"({len(tech['applies_to'])} SC)" if tech["applies_to"] else "(no SC)"
        print(f"✓ {len(summary)} chars {sc_info} | ETA: {eta}")
    else:
        print(f"✗ empty | ETA: {eta}")
        summary = f"Technique {tid} ({tech['category']}) addresses web accessibility requirements."
    
    results.append({
        "id": tid,
        "type": "technique",
        "category": tech["category"],
        "applies_to": tech["applies_to"],
        "summary": summary,
        "content_len": tech["content_len"],
    })
    
    # Save checkpoint every 20
    if (i + 1) % 20 == 0:
        checkpoint = {
            "model": "gemma4:e2b",
            "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "count": i + 1,
            "elapsed": f"{time.time()-t_start:.0f}s",
            "results": results,
        }
        with open(OUT_DIR / f"checkpoint_gemma_{i+1}.json", "w") as f:
            json.dump(checkpoint, f, indent=2, ensure_ascii=False)
        print(f"\n  --- Checkpoint: {i+1}/{len(structured)} in {time.time()-t_start:.0f}s ---\n")

elapsed = time.time() - t_start
print(f"\nDone: {len(results)} techniques in {elapsed:.0f}s ({elapsed/len(results):.1f}s/tech)")

# Save final
OUT_DIR = Path("embeddings")
OUT_DIR.mkdir(exist_ok=True)

with open(OUT_DIR / "tech_summaries_gemma.json", "w") as f:
    json.dump({
        "model": "gemma4:e2b",
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(results),
        "elapsed": f"{elapsed:.0f}s",
        "results": results,
    }, f, indent=2, ensure_ascii=False)

print(f"Saved: {OUT_DIR / 'tech_summaries_gemma.json'}")
