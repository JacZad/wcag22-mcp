#!/usr/bin/env python3
"""Phase 1-2: Build comprehensive SC→technique mapping, structure data for re-summarization."""

import json, re, time, sys
from pathlib import Path
from collections import defaultdict

DATA = "wcag-data.json"
SUMMARIES = "embeddings/embeddings-data.json"
OUT = "embeddings/tech_for_summary.json"

with open(DATA) as f:
    wcag = json.load(f)

with open(SUMMARIES) as f:
    summ = json.load(f)

teksty = summ["summaries"]
techs = wcag["techniques"]
scs = wcag["scs"]

# ── Build sc_by_tech from 3 sources ──
print("=== Building comprehensive SC → technique mapping ===")

sc_by_tech = defaultdict(list)

# Source 1: existing tech_by_sc (filter valid SC IDs)
tbs = wcag.get("indexes", {}).get("tech_by_sc", {})
for raw_sc_id, refs in tbs.items():
    if re.match(r'^\d+\.\d+\.\d+$', raw_sc_id):
        for tid in refs:
            if tid in techs:
                sc_by_tech[tid].append(raw_sc_id)

print(f"Source 1 (tech_by_sc): {sum(len(v) for v in sc_by_tech.values())} edges")

# Source 2: Success Criterion mentions in technique content_md
sc_ref = re.compile(r'(?:Success Criterion|success criterion)\s+(\d+\.\d+\.\d+)', re.IGNORECASE)
for tid, t in techs.items():
    md = t.get("content_md", "")
    refs = sc_ref.findall(md)
    for sc_id in refs:
        if sc_id not in sc_by_tech[tid]:
            sc_by_tech[tid].append(sc_id)

print(f"Source 2 (content_md): {sum(len(v) for v in sc_by_tech.values())} edges total after merge")

# Source 3: Understanding docs → technique refs
understanding = wcag.get("understanding", {})
tech_pat = re.compile(r'(G|ARIA|H|C|F|SCR|PDF|SVR|SMIL|T|SL|FLASH|PDF)(\d+)')
und_to_sc = defaultdict(list)
for slug, u in understanding.items():
    sc_id = u.get("sc_id", "")
    if not re.match(r"^\d+\.\d+\.\d+$", str(sc_id)):
        continue
    md = u.get("full_md", "")
    for prefix, num in tech_pat.findall(md):
        tid = prefix + num
        if tid in techs:
            und_to_sc[tid].append(sc_id)

for tid, refs in und_to_sc.items():
    for sc_id in refs:
        if sc_id not in sc_by_tech[tid]:
            sc_by_tech[tid].append(sc_id)

print(f"Source 3 (understanding): {sum(len(v) for v in sc_by_tech.values())} edges total after merge")

# Deduplicate and sort
for tid in sc_by_tech:
    sc_by_tech[tid] = sorted(set(sc_by_tech[tid]))

# ── Build structured data for each technique ──
print(f"\n=== Building structured tech data ({len(techs)} total, {len(sc_by_tech)} with SC mapping) ===")

tech_data = {}
for tid, t in techs.items():
    sc_ids = sc_by_tech.get(tid, [])
    
    # Build SC info
    applies_to = []
    for sc_id in sc_ids:
        sc = scs.get(sc_id, {})
        applies_to.append({
            "sc_id": sc_id,
            "title": sc.get("title", ""),
            "level": sc.get("level", ""),
        })
    
    # Get existing summary if available
    existing = None
    for key, st in teksty.items():
        if st.get("type") == "technique" and st.get("id") == tid:
            existing = st.get("summary", "")
            break
    
    # Get category
    cat = t.get("category", "general")
    if not cat:
        cat = "general"
    
    # Get content_md for re-summarization
    content = t.get("content_md", "")
    
    tech_data[tid] = {
        "id": tid,
        "category": cat,
        "applies_to": applies_to,
        "sc_summary": "; ".join(f"{s['sc_id']} {s['title']} ({s['level']})" for s in applies_to),
        "content_md": content,
        "content_len": len(content),
    }

# Save for next phase
with open(OUT, "w") as f:
    json.dump({
        "count": len(tech_data),
        "mapped": sum(1 for t in tech_data.values() if t["applies_to"]),
        "unmapped": sum(1 for t in tech_data.values() if not t["applies_to"]),
        "techniques": tech_data,
    }, f, indent=2, ensure_ascii=False)

print(f"Saved: {OUT}")
print(f"  Mapped: {sum(1 for t in tech_data.values() if t['applies_to'])} techniques")
print(f"  Unmapped: {sum(1 for t in tech_data.values() if not t['applies_to'])} techniques")

# Show summary
print(f"\n=== SC coverage ===")
all_sc_ids = set()
for t in tech_data.values():
    for s in t["applies_to"]:
        all_sc_ids.add(s["sc_id"])
print(f"Unique SCs covered: {len(all_sc_ids)}")
for sc_id in sorted(all_sc_ids)[:10]:
    cnt = sum(1 for t in tech_data.values() if any(s["sc_id"] == sc_id for s in t["applies_to"]))
    sc = scs.get(sc_id, {})
    print(f"  {sc_id} {sc.get('title','')} ({sc.get('level','')}): {cnt} techniques")
if len(all_sc_ids) > 10:
    print(f"  ... and {len(all_sc_ids)-10} more")
