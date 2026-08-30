#!/usr/bin/env python3
"""
build_data.py — Build wcag-data.json from w3c/wcag repo using Pandoc.

Converts all HTML files (SC, techniques, terms, understanding) to clean Markdown
via Pandoc, extracts metadata, builds indexes, and writes a single JSON file.
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# ── paths ──
REPO_DIR = Path(__file__).parent / "wcag-repo"
OUTPUT = Path(__file__).parent / "wcag-data.json"
SC_MAP_MODULE = Path(__file__).parent / "sc_map.py"
CATEGORIES_FILE = Path(__file__).parent / "categories-en.json"
PATTERNS_FILE = Path(__file__).parent / "patterns.json"

# Load SC ID mapping from sc_map.py
def _load_sc_map():
    """Load SC_MAP from sc_map.py."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("sc_map", SC_MAP_MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.SC_MAP, mod.PRINCIPLES, mod.GUIDELINES


# ── pandoc wrapper ──
def _pandoc(path):
    """Convert an HTML file to Markdown via pandoc."""
    r = subprocess.run(
        ["pandoc", "-f", "html", "-t", "markdown", "--wrap=preserve", str(path)],
        capture_output=True, text=True, timeout=30
    )
    if r.returncode != 0:
        print(f"  ⚠ pandoc error on {path.name}: {r.stderr[:200]}", file=sys.stderr)
        return ""
    return r.stdout.strip()


# ── metadata extraction ──

def _extract_meta_from_md(md, path):
    """Extract metadata from the first section (meta block) of a markdown doc."""
    meta = {}
    
    # Try meta section
    m = re.search(r'^ID:\s*(.+)$', md, re.MULTILINE)
    if m:
        meta["id"] = m.group(1).strip()
    
    m = re.search(r'^Technology:\s*(.+)$', md, re.MULTILINE)
    if m:
        meta["technology"] = m.group(1).strip()
    
    m = re.search(r'^Type:\s*(.+)$', md, re.MULTILINE)
    if m:
        meta["type"] = m.group(1).strip()
    
    # Conformance level (SC files)
    # The level appears after the h4 heading
    m = re.search(r'^####\s+(.+)$', md, re.MULTILINE)
    if m:
        meta["title"] = m.group(1).strip()
    
    # For SC files: find the standalone letter A/AA/AAA after the title
    lines = md.split('\n')
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped in ("A", "AA", "AAA") and len(stripped) <= 3:
            # Check it's not part of a list or definition
            meta["level"] = stripped
            break
    
    return meta


def _map_sc_slug(slug, applies_to):
    """Map a WCAG Understanding slug to an SC ID and add to list."""
    from sc_map import SC_MAP, SC_ID_TO_SLUG
    # Strip .html extension if present
    slug = slug.replace('.html', '').rstrip('/')
    if slug in SC_MAP:
        sc_id = SC_MAP[slug][0]
        if sc_id not in applies_to:
            applies_to.append(sc_id)
    elif slug in SC_ID_TO_SLUG or re.match(r'^\d+\.\d+\.\d+$', slug):
        # Direct SC ID that wasn't in SC_MAP — unusual but valid
        sc_id = slug
        if sc_id not in applies_to:
            applies_to.append(sc_id)


def _fix_w3c_links(md):
    """Replace relative W3C links with absolute URLs."""
    # ../../Understanding/bypass-blocks → /WAI/WCAG22/Understanding/bypass-blocks
    md = re.sub(
        r'(\()(\.\./)+Understanding/', r'\1https://www.w3.org/WAI/WCAG22/Understanding/', md
    )
    md = re.sub(
        r'(\()(\.\./)+techniques/', r'\1https://www.w3.org/WAI/WCAG22/Techniques/', md
    )
    # Anchors: (#name-role-value) → (https://www.w3.org/WAI/WCAG22/#name-role-value)
    md = re.sub(
        r'\(#([a-z][-a-z0-9]+)\)', r'(https://www.w3.org/WAI/WCAG22/#\1)', md
    )
    return md


