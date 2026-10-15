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

from apply_summaries import load_summaries

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
        capture_output=True, text=True, encoding="utf-8", timeout=30
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


def _pandoc_str(html):
    """Convert an HTML fragment to Markdown via pandoc."""
    r = subprocess.run(
        ["pandoc", "-f", "html", "-t", "markdown", "--wrap=preserve"],
        input=html, capture_output=True, text=True, encoding="utf-8", timeout=30
    )
    if r.returncode != 0:
        print(f"  ⚠ pandoc error: {r.stderr[:200]}", file=sys.stderr)
        return ""
    md = r.stdout.strip().replace("\\'", "'").replace('\\"', '"')
    return _fix_w3c_links(md)


_NOTE_RE = re.compile(r'<(p|div)\s+class="note"[^>]*>.*?</\1>', re.S)


def _list_kind(lead):
    """
    Jak czytać listę pod zdaniem wiodącym kryterium.

    Pandoc oddaje każdą <dl> tak samo, więc dawniej wszystko lądowało jako
    "Exceptions" — a w 2.2.2 to warunki łączne (AND), w 3.3.8 alternatywy (OR),
    w 1.4.11 zakres (każdy punkt to osobny wymóg). Agent czytał to jako wyjątki.
    """
    low = " ".join(lead.lower().split())
    if "all of the following" in low or "the following are true" in low:
        return "all"
    if "at least one of the following" in low:
        return "any"
    if re.search(r"\bexcept\b", low):
        return "exceptions"
    return "each"


def _parse_sc_html(html):
    """Rozbij plik kryterium na zdanie wiodące, listę z jej typem i uwagi."""
    m = re.search(r'<section[^>]*class="sc[^"]*"[^>]*>(.*)</section>', html, re.S)
    inner = m.group(1) if m else html
    removed = "obsolete" in html[:300] or "This criterion no longer has utility" in html
    inner = re.sub(r'<h4>.*?</h4>', '', inner, flags=re.S)
    inner = re.sub(r'<p class="(conformance-level|change)">.*?</p>', '', inner, flags=re.S)

    dl = re.search(r'<dl>(.*?)</dl>', inner, re.S)
    before, after = (inner[:dl.start()], inner[dl.end():]) if dl else (inner, "")
    notes = [n.group(0) for n in _NOTE_RE.finditer(before + after)]
    lead_html = _NOTE_RE.sub('', before)
    tail_html = _NOTE_RE.sub('', after).strip()

    lead = _pandoc_str(lead_html)
    items = []
    if dl:
        for dt, dd in re.findall(r'<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>', dl.group(1), re.S):
            items.append({"label": _pandoc_str(dt), "text": _pandoc_str(dd)})
    if tail_html:
        lead = (lead + "\n\n" + _pandoc_str(tail_html)).strip()
    notes_md = [re.sub(r'^:::+.*$', '', _pandoc_str(n), flags=re.M).strip() for n in notes]

    kind = _list_kind(lead) if items else ""
    items_md = "\n\n".join(f"{it['label']}\n: {it['text']}" for it in items)
    return {
        "normative_md": lead,
        "list_kind": kind,
        "items": items,
        "items_md": items_md,
        "notes": [n for n in notes_md if n],
        "removed": removed,
    }


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
        
        parsed = _parse_sc_html(fpath.read_text(encoding="utf-8"))
        if parsed is None:
            continue

        scs[sc_id] = {
            "id": sc_id,
            "slug": slug,
            "title": title,
            "level": level,
            "version": f"WCAG 2.{ver[-1]}",
            "principle": principle,
            "guideline": guideline,
            **parsed,
            "w3c_url": f"https://www.w3.org/WAI/WCAG22/Understanding/{slug}"
        }
    
    return scs


# Techniki dla nierozwijanych już technologii (Flash, Silverlight) pomijamy:
# zaśmiecały wyniki wyszukiwania, a nikt już ich nie stosuje.
EXCLUDED_TECH_CATEGORIES = {"flash", "silverlight"}


