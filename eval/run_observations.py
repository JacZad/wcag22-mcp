"""Test na obserwacjach (eval/observations.json): opis problemu → kryterium WCAG.

Użycie (z katalogu repo):
    PYTHONUTF8=1 uv run python eval/run_observations.py

observations.json: 128 polskich opisów z oczekiwanymi kryteriami (scIds).
observations_queries_en.json: angielskie zapytania napisane na podstawie samych
opisów, tak jak zrobiłby to model po instructions serwera. Prefiksy id: F =
scenariusz, M = opis, K = tylko nagłówek (kod, którego dotyczył, nie został
dołączony — te pozycje są w dużej mierze nierozstrzygalne).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_eval as r  # noqa: E402

D = Path(__file__).resolve().parent
obs = json.load(open(D / "observations.json", encoding="utf-8"))
qs = json.load(open(D / "observations_queries_en.json", encoding="utf-8"))


def stats(items, fn):
    n = len(items)
    h = {1: 0, 3: 0, 5: 0}
    mrr = 0
    for o in items:
        rk = r.first_rank(fn(o), set(o["scIds"]))
        for k in h:
            if rk and rk <= k:
                h[k] += 1
        if rk:
            mrr += 1 / rk
    return h[1] / n, h[3] / n, h[5] / n, mrr / n


systems = {"FTS5, polski opis": lambda o: r.sys_fts5(o["text"]),
           "FTS5, angielskie zapytanie": lambda o: r.sys_fts5(qs[o["id"]]),
           "search() — sekcja kryteriów": lambda o: r.sys_search_sc(qs[o["id"]]),
           "graf, angielskie zapytanie": lambda o: r.sys_graph(qs[o["id"]]),
           "FTS5+graf (RRF)": lambda o: r.sys_hybrid(qs[o["id"]])}
groups = {"wszystkie": obs,
          "F (scenariusze)": [o for o in obs if o["id"].startswith("F")],
          "M (opisy)": [o for o in obs if o["id"].startswith("M")],
          "K (tylko nagłówek kodu)": [o for o in obs if o["id"].startswith("K")]}

missing = [o["id"] for o in obs if o["id"] not in qs]
print(f"{len(obs)} obserwacji, brak zapytania: {missing or 'brak'}")
for gname, items in groups.items():
    print(f"\n== {gname} (n={len(items)})")
    print(f"{'system':28} {'hit@1':>6} {'hit@3':>6} {'hit@5':>6} {'MRR':>6}")
    for name, fn in systems.items():
        a, b, c, m = stats(items, fn)
        print(f"{name:28} {a:6.0%} {b:6.0%} {c:6.0%} {m:6.2f}")

print("\n== pudła FTS5 (angielskie zapytanie), top-3, grupy F i M")
for o in obs:
    if o["id"][0] in "FM":
        ranking = r.sys_fts5(qs[o["id"]])
        rk = r.first_rank(ranking, set(o["scIds"]))
        if not rk or rk > 3:
            print(f"  {o['id']:9} oczekiwano {o['scIds']}  dostał {ranking[:3]}  rank={rk}  | {qs[o['id']]}")