# ── builders ──

def build_scs(sc_map):
    """Build SC entries from HTML files."""
    scs = {}
    for slug, (sc_id, title, level, principle, guideline) in sc_map.items():
        # Find the file across versions
        for ver in ['22', '21', '20']:
            fpath = REPO_DIR / "guidelines" / "sc" / ver / f"{slug}.html"
            if fpath.exists():
                break
        else:
            continue
        
        md = _pandoc(fpath)
        if not md:
            continue
        
        # Clean up: remove the outer fenced div with section class
        # Keep the content but strip the enclosing ::: block
        md = re.sub(r'^:::.*?sc.*\n', '', md, count=1)
        md = re.sub(r'\n:::$', '', md)
        
        # Split the SC into normative text and exceptions.
        #
        # Pandoc renders the exceptions as a definition list: the label sits on
        # its own line and the body below it starts with ": ". The previous
        # version looked for a trailing colon to spot the label — but it is the
        # normative sentence that usually ends in one ("except for the
        # following:"), so 17 criteria lost their normative text to the
        # exceptions block, and 1.1.1 swallowed its exceptions the other way.
        # The definition marker is unambiguous, so we cut on that instead.
        lines = [ln for ln in md.split('\n') if ln.strip() != ':::']

        level_idx = next((i for i, ln in enumerate(lines)
                          if ln.strip() in ("A", "AA", "AAA")), None)
        body = lines[level_idx + 1:] if level_idx is not None else lines

        # Kryteria wycofane (4.1.1) nie mają wiersza z poziomem, więc zostaje im
        # nagłówek tytułowy — tytuł trzymamy osobno, tu jest zbędny.
        while body and (not body[0].strip() or body[0].lstrip().startswith("#")):
            body = body[1:]

        def_idx = next((i for i, ln in enumerate(body) if re.match(r'^:\s', ln)), None)

        if def_idx is None:
            normative_parts, exception_parts = body, []
        else:
            # Etykieta wyjątku to ostatni niepusty wiersz przed treścią definicji.
            label_idx = def_idx - 1
            while label_idx >= 0 and not body[label_idx].strip():
                label_idx -= 1
            if label_idx < 0:
                label_idx = def_idx
            normative_parts = body[:label_idx]
            exception_parts = body[label_idx:]
        
        scs[sc_id] = {
            "id": sc_id,
            "slug": slug,
            "title": title,
            "level": level,
            "version": f"WCAG 2.{ver[-1]}",
            "principle": principle,
            "guideline": guideline,
            "normative_md": _fix_w3c_links('\n'.join(normative_parts).strip()),
            "exceptions_md": _fix_w3c_links('\n'.join(exception_parts).strip()) if exception_parts else "",
            "w3c_url": f"https://www.w3.org/WAI/WCAG22/Understanding/{slug}"
        }
    
    return scs


