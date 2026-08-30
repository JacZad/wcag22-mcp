#!/usr/bin/env python3
"""
Test suite for WCAG embedding search.
Tests how well each embedder finds the right document(s) for a given query.
"""

import json, sys, time, math
from pathlib import Path

# ── Test queries (what a real auditor would ask) ──
# Each entry: (query_pl, query_en, expected_docs, reason)
# expected_docs: list of (type, id) tuples that should rank high
TEST_QUERIES = [
    # === DIRECT TITLE MATCHES ===
    ("kontrast tekstu", "text contrast",
     [("sc", "1.4.3"), ("sc", "1.4.6")],
     "Both contrast SCs should rank high"),

    ("wielkość celu minimum", "target size minimum",
     [("sc", "2.5.8")],
     "Exact title match for 2.5.8"),

    ("fokus widoczny", "focus visible",
     [("sc", "2.4.7")],
     "Exact title match"),

    # === SEMANTIC (different words, same concept) ===
    ("klikalny obszar przycisku", "clickable button area",
     [("sc", "2.5.8")],
     "User asks about button size → should match target size minimum"),

    ("obramowanie fokusa", "focus outline",
     [("sc", "2.4.13"), ("sc", "2.4.7")],
     "Focus appearance + focus visible"),

    ("powiększanie czcionki", "enlarge font size",
     [("sc", "1.4.4")],
     "Resize text SC"),

    ("przyciski na małym ekranie", "buttons on small screen",
     [("sc", "1.4.10")],
     "Reflow - content fits on small screens"),

    ("czytnik ekranu nie czyta obrazka", "screen reader does not read image",
     [("sc", "1.1.1")],
     "Non-text content alternative"),

    ("kolor a informacja", "color alone conveys information",
     [("sc", "1.4.1")],
     "Use of color"),

    ("pole wyszukiwania autouzupełnianie", "search field autocomplete",
     [("sc", "1.3.5")],
     "Identify input purpose"),

    ("skróty klawiszowe jedna litera", "single key shortcut",
     [("sc", "2.1.4")],
     "Character key shortcuts"),

    ("tabela z czytelną kolejnością", "table reading order",
     [("sc", "1.3.2")],
     "Meaningful sequence"),

    ("link obrazek z tekstem duplikacja", "link image and text duplication",
     [("technique", "H2")],
     "Technique H2 - combining adjacent image and text links"),

    ("alt text dla ikony", "alt text for icon",
     [("sc", "1.1.1"), ("technique", "H2")],
     "Both the SC and a technique"),

    # === CROSS-CATEGORY ===
    ("jak sprawdzić kontrast narzędziem", "how to check contrast with tool",
     [("sc", "1.4.3"), ("technique", "G18")],
     "Technique G18 about contrast checking"),

    ("link pomijanie nawigacji", "skip navigation link",
     [("sc", "2.4.1"), ("technique", "G1")],
     "Bypass blocks + technique"),

    ("nagłówek sekcji aria", "section heading aria",
     [("technique", "ARIA12")],
     "ARIA12 - using role=heading"),

    ("rama czy iframe tytuł", "frame or iframe title",
     [("technique", "H64")],
     "H64 - using the title attribute of iframe"),

    ("język strony atrybut lang", "page language attribute lang",
     [("sc", "3.1.1"), ("technique", "H57")],
     "Language of page + technique H57"),

    # === WCAG 2.2 NEW ===
    ("fokus niezakryty", "focus not obscured",
     [("sc", "2.4.11"), ("sc", "2.4.12")],
     "New WCAG 2.2 criteria"),

    ("przeciąganie zamiennik", "dragging alternative",
     [("sc", "2.5.7")],
     "Dragging movements - new in 2.2"),

    ("ponowne wpisywanie danych", "redundant entry",
     [("sc", "3.3.7")],
     "Redundant entry - new in 2.2"),

    ("dostępne logowanie bez kaptcha", "accessible authentication without captcha",
     [("sc", "3.3.8"), ("sc", "3.3.9")],
     "Authentication SCs"),

    # === SPRAWDZENIE SEPARACJI ===
    ("kontrast elementów interfejsu", "non-text interface contrast",
     [("sc", "1.4.11")],
     "Non-text contrast (buttons etc), NOT text contrast 1.4.3"),
]

EXPECTED = {}
for i, (pl, en, docs, reason) in enumerate(TEST_QUERIES):
    EXPECTED[f"q{i:02d}"] = {
        "query_pl": pl,
        "query_en": en,
        "expected": docs,
        "reason": reason,
    }

# Save test set
Path("embeddings").mkdir(exist_ok=True)
with open("embeddings/test_queries.json", "w") as f:
    json.dump({
        "description": "WCAG retrieval test queries",
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(EXPECTED),
        "queries": EXPECTED,
    }, f, indent=2, ensure_ascii=False)

print(f"Test suite: {len(EXPECTED)} queries")
print(f"Saved to embeddings/test_queries.json")

# Print summary
cats = {"direct": 0, "semantic": 0, "cross": 0, "new22": 0, "separation": 0}
for q in EXPECTED.values():
    desc = q["reason"]
    if "Exact" in desc or "title" in desc.lower(): cats["direct"] += 1
    elif "separacji" in desc: cats["separation"] += 1
    elif "new" in desc.lower() or "2.2" in desc: cats["new22"] += 1
    elif "cross" in desc.lower() or "technique" in desc.lower() or "Technique" in desc: cats["cross"] += 1
    else: cats["semantic"] += 1

for k, v in cats.items():
    print(f"  {k}: {v}")
