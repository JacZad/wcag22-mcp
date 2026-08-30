#!/usr/bin/env python3
"""Complete rebuild: extract SC mappings, re-summarize, clean, and embed.

Phase 1-2: Build comprehensive SC mapping + structure data.
Phase 3: Re-summarize 520 techniques with local LLM (SC context included).
Phase 4: Re-embed with nomic-embed-text.
"""

import json, re, time, sys, sqlite3
from pathlib import Path
from collections import defaultdict

DATA = "wcag-data.json"
OUT = "embeddings"
OUT_DIR = Path(OUT)

# ── 1. Load data ──
with open(DATA) as f:
    wcag = json.load(f)

techs = wcag["techniques"]
scs = wcag["scs"]

# ── 2. Build comprehensive SC → technique mapping ──
print("=" * 60)
print("PHASE 1-2: Build SC mapping + structure technique data")
print("=" * 60)

sc_by_tech = defaultdict(list)

# Source A: existing tech_by_sc (filter valid SC IDs)
tbs = wcag.get("indexes", {}).get("tech_by_sc", {})
for raw_sc_id, refs in tbs.items():
    if re.match(r'^\d+\.\d+\.\d+$', raw_sc_id):
        for tid in refs:
            if tid in techs and raw_sc_id not in sc_by_tech[tid]:
                sc_by_tech[tid].append(raw_sc_id)

print(f"Source A (tech_by_sc): {sum(len(v) for v in sc_by_tech.values())} edges from {len(sc_by_tech)} techniques")

# Source B: Success Criterion mentions in technique content_md
sc_ref = re.compile(r'(?:Success Criterion|success criterion)\s+(\d+\.\d+\.\d+)', re.IGNORECASE)
for tid, t in techs.items():
    md = t.get("content_md", "")
    for sc_id in sc_ref.findall(md):
        if sc_id not in sc_by_tech[tid]:
            sc_by_tech[tid].append(sc_id)

print(f"Source B (content_md SC refs): {sum(len(v) for v in sc_by_tech.values())} edges total")

# Source C: Understanding docs → technique references
understanding = wcag.get("understanding", {})
tech_pat = re.compile(r'(G|ARIA|H|C|F|SCR|PDF|SVR|SMIL|T|SL|FLASH|PDF)(\d+)')
und_to_sc = defaultdict(list)
for slug, u in understanding.items():
    sc_id = u.get("sc_id", "")
    if not re.match(r"^\d+\.\d+\.\d+$", str(sc_id)):
        continue
    for prefix, num in tech_pat.findall(u.get("full_md", "")):
        tid = prefix + num
        if tid in techs and sc_id not in sc_by_tech[tid]:
            sc_by_tech[tid].append(sc_id)

print(f"Source C (Understanding docs): {sum(len(v) for v in sc_by_tech.values())} edges total")

# Source D: Failure descriptions from techniques listing page (failure items list SC in their title)
# The wcag-data.json failure descriptions already contain SC refs extracted in Source B
# But let's also check the technique 'category' field for failures
f_ref = re.compile(r'Failure of (?:Success Criterion|success criterion)\s+(\d+\.\d+\.\d+)', re.IGNORECASE)
for tid, t in techs.items():
    if t.get("category") == "failures" or tid.startswith("F") or tid.startswith("PDF"):
        md = t.get("content_md", "")
        for sc_id in f_ref.findall(md):
            if sc_id not in sc_by_tech[tid]:
                sc_by_tech[tid].append(sc_id)

print(f"Source D (failure descriptions): {sum(len(v) for v in sc_by_tech.values())} edges total")

# Source E: W3C techniques listing page — failures explicitly say "Failure of SC X.Y.Z"
# Already covered by Source B + D - the page content was scraped into content_md

# Deduplicate and sort
for tid in sc_by_tech:
    sc_by_tech[tid] = sorted(set(sc_by_tech[tid]))

mapped_count = len(sc_by_tech)
print(f"\nFinal: {mapped_count}/{len(techs)} techniques have SC mapping")

# ── 3. Build structured data for summarization ──
print("\n" + "=" * 60)
print("PHASE 3: Structure technique data for re-summarization")
print("=" * 60)

# Build category map from existing summaries
existing_summaries = {}
try:
    with open(OUT_DIR / "embeddings-data.json") as f:
        old_summ = json.load(f)
    for key, t in old_summ.get("summaries", {}).items():
        if t.get("type") == "technique":
            existing_summaries[t["id"]] = t.get("summary", "")
except (FileNotFoundError, json.JSONDecodeError):
    print("  No existing summaries found")

# Build tech data
techs_for_summary = []
no_content = []
for tid, t in techs.items():
    sc_ids = sc_by_tech.get(tid, [])
    applies_to = [{"sc_id": s, "title": scs.get(s, {}).get("title", ""), "level": scs.get(s, {}).get("level", "")} for s in sc_ids]
    
    content = t.get("content_md", "").strip()
    if not content:
        no_content.append(tid)
        continue
    
    cat = t.get("category", "general")
    
    techs_for_summary.append({
        "id": tid,
        "category": cat,
        "applies_to": applies_to,
        "sc_context": "; ".join(f"{s['sc_id']} {s['title']} ({s['level']})" for s in applies_to),
        "content_md": content,
        "content_len": len(content),
        "has_existing": tid in existing_summaries,
    })

# Save structured data
structured = {
    "total": len(techs_for_summary),
    "mapped": sum(1 for t in techs_for_summary if t["applies_to"]),
    "unmapped": sum(1 for t in techs_for_summary if not t["applies_to"]),
    "no_content": len(no_content),
    "sc_coverage": len(set(s["sc_id"] for t in techs_for_summary for s in t["applies_to"])),
    "techniques": techs_for_summary,
}

with open(OUT_DIR / "tech_structured.json", "w") as f:
    json.dump(structured, f, indent=2, ensure_ascii=False)

print(f"  Total techniques with content: {len(techs_for_summary)}")
print(f"  With SC mapping: {structured['mapped']}")
print(f"  Without mapping: {structured['unmapped']}")
print(f"  Without content_md: {len(no_content)}")
print(f"  Unique SCs covered: {structured['sc_coverage']}")
print(f"\nSaved: {OUT_DIR / 'tech_structured.json'}")

# ── Show sample ──
print("\n=== Sample techniques ===")
for t in techs_for_summary[:3]:
    print(f"  {t['id']}: cat={t['category']}, content_len={t['content_len']}")
    if t['applies_to']:
        print(f"    SC: {t['sc_context'][:100]}")
    else:
        print(f"    No SC mapping")
