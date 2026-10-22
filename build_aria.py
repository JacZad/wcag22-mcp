#!/usr/bin/env python3
"""
build_aria.py — Build aria-data.json from the WAI-ARIA 1.2 Recommendation.

Source: https://www.w3.org/TR/wai-aria-1.2/ saved as aria-src/wai-aria-1.2.html
(ignored by git, like wcag-repo/). Roles, states and properties are converted
to Markdown via Pandoc. RFC 2119 sentences (MUST, SHOULD NOT…) are extracted
separately so the server can show which statements are requirements.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

from bs4 import BeautifulSoup

SRC = Path(__file__).parent / "aria-src" / "wai-aria-1.2.html"
OUTPUT = Path(__file__).parent / "aria-data.json"
SPEC_URL = "https://www.w3.org/TR/wai-aria-1.2/"

# Longest first, so "MUST NOT" wins over "MUST".
RFC_KEYWORDS = ["MUST NOT", "SHALL NOT", "SHOULD NOT", "NOT RECOMMENDED",
                "MUST", "SHALL", "REQUIRED", "SHOULD", "RECOMMENDED", "MAY", "OPTIONAL"]


def _pandoc(html):
    r = subprocess.run(
        ["pandoc", "-f", "html", "-t", "gfm-raw_html", "--wrap=none"],
        input=html, capture_output=True, text=True, encoding="utf-8", timeout=30,
    )
    if r.returncode != 0:
        print(f"  ⚠ pandoc: {r.stderr[:200]}", file=sys.stderr)
        return ""
    return r.stdout.strip()


def _clean(md):
    # Spec cross-references are noise outside the spec page.
    md = re.sub(r"\]\(#[^)]*\)", "]", md)
    md = re.sub(r"\[([^\]]*)\]", r"\1", md)
    return re.sub(r"\n{3,}", "\n\n", md).strip()


def _sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z])", text) if s.strip()]


def _rfc_statements(desc):
    """Sentences that contain an RFC 2119 keyword, with the strongest keyword."""
    out = []
    for p in desc.find_all(["p", "li"]):
        if not p.find(class_="rfc2119"):
            continue
        text = re.sub(r"\s+", " ", p.get_text(" "))
        text = re.sub(r"\s+([.,;:)])", r"\1", text).strip()
        for s in _sentences(text):
            found = [k for k in RFC_KEYWORDS if re.search(rf"\b{k}\b", s)]
            if found:
                out.append({"keyword": found[0], "text": s})
    return out


def _characteristics(table):
    rows = {}
    if not table:
        return rows
    for tr in table.select("tbody tr"):
        th, td = tr.find("th"), tr.find("td")
        if th and td:
            key = th.get_text(" ", strip=True).rstrip(":")
            rows[key] = re.sub(r"\s+", " ", td.get_text(" ", strip=True))
    return rows


def _entry(sec, kind):
    name = sec["id"]
    desc = sec.find(class_=re.compile(r"(role|property|state)-description"))
    table = sec.find("table", class_=re.compile(r"(role|property|state)-features|def"))
    chars = _characteristics(table)
    entry = {
        "name": name,
        "kind": kind,
        "description_md": _clean(_pandoc(str(desc))) if desc else "",
        "rfc": _rfc_statements(desc) if desc else [],
        "characteristics": chars,
        "url": f"{SPEC_URL}#{name}",
    }
    if kind == "role":
        entry["abstract"] = chars.get("Is Abstract", "").lower() == "true"
    return entry


def build():
    soup = BeautifulSoup(SRC.read_text(encoding="utf-8"), "html.parser")
    roles, attributes = {}, {}
    for sec in soup.find_all("section", class_="role"):
        roles[sec["id"]] = _entry(sec, "role")
    for cls, kind in (("property", "property"), ("state", "state")):
        for sec in soup.find_all("section", class_=cls):
            if sec.get("id", "").startswith("aria-"):
                attributes[sec["id"]] = _entry(sec, kind)
    data = {
        "spec": "WAI-ARIA 1.2",
        "url": SPEC_URL,
        "roles": roles,
        "attributes": attributes,
        "counts": {
            "roles": len(roles),
            "attributes": len(attributes),
            "rfc_statements": sum(len(e["rfc"]) for e in [*roles.values(), *attributes.values()]),
        },
    }
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"✅ {OUTPUT.name}: {data['counts']}")


if __name__ == "__main__":
    build()
