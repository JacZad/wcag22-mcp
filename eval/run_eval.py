"""Porównanie metod wyszukiwania w serwerze: FTS5 (search), graf, lookup JSON (get), hybryda.

Użycie (z katalogu repo):
    PYTHONUTF8=1 uv run python eval/run_eval.py [--misses] [--en]

Zadanie A: pytanie → właściwe kryterium. Zadanie B: kryterium → powiązane kryteria.
Wejście: eval/eval_set.json. Serwer ładowany jest jako moduł, więc mierzymy
dokładnie to, co widzi klient (parsujemy wyjście narzędzi tam, gdzie to ma sens).
"""
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import server as s  # noqa: E402

SC_RE = re.compile(r"\b(\d\.\d{1,2}\.\d{1,2})\b")
STOP = set("""a an the to of for and or in on at is are it its my our be not no with without
must should needs need needs user users page pages site sites content that this when
every each does do doesnt cannot can from by as""".split())
KS = (1, 3, 5)


def uniq(seq):
    seen, out = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


# ─── Systemy do zadania A ───

def sys_fts5(q):
    """Kolejność kryteriów w wyjściu search()."""
    return uniq(m for m in SC_RE.findall(s.search(q)) if m in s.SCS)


def sys_search_sc(q):
    """Kryteria z sekcji „Kryteria sukcesu" w wyjściu search(), w kolejności wyświetlenia."""
    ids, in_sc = [], False
    for line in s.search(q).splitlines():
        if line.startswith("## "):
            in_sc = line.startswith("## Kryteria")
        elif in_sc:
            m = re.match(r"\S+ \*\*(\d\.\d+\.\d+)\*\*", line)
            if m:
                ids.append(m.group(1))
    return uniq(ids)


def sys_get(q):
    """Lookup JSON: _resolve() to to samo, co robi get() dla ID/sluga/tytułu."""
    sc = s._resolve(q)
    return [sc] if sc else []


def _norm_words(q):
    return [w for w in re.sub(r"[^\w\s]", " ", q.lower()).split()]


def _seeds(q):
    """Encje grafu rozpoznane w zapytaniu: kategorie, wzorce, techniki, definicje."""
    words = _norm_words(q)
    found = []
    for n in (3, 2, 1):
        for i in range(len(words) - n + 1):
            gram = words[i:i + n]
            if n == 1 and gram[0] in STOP:
                continue
            text = " ".join(gram)
            node = s._resolve_graph_node(text)
            if node and not node.startswith("SC:"):
                found.append(node)
            dnode = "DEF:" + text.replace(" ", "_")
            if dnode in s.GRAPH:
                found.append(dnode)
    return uniq(found)


def sys_graph(q):
    """Ekspansja z encji: SC sąsiadujące z rozpoznanymi węzłami, ważone 1/ln(2+stopień)."""
    G = s.GRAPH
    score = defaultdict(float)
    for seed in _seeds(q):
        w = 1.0 / math.log(2 + G.degree(seed))
        for nb in set(G.predecessors(seed)) | set(G.successors(seed)):
            if nb.startswith("SC:"):
                score[nb[3:]] += w
    return [k for k, _ in sorted(score.items(), key=lambda kv: (-kv[1], kv[0]))]


def rrf(*rankings, k=60):
    score = defaultdict(float)
    for r in rankings:
        for i, item in enumerate(r):
            score[item] += 1.0 / (k + i + 1)
    return [x for x, _ in sorted(score.items(), key=lambda kv: (-kv[1], kv[0]))]


def sys_hybrid(q):
    return rrf(sys_fts5(q), sys_graph(q))


SYSTEMS_A = {"get (JSON)": sys_get, "search (FTS5)": sys_fts5,
             "graf (encje)": sys_graph, "FTS5+graf (RRF)": sys_hybrid}


# ─── Systemy do zadania B ───

def _title(sc):
    return s.SCS[sc].get("title", sc)


def rel_fts5(sc):
    return [x for x in sys_fts5(_title(sc)) if x != sc]


def rel_graph_tool(sc):
    """Dokładnie to, co widzi model: graph_query(sc), SC z sekcji krawędzi (z obcięciem do 12)."""
    out = s.graph_query(sc)
    ids = [m for line in out.splitlines()[1:] if line.startswith("- ")
           for m in SC_RE.findall(line)]
    return [x for x in uniq(ids) if x != sc and x in s.SCS]


def rel_graph_ranked(sc):
    """Idealnie uszeregowany graf: SC–SC wg wagi + wspólne kategorie i wzorce."""
    G, node = s.GRAPH, "SC:" + sc
    score = defaultdict(float)
    for _, nb, d in G.out_edges(node, data=True):
        if nb.startswith("SC:") and d.get("weight"):
            score[nb[3:]] += d["weight"]
    for nb, _, d in G.in_edges(node, data=True):
        if nb.startswith("SC:") and d.get("weight"):
            score[nb[3:]] += d["weight"]
    for _, grp in G.out_edges(node):
        if grp.startswith(("CAT:", "PAT:")):
            for _, nb in G.out_edges(grp):
                if nb.startswith("SC:") and nb != node:
                    score[nb[3:]] += 1
    return [k for k, _ in sorted(score.items(), key=lambda kv: (-kv[1], kv[0]))]


def rel_hybrid(sc):
    return rrf(rel_fts5(sc), rel_graph_ranked(sc))