def build_techniques():
    """Build technique entries from HTML files."""
    techniques = {}
    tech_base = REPO_DIR / "techniques"
    if not tech_base.exists():
        return techniques
    
    for cat_dir in sorted(tech_base.iterdir()):
        if not cat_dir.is_dir() or cat_dir.name.startswith('.'):
            continue
        for fpath in sorted(cat_dir.iterdir()):
            if fpath.suffix != '.html':
                continue
            
            md = _pandoc(fpath)
            if not md:
                continue
            
            # Extract ID from meta section. Upstream źródło bywa uszkodzone —
            # techniques/general/G214.html deklaruje "ID: @@G210", przez co
            # technika G214 znikała z danych, a jej treść trafiała pod klucz
            # kolidujący z prawdziwym G210. Nazwa pliku jest wiarygodniejsza,
            # więc deklarowane ID przyjmujemy tylko, gdy ma poprawny kształt.
            m = re.search(r'^ID:\s*(.+)$', md, re.MULTILINE)
            declared = m.group(1).strip() if m else ""
            if re.fullmatch(r'[A-Za-z]+\d+', declared):
                tid = declared
            else:
                if declared:
                    print(f"  ⚠ {fpath.name}: nieprawidłowe ID '{declared}' — używam nazwy pliku",
                          file=sys.stderr)
                tid = fpath.stem
            
            # Extract type from meta
            m = re.search(r'^Type:\s*(.+)$', md, re.MULTILINE)
            ttype = m.group(1).strip() if m else "technique"
            
            # Extract related SCs from links (handle both relative and absolute)
            applies_to = []
            # Relative: ../../Understanding/bypass-blocks
            for m in re.finditer(r'\(\.\./\.\./Understanding/([^)\"#]+)', md):
                slug = m.group(1).rstrip('/')
                _map_sc_slug(slug, applies_to)
            # Absolute: https://www.w3.org/WAI/WCAG22/Understanding/bypass-blocks
            for m in re.finditer(r'\(https://www\.w3\.org/WAI/WCAG22/Understanding/([^)\"#]+)', md):
                slug = m.group(1).rstrip('/')
                _map_sc_slug(slug, applies_to)
            # Also check the text directly for "Success Criterion" or "Success Criteria"
            for m in re.finditer(r'Success Criteri[ao]n\s+(\d+\.\d+\.\d+)', md):
                sc_id = m.group(1)
                if sc_id not in applies_to:
                    applies_to.append(sc_id)
            # Also check for "Failure of Success Criterion X.Y.Z"
            for m in re.finditer(r'Failure of (?:Success Criterion|success criterion)\s+(\d+\.\d+\.\d+)', md):
                sc_id = m.group(1)
                if sc_id not in applies_to:
                    applies_to.append(sc_id)
            # Broader: comma-separated SC lists after "Success Criterion" (e.g. "1.4.3, 1.4.6 and 1.4.8")
            for m in re.finditer(r'(?:Success Criteri[ao]n|success criterion)\s+(\d+\.\d+\.\d+(?:\s*[,;]\s*\d+\.\d+\.\d+)*(?:\s*(?:,?\s*and|,?\s*or|,?\s*&)\s*\d+\.\d+\.\d+)?)', md):
                # Extract all SC IDs from the captured group
                all_scs = re.findall(r'\d+\.\d+\.\d+', m.group(1))
                for sc_id in all_scs:
                    if sc_id not in applies_to:
                        applies_to.append(sc_id)
            
            # Remove meta section from content_md
            content = re.sub(r'^:::.*?meta.*?^:::$', '', md, count=1, flags=re.DOTALL | re.MULTILINE)
            content = content.strip()
            
            techniques[tid] = {
                "id": tid,
                "category": cat_dir.name,
                "type": ttype,
                "applies_to": applies_to,
                "content_md": _fix_w3c_links(content)
            }
    
    return techniques


def build_definitions():
    """Build definition entries from term files."""
    definitions = {}
    for ver in ['22', '21', '20']:
        terms_dir = REPO_DIR / "guidelines" / "terms" / ver
        if not terms_dir.exists():
            continue
        for fpath in sorted(terms_dir.iterdir()):
            if fpath.suffix != '.html':
                continue
            
            md = _pandoc(fpath)
            if not md:
                continue
            
            # Pandoc renders <dfn>term</dfn> as: [term]{#id .dfn}
            m = re.match(r'^\[(.+?)\].*?\n\n(.+?)$', md, re.DOTALL)
            if not m:
                continue
            
            term = m.group(1).strip().lower()
            definition = m.group(2).strip()
            
            # Extract bullet details if present
            details = []
            for item in re.findall(r'^- (.+)', definition):
                details.append(item)
            
            definitions[term] = {
                "term": term,
                "definition_md": definition,
                "details": details
            }
    
    return definitions


