#!/usr/bin/env python3
"""Step 1: Scrape W3C Understanding pages to extract full SC→technique mapping."""

import json, re, time, sys
from pathlib import Path
from collections import defaultdict
import urllib.request

DATA = "wcag-data.json"
MAPPING_OUT = "embeddings/sc_tech_mapping.json"

with open(DATA) as f:
    wcag = json.load(f)

scs = wcag["scs"]
techs = wcag["techniques"]

# ── Build SC list with slugs ──
sc_list = []
for sc_id, sc in scs.items():
    slug = sc.get("slug", "")
    if not slug:
        slug = sc_id.replace(".", "-")
    sc_list.append((sc_id, slug, sc.get("title", "")))

print(f"Will scrape {len(sc_list)} Understanding pages...")

# ── Patterns ──
# Technique links: href="https://www.w3.org/WAI/WCAG22/Techniques/(general|html|css|aria|...)/TECH_ID"
tech_link = re.compile(r'href="https://www\.w3\.org/WAI/WCAG22/Techniques/[^/]+/([A-Za-z@]+\d+)"')
# Also failure links
fail_link = re.compile(r'href="https://www\.w3\.org/WAI/WCAG22/Techniques/failures/(F\d+)"')

# ── Scrape all Understanding pages ──
sc_tech_map = {}  # SC → list of technique IDs
errors = []

for i, (sc_id, slug, title) in enumerate(sc_list):
    url = f"https://www.w3.org/WAI/WCAG22/Understanding/{slug}"
    
    print(f"  [{i+1}/{len(sc_list)}] {sc_id} {title[:30]}... ", end="", flush=True)
    
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                html = resp.read().decode("utf-8")
            break
        except Exception as e:
            if attempt == 2:
                print(f"FAILED: {e}")
                errors.append((sc_id, slug, str(e)))
                html = ""
            else:
                time.sleep(2)
    
    if not html:
        continue
    
    # Extract all technique IDs from the page
    all_techs = set()
    for m in tech_link.finditer(html):
        all_techs.add(m.group(1))
    for m in fail_link.finditer(html):
        all_techs.add(m.group(1))
    
    # Filter: only techniques that exist in our dataset
    valid_techs = sorted(t for t in all_techs if t in techs)
    
    if valid_techs:
        sc_tech_map[sc_id] = valid_techs
        print(f"{len(valid_techs)} techs")
    else:
        print(f"0 techs (techs found but none in dataset: {all_techs})" if all_techs else "0 techs (empty)")

print(f"\nScraped {len(sc_tech_map)}/{len(sc_list)} SCs")
print(f"Errors: {len(errors)}")

# ── Build reverse mapping: technique → list of SCs ──
tech_sc_map = defaultdict(list)
for sc_id, tech_ids in sc_tech_map.items():
    for tid in tech_ids:
        if tid not in tech_sc_map[tid]:
            tech_sc_map[tid].append(sc_id)

for tid in tech_sc_map:
    tech_sc_map[tid] = sorted(tech_sc_map[tid])

# ── Stats ──
all_mapped_techs = set(tech_sc_map.keys())
unmapped_techs = set(techs.keys()) - all_mapped_techs

print(f"\n=== Results ===")
print(f"Techniques with SC mapping: {len(all_mapped_techs)}/{len(techs)}")
print(f"Techniques without mapping: {len(unmapped_techs)}")
print(f"Total SC→technique edges: {sum(len(v) for v in sc_tech_map.values())}")
print(f"Average techs per SC: {sum(len(v) for v in sc_tech_map.values())/len(sc_tech_map):.1f}")

# Show unmapped by prefix
from collections import Counter
prefixes = Counter()
for tid in unmapped_techs:
    m = re.match(r'([A-Za-z@]+)', tid)
    if m:
        prefixes[m.group(1)] += 1
print(f"\nUnmapped by prefix:")
for p, cnt in sorted(prefixes.items(), key=lambda x: -x[1])[:10]:
    print(f"  {p}: {cnt}")

# ── Save ──
output = {
    "scraped": time.strftime("%Y-%m-%d %H:%M:%S"),
    "sc_count": len(sc_tech_map),
    "tech_mapped": len(all_mapped_techs),
    "tech_unmapped": len(unmapped_techs),
    "edges": sum(len(v) for v in sc_tech_map.values()),
    "sc_to_techs": {k: v for k, v in sorted(sc_tech_map.items())},
    "tech_to_scs": {k: v for k, v in sorted(tech_sc_map.items())},
}

with open(MAPPING_OUT, "w") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nSaved: {MAPPING_OUT}")