SYSTEMS_B = {"search (FTS5, tytuł)": rel_fts5, "graph_query (jak widzi model)": rel_graph_tool,
             "graf (idealnie uszeregowany)": rel_graph_ranked, "FTS5+graf (RRF)": rel_hybrid}


# ─── Metryki ───

def first_rank(ranking, expected):
    for i, x in enumerate(ranking):
        if x in expected:
            return i + 1
    return None


def evaluate_a(items):
    rows = {}
    for name, fn in SYSTEMS_A.items():
        per = []
        for it in items:
            r = fn(it["q"])
            per.append({"q": it["q"], "style": it["style"], "expected": it["expected"],
                        "ranking": r[:5], "rank": first_rank(r, set(it["expected"]))})
        rows[name] = per
    return rows


def summarize_a(per):
    n = len(per)
    out = {f"hit@{k}": sum(1 for p in per if p["rank"] and p["rank"] <= k) / n for k in KS}
    out["MRR"] = sum(1 / p["rank"] for p in per if p["rank"]) / n
    return out


def evaluate_b(items):
    rows = {}
    for name, fn in SYSTEMS_B.items():
        per = []
        for it in items:
            r = fn(it["sc"])
            exp = set(it["expected"])
            per.append({"sc": it["sc"], "expected": it["expected"], "ranking": r[:10],
                        "r5": len(exp & set(r[:5])) / len(exp),
                        "r10": len(exp & set(r[:10])) / len(exp),
                        "n_returned": len(r)})
        rows[name] = per
    return rows


def main():
    data = json.load(open(ROOT / "eval" / "eval_set.json", encoding="utf-8"))
    if "--en" in sys.argv:
        for it in data["find"]:
            if "q_en" in it:
                it["q"], it["style"] = it["q_en"], "pl->en"
    a, b = evaluate_a(data["find"]), evaluate_b(data["related"])
    show_misses = "--misses" in sys.argv

    print(f"## A. Pytanie → kryterium ({len(data['find'])} pytań)\n")
    print(f"{'system':20} {'hit@1':>6} {'hit@3':>6} {'hit@5':>6} {'MRR':>6}")
    for name, per in a.items():
        m = summarize_a(per)
        print(f"{name:20} {m['hit@1']:6.0%} {m['hit@3']:6.0%} {m['hit@5']:6.0%} {m['MRR']:6.2f}")

    print("\nhit@3 wg stylu pytania:")
    styles = sorted({it["style"] for it in data["find"]})
    print(f"{'system':20} " + " ".join(f"{st:>8}" for st in styles))
    for name, per in a.items():
        cells = []
        for st in styles:
            sub = [p for p in per if p["style"] == st]
            cells.append(f"{sum(1 for p in sub if p['rank'] and p['rank'] <= 3) / len(sub):8.0%}")
        print(f"{name:20} " + " ".join(cells))
    print("(liczba pytań: " + ", ".join(
        f"{st}={sum(1 for it in data['find'] if it['style'] == st)}" for st in styles) + ")")

    # Gdzie jedna metoda trafia, a druga nie
    fts, gr = a["search (FTS5)"], a["graf (encje)"]
    only_fts = [f["q"] for f, g in zip(fts, gr) if f["rank"] and f["rank"] <= 3 and not (g["rank"] and g["rank"] <= 3)]
    only_gr = [g["q"] for f, g in zip(fts, gr) if g["rank"] and g["rank"] <= 3 and not (f["rank"] and f["rank"] <= 3)]
    both_miss = [f["q"] for f, g in zip(fts, gr) if not (f["rank"] and f["rank"] <= 3) and not (g["rank"] and g["rank"] <= 3)]
    print(f"\nTrafia w top-3 tylko FTS5: {len(only_fts)}  |  tylko graf: {len(only_gr)}  |  żadne: {len(both_miss)}")
    if show_misses:
        for label, lst in (("tylko graf", only_gr), ("żadne", both_miss)):
            print(f"\n{label}:")
            for q in lst:
                print("  -", q)
        print("\nFTS5 — pudła (top-3):")
        for p in fts:
            if not (p["rank"] and p["rank"] <= 3):
                print(f"  - {p['q']!r}  oczekiwano {p['expected']}  dostał {p['ranking'][:3]}")

    print(f"\n## B. Kryterium → powiązane kryteria ({len(data['related'])} kryteriów)\n")
    # dev = zbiór, na którym dostrajano punktację grafu; holdout dopisano wcześniej.
    split_of = {it["sc"]: it.get("split", "dev") for it in data["related"]}
    print(f"{'system':32} {'dev@5':>6} {'dev@10':>7} {'hold@5':>7} {'hold@10':>8} {'zwróconych':>11}")
    for name, per in b.items():
        cells = []
        for sp in ("dev", "holdout"):
            sub = [p for p in per if split_of[p["sc"]] == sp]
            cells += [sum(p["r5"] for p in sub) / len(sub), sum(p["r10"] for p in sub) / len(sub)]
        n_ret = sum(p["n_returned"] for p in per) / len(per)
        print(f"{name:32} {cells[0]:6.0%} {cells[1]:7.0%} {cells[2]:7.0%} {cells[3]:8.0%} {n_ret:11.1f}")
    if show_misses:
        for name in ("graph_query (jak widzi model)", "graf (idealnie uszeregowany)"):
            print(f"\n{name}:")
            for p in b[name]:
                print(f"  {p['sc']}: oczekiwano {p['expected']}  top-10 {p['ranking']}")

    out = ROOT / "eval" / ("results_en.json" if "--en" in sys.argv else "results.json")
    json.dump({"A": a, "B": b}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