def build_understanding(sc_map):
    """Build understanding entries with full_md + short_md (mechanical extract)."""
    docs = {}
    for slug, (sc_id, *_) in sc_map.items():
        for ver in ['22', '21', '20']:
            fpath = REPO_DIR / "understanding" / ver / f"{slug}.html"
            if fpath.exists():
                md = _pandoc(fpath)
                if md:
                    full = _fix_w3c_links(md)
                    # Mechanical short_md: "In brief" + "Intent" sections (placeholder until LLM summary)
                    brief = ""
                    intent = ""
                    m = re.search(r'## In brief(.+?)(?=:::$)', full, re.DOTALL)
                    if m:
                        brief = m.group(0).strip()
                    m = re.search(r'(## Intent.+?)(?=##|\Z)', full, re.DOTALL)
                    if m:
                        intent = m.group(1).strip()
                    short = f"{brief}\n\n{intent}" if (brief or intent) else ""

                    docs[slug] = {
                        "slug": slug,
                        "sc_id": sc_id,
                        "full_md": full,
                        "short_md": short,
                    }
                break
    return docs


def build_indexes(scs, techniques, understanding=None):
    """Build search and lookup indexes.
    
    Optionally accepts understanding docs to cross-reference technique→SC mappings."""
    by_level = {"A": [], "AA": [], "AAA": []}
    by_version = {}
    tech_by_sc = {}
    failures_by_sc = {}
    search_index = {}
    
    for sc_id, sc in scs.items():
        level = sc["level"]
        if level in by_level:
            by_level[level].append(sc_id)
        
        ver = sc["version"]
        if ver not in by_version:
            by_version[ver] = []
        by_version[ver].append(sc_id)
        
        # Build search keywords from title
        for word in re.findall(r'[a-zA-Z]{3,}', sc["title"]):
            key = word.lower()
            if key not in search_index:
                search_index[key] = []
            if sc_id not in search_index[key]:
                search_index[key].append(sc_id)
    
    # Source 1: technique → SC from applies_to
    for tid, tech in techniques.items():
        for sc_ref in tech["applies_to"]:
            if sc_ref not in tech_by_sc:
                tech_by_sc[sc_ref] = []
            tech_by_sc[sc_ref].append(tid)
            if tech["type"] == "Failure":
                if sc_ref not in failures_by_sc:
                    failures_by_sc[sc_ref] = []
                failures_by_sc[sc_ref].append(tid)
    
    # Source 2: Understanding docs → technique cross-reference
    # Scan each understanding doc for technique IDs and add those techniques to the SC
    if understanding:
        tech_pat = re.compile(r'\b((?:G|ARIA|H|C|F|SCR|PDF|SVR|SMIL|T|SL|FLASH|W)\d+)\b')
        for slug, und in understanding.items():
            sc_id = und.get("sc_id", "")
            if not re.match(r'^\d+\.\d+\.\d+$', str(sc_id)):
                continue
            full_md = und.get("full_md", "")
            for m in tech_pat.finditer(full_md):
                tid = m.group(1)
                if tid in techniques:
                    if sc_id not in tech_by_sc:
                        tech_by_sc[sc_id] = []
                    if tid not in tech_by_sc[sc_id]:
                        tech_by_sc[sc_id].append(tid)
                    # Also mark as failure if F-prefix
                    if tid.startswith('F'):
                        if sc_id not in failures_by_sc:
                            failures_by_sc[sc_id] = []
                        if tid not in failures_by_sc[sc_id]:
                            failures_by_sc[sc_id].append(tid)
    
    return {
        "by_level": by_level,
        "by_version": by_version,
        "tech_by_sc": {k: sorted(v) for k, v in tech_by_sc.items()},
        "failures_by_sc": {k: sorted(v) for k, v in failures_by_sc.items()},
        "search_index": dict(sorted(search_index.items()))
    }


# ── main ──

