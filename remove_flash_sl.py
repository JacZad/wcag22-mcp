#!/usr/bin/env python3
"""Remove all FLASH* and SL* techniques from the WCAG 2.2 MCP data."""

import json
import numpy as np
from pathlib import Path

BASE = Path(__file__).parent

# ── 1. wcag-data.json ──
print("📦 Updating wcag-data.json...")
with open(BASE / "wcag-data.json") as f:
    data = json.load(f)

to_remove = set()
for k in data["techniques"]:
    if k.startswith("FLASH") or k.startswith("SL"):
        to_remove.add(k)

print(f"   Found {len(to_remove)} techniques to remove: {', '.join(sorted(to_remove)[:5])}...")

# Remove from techniques dict
for tid in to_remove:
    del data["techniques"][tid]

# Remove references from tech_by_sc
cleaned_sc = 0
for sc_id, tech_ids in data["indexes"]["tech_by_sc"].items():
    orig = len(tech_ids)
    data["indexes"]["tech_by_sc"][sc_id] = [t for t in tech_ids if t not in to_remove]
    if len(data["indexes"]["tech_by_sc"][sc_id]) < orig:
        cleaned_sc += 1

# Remove references from failures_by_sc
cleaned_fail = 0
for sc_id, fail_ids in data["indexes"].get("failures_by_sc", {}).items():
    orig = len(fail_ids)
    data["indexes"]["failures_by_sc"][sc_id] = [f for f in fail_ids if f not in to_remove]
    if len(data["indexes"]["failures_by_sc"][sc_id]) < orig:
        cleaned_fail += 1

# Update counts
data["counts"]["techniques"] = len(data["techniques"])

with open(BASE / "wcag-data.json", "w") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"   Removed from techniques dict ✓")
print(f"   Cleaned tech_by_sc: {cleaned_sc} SC entries")
print(f"   Cleaned failures_by_sc: {cleaned_fail} entries")
print(f"   New technique count: {data['counts']['techniques']}")

# ── 2. tech_index.json + tech_embeddings.npy ──
print("\n📦 Updating embeddings...")
with open(BASE / "embeddings" / "tech_index.json") as f:
    tech_index = json.load(f)

embeddings = np.load(BASE / "embeddings" / "tech_embeddings.npy")
print(f"   Current embeddings shape: {embeddings.shape}")
print(f"   Current tech_index items: {len(tech_index['items'])}")

# Find indices to keep
keep_indices = []
keep_items = []
for i, item in enumerate(tech_index["items"]):
    if item["id"] not in to_remove:
        keep_indices.append(i)
        keep_items.append(item)

# Filter embeddings
new_embeddings = embeddings[keep_indices]
tech_index["items"] = keep_items
tech_index["count"] = len(keep_items)

# Save
np.save(BASE / "embeddings" / "tech_embeddings.npy", new_embeddings)
with open(BASE / "embeddings" / "tech_index.json", "w") as f:
    json.dump(tech_index, f, indent=2, ensure_ascii=False)

print(f"   New embeddings shape: {new_embeddings.shape}")
print(f"   New tech_index items: {tech_index['count']}")
print("\n✅ Done! Restart the MCP server to apply changes.")
