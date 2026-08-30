#!/usr/bin/env python3
"""Clean W3C technique Markdown: strip Pandoc divs, inline spans, condense."""

import json
import re

DATA = "wcag-data.json"

with open(DATA) as f:
    data = json.load(f)

techs = data["techniques"]
total = len(techs)
print(f"Processing {total} techniques...")


def clean_md(text: str) -> str:
    if not text:
        return text

    # 1. Remove Pandoc div markers — entire lines starting with ::: (with optional leading whitespace)
    # Pattern 1a: ::: {#id .class} or ::: note or ::: warning (with optional indent for nested blocks)
    text = re.sub(r'^[ \t]*:+[ \t]*(\{[^}]*\}|\w+)[ \t]*\n', '', text, flags=re.MULTILINE)
    # Pattern 1b: bare ::: (closing marker) — with \n or at end of string
    text = re.sub(r'^[ \t]*:+[ \t]*\n', '', text, flags=re.MULTILINE)
    # Pattern 1c: bare ::: at very end of string (no trailing newline)
    text = re.sub(r'^[ \t]*:+[ \t]*$', '', text, flags=re.MULTILINE)

    # 2. Pandoc inline spans: [text]{.class title="..."} → text
    text = re.sub(r'\[([^\]]+)\]\{[^}]*\}', r'\1', text)
    # 2b. Pandoc inline code spans: `code`{.variable} → `code`
    text = re.sub(r'`([^`]+)`\{[^}]*\}', r'`\1`', text)

    # 3. Simplify relative W3C links (../../path/file.html → just anchor text)
    text = re.sub(r'\[([^\]]+)\]\(\.\./[^)]+\)', r'\1', text)

    # 4. Ensure blank line before any heading (restore spacing lost by Pandoc removal)
    text = re.sub(r'([^\n])\n(?=#{1,6}\s)', r'\1\n\n', text)

    # 5. Collapse 3+ blank lines → 1
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 6. Strip trailing whitespace
    text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)

    # 7. Replace &nbsp; / &#160; with space
    text = text.replace('&#160;', ' ')
    text = text.replace('\xa0', ' ')

    return text.strip()


# Process techniques
changed = 0
before_total = 0
after_total = 0
for tid, tech in techs.items():
    raw = tech.get("content_md", "")
    before_total += len(raw)
    if not raw:
        continue
    cleaned = clean_md(raw)
    if cleaned != raw:
        tech["content_md"] = cleaned
        changed += 1
    after_total += len(cleaned)

# Also clean understanding docs
if "understanding" in data:
    for sc_id, doc in data["understanding"].items():
        if isinstance(doc, dict):
            for key in ("understanding", "intent", "benefits", "examples"):
                if key in doc and doc[key]:
                    doc[key] = clean_md(doc[key])

with open(DATA, "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

saved = before_total - after_total
pct = saved * 100 // max(before_total, 1)
print(f"Cleaned {changed}/{total} techniques (content changed)")
print(f"Size: {before_total:,} B → {after_total:,} B (saved {saved:,} B — {pct}%)")

# Also report understanding docs cleaned
u_total = 0
u_cleaned = 0
for sc_id, doc in data.get("understanding", {}).items():
    for key in ("understanding", "intent", "benefits", "examples"):
        if key in doc and isinstance(doc[key], str) and doc[key]:
            u_total += 1
            if clean_md(doc[key]) != doc[key]:  # already updated above
                u_cleaned += 1
print(f"Understanding docs: {u_cleaned}/{u_total} sections cleaned")
