#!/usr/bin/env python3
"""
Generate English summaries of all WCAG 2.2 documents using local Ollama model.
Saves to embeddings/embeddings-data.json for later embedding and search.
"""

import json
import re
import sys
import time
from pathlib import Path

DATA = "wcag-data.json"
OUT = "embeddings/embeddings-data.json"
MODEL = "gemma4:e2b"
OLLAMA = "http://localhost:11434/api/generate"

with open(DATA) as f:
    data = json.load(f)

SUMMARIES = {}
stats = {"sc": 0, "technique": 0, "definition": 0, "errors": 0}

def llm_summarize(prompt: str, max_retries=2, num_predict=800) -> str:
    """Send a prompt to Ollama and return the text response."""
    import urllib.request, urllib.error
    
    body = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": num_predict,
        }
    }).encode()
    
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(OLLAMA, body, {"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as resp:
                result = json.loads(resp.read())
                text = result.get("response", "").strip()
                if text:
                    return text
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"  [Error after {max_retries} retries: {e}]")
    return ""


# ── SC summaries ──
print("=== SC summaries ===")
sc_list = sorted(data["scs"].items(), key=lambda x: [int(p) for p in x[0].split(".")])
for sc_id, sc in sc_list:
    title = sc.get("title", "")
    level = sc.get("level", "")
    
    # Get Understanding text if available
    und = data.get("understanding", {}).get(sc_id, {})
    intent = und.get("intent", "") if isinstance(und, dict) else ""
    # Take first ~1000 chars of intent
    intent_snippet = intent[:1500] if intent else ""
    
    prompt = f"""Write a 2-3 sentence summary in plain English of WCAG Success Criterion {sc_id} ({title}, Level {level}).

Context from the official Understanding document:
{intent_snippet[:1000]}

Focus on: what the criterion requires, who it helps, and when it applies. Write for a developer who needs to understand why this matters."""
    
    summary = llm_summarize(prompt)
    SUMMARIES[f"sc:{sc_id}"] = {
        "id": sc_id,
        "type": "sc",
        "title": title,
        "level": level,
        "summary": summary,
    }
    stats["sc"] += 1
    sys.stdout.write(f"  {sc_id:8s} {summary[:80]}...\n")
    sys.stdout.flush()
    time.sleep(0.3)  # gentle rate limit


# ── Technique summaries ──
print("\n=== Technique summaries ===")
tech_list = sorted(data["techniques"].items(), key=lambda x: x[0])
for tid, tech in tech_list:
    content_md = tech.get("content_md", "")
    # First ~800 chars gives us the title and description
    intro = content_md[:800] if content_md else ""
    cat = tech.get("category", "")
    
    prompt = f"""Write a detailed summary (~400-500 words) of WCAG technique {tid} ({cat}). 

Context from the technique documentation:
{intro[:800]}

Describe: what problem this technique solves, exactly how to implement it, who benefits from it, and any important exceptions or limitations. Use concrete language and avoid general accessibility boilerplate. Focus on what makes THIS technique unique."""
    
    summary = llm_summarize(prompt)
    SUMMARIES[f"technique:{tid}"] = {
        "id": tid,
        "type": "technique",
        "category": cat,
        "summary": summary,
    }
    stats["technique"] += 1
    if stats["technique"] % 50 == 0:
        print(f"  ... {stats['technique']}/520 techniques done")
    sys.stdout.flush()
    time.sleep(0.15)


# ── Definition summaries ──
print("\n=== Definition summaries ===")
def_list = sorted(data["definitions"].items(), key=lambda x: x[0])
for term, defn in def_list:
    if isinstance(defn, dict):
        text = defn.get("definition", "") or defn.get("definition_md", "")
    else:
        text = str(defn)
    
    prompt = f"""Define the WCAG term "{term}" in 1-2 clear sentences.

Original definition:
{text[:500]}

Write a practical, concise definition that a developer would understand."""
    
    summary = llm_summarize(prompt)
    SUMMARIES[f"definition:{term}"] = {
        "id": term,
        "type": "definition",
        "summary": summary,
    }
    stats["definition"] += 1
    sys.stdout.flush()
    time.sleep(0.1)


# ── Save ──
Path(OUT).parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w") as f:
    json.dump({
        "model": MODEL,
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(SUMMARIES),
        "stats": stats,
        "summaries": SUMMARIES,
    }, f, ensure_ascii=False, indent=2)

print(f"\n=== Done: {len(SUMMARIES)} summaries, {stats['errors']} errors ===")
print(f"Saved to {OUT}")