def main():
    t0 = time.time()
    
    print("Loading SC map...")
    SC_MAP, PRINCIPLES, GUIDELINES = _load_sc_map()
    
    print(f"Building SCs ({len(SC_MAP)} total)...")
    scs = build_scs(SC_MAP)
    print(f"  → {len(scs)} SCs built")
    
    print("Building techniques...")
    techniques = build_techniques()
    print(f"  → {len(techniques)} techniques")
    
    print("Building definitions...")
    definitions = build_definitions()
    print(f"  → {len(definitions)} definitions")
    
    print("Building understanding docs...")
    understanding = build_understanding(SC_MAP)
    print(f"  → {len(understanding)} docs")
    
    print("Building indexes...")
    indexes = build_indexes(scs, techniques, understanding)

    print("Loading categories...")
    if CATEGORIES_FILE.exists():
        with open(CATEGORIES_FILE, encoding="utf-8") as f:
            categories = json.load(f)
        print(f"  → {len(categories)} categories loaded")
    else:
        categories = {}
        print("  → no categories file found")

    print("Attaching techniques to SCs...")
    tech_by_sc = indexes.get("tech_by_sc", {})
    failures_by_sc = indexes.get("failures_by_sc", {})
    attached_count = 0
    for sc_id, sc in scs.items():
        tids = sorted(tech_by_sc.get(sc_id, []))
        fids = sorted(failures_by_sc.get(sc_id, []))
        sc["techniques"] = tids
        sc["failures"] = fids
        if tids:
            attached_count += 1
    print(f"  → {attached_count}/{len(scs)} SCs have techniques, "
          f"{sum(len(sc.get('techniques',[])) for sc in scs.values())} total edges")

    print("Merging understanding into SCs...")
    merge_count = 0
    for sc_id, sc in scs.items():
        slug = sc["slug"]
        und = understanding.get(slug, {})
        sc["understanding_full_md"] = und.get("full_md", "")
        sc["understanding_short_md"] = und.get("short_md", "")
        if und.get("full_md"):
            merge_count += 1
    print(f"  → {merge_count}/{len(scs)} SCs have understanding docs")

    print("Loading patterns...")
    if PATTERNS_FILE.exists():
        with open(PATTERNS_FILE, encoding="utf-8") as f:
            patterns = json.load(f)
        print(f"  → {len(patterns)} patterns loaded")
        # Validate: every pattern's scs must exist
        for pname, pdata in patterns.items():
            missing = [sc for sc in pdata.get("scs", []) if sc not in scs]
            if missing:
                print(f"  ⚠ Pattern '{pname}': missing SCs {missing}")
    else:
        patterns = {}
        print("  → no patterns file found")

    # Build hierarchy
    principles = {}
    for pn, p in PRINCIPLES.items():
        principles[pn] = {
            "num": pn,
            "title": p["title"],
            "guidelines": sorted([g for g, info in GUIDELINES.items() if info["principle"] == pn])
        }
    
    guidelines = {}
    for gn, g in GUIDELINES.items():
        guidelines[gn] = {
            "num": gn,
            "title": g["title"],
            "principle": g["principle"],
            "scs": sorted([sc["id"] for sc in scs.values() if sc["guideline"] == gn],
                          key=lambda x: [int(p) for p in x.split('.')])
        }
    
    data = {
        "version": "WCAG 2.2",
        "built": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "counts": {
            "scs": len(scs),
            "techniques": len(techniques),
            "definitions": len(definitions),
            "understanding": len(understanding),
            "categories": len(categories),
            "patterns": len(patterns),
        },
        "categories": categories,
        "patterns": patterns,
        "principles": principles,
        "guidelines": guidelines,
        "scs": dict(sorted(scs.items())),
        "techniques": dict(sorted(techniques.items())),
        "definitions": definitions,
        "indexes": indexes
    }
    
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    elapsed = time.time() - t0
    size_mb = os.path.getsize(OUTPUT) / (1024 * 1024)
    print(f"\n✅ Written to {OUTPUT}")
    print(f"   {size_mb:.1f} MB, {elapsed:.1f}s")


if __name__ == "__main__":
    main()