def build_techniques():
    """Build technique entries from HTML files."""
    techniques = {}
    tech_base = REPO_DIR / "techniques"
    if not tech_base.exists():
        return techniques
    
    for cat_dir in sorted(tech_base.iterdir()):
        if not cat_dir.is_dir() or cat_dir.name.startswith('.'):
            continue
        if cat_dir.name in EXCLUDED_TECH_CATEGORIES:
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
                    # Mechanical short_md: "In brief" + "Intent" sections (overridden by understanding_summaries.md)
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


def _load_associated_techniques():
    """Autorytatywne mapowanie technika → SC z understanding.11tydata.js (W3C).

    Zwraca {sc_id: [tid, ...]} (sufficient, advisory i failure razem) albo {}
    gdy brak node/pliku. Bez tego techniki dostają SC tylko z heurystyki
    po treści, która łapie przypadkowe wzmianki (np. 2.1.1 w uwadze F105).
    """
    import subprocess, tempfile
    from sc_map import SC_MAP
    src = REPO_DIR / "understanding" / "understanding.11tydata.js"
    if not src.exists():
        return {}
    script = r"""import f from "./u.mjs";
const m = f({}).associatedTechniques;
const out = {};
const walk = (o, s) => {
  if (Array.isArray(o)) o.forEach(x => typeof x === "string" ? s.add(x) : walk(x, s));
  else if (o && typeof o === "object") Object.values(o).forEach(v => walk(v, s));
};
for (const [k, v] of Object.entries(m)) {
  const s = new Set();
  walk(v, s);
  out[k] = [...s].filter(x => /^[A-Z]+\d+$/.test(x));
}
console.log(JSON.stringify(out));
"""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "u.mjs").write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        (tmp / "dump.mjs").write_text(script, encoding="utf-8")
        try:
            res = subprocess.run(["node", "dump.mjs"], cwd=tmp, capture_output=True,
                                 text=True, encoding="utf-8", check=True)
        except (OSError, subprocess.CalledProcessError) as e:
            print(f"  ⚠ brak mapowania z understanding.11tydata.js ({e})", file=sys.stderr)
            return {}
    by_sc = {}
    for slug, tids in json.loads(res.stdout).items():
        if slug in SC_MAP:
            by_sc[SC_MAP[slug][0]] = tids
    return by_sc


def build_indexes(scs, techniques):
    """Build search and lookup indexes (technique→SC wg techniques[*].applies_to)."""
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
    
    for tid, tech in techniques.items():
        for sc_ref in tech["applies_to"]:
            tech_by_sc.setdefault(sc_ref, []).append(tid)
            if tech["category"] == "failures":
                failures_by_sc.setdefault(sc_ref, []).append(tid)

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

    print("Applying W3C technique→SC mapping...")
    assoc = _load_associated_techniques()
    mapped = {}
    for sc_id, tids in assoc.items():
        for tid in tids:
            if tid in techniques:
                mapped.setdefault(tid, []).append(sc_id)
    for tid, sc_ids in mapped.items():
        techniques[tid]["applies_to"] = sorted(set(sc_ids), key=lambda x: [int(p) for p in x.split('.')])
    print(f"  → {len(mapped)}/{len(techniques)} techniques mapped from W3C data")
    
    print("Building definitions...")
    definitions = build_definitions()
    print(f"  → {len(definitions)} definitions")
    
    print("Building understanding docs...")
    understanding = build_understanding(SC_MAP)
    print(f"  → {len(understanding)} docs")
    
    print("Building indexes...")
    indexes = build_indexes(scs, techniques)

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
    summaries = load_summaries()
    merge_count = 0
    for sc_id, sc in scs.items():
        slug = sc["slug"]
        und = understanding.get(slug, {})
        sc["understanding_full_md"] = und.get("full_md", "")
        # Ręczne streszczenie ma pierwszeństwo przed wyciągiem mechanicznym
        sc["understanding_short_md"] = summaries.get(sc_id) or und.get("short_md", "")
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
