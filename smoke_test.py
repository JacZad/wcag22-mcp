#!/usr/bin/env python3
"""
smoke_test.py — Sprawdza, że zbudowany obraz naprawdę potrafi obsłużyć
wszystkie narzędzia MCP.

Powstał dlatego, że produkcja przez dłuższy czas odpowiadała
"Graph is not available" i zwracała jeden wynik wyszukiwania zamiast
kilkunastu — a z zewnątrz nic tego nie zdradzało, bo błędy były połykane.
Test wywołuje każde narzędzie i uznaje za awarię nie tylko wyjątek, ale też
odpowiedź, która wygląda na cichą degradację.

Użycie:
  python3 smoke_test.py

Kod wyjścia 0, gdy wszystko działa; 1 przy pierwszym problemie.
"""

import importlib.util
import sys
from pathlib import Path

SERVER = Path(__file__).parent / "server.py"

# Fragmenty, które w pierwszej linii odpowiedzi oznaczają, że narzędzie
# nie zrobiło tego, o co prosiliśmy.
FAILURE_MARKERS = (
    "not available",
    "not found",
    "Graph is not available",
    "Empty query",
    "Invalid ",
)

# (narzędzie, argumenty, minimalna sensowna długość odpowiedzi)
CHECKS = [
    ("status",            (),                              200),
    ("get_sc",            ("1.4.3",),                      300),
    ("get_sc",            ("kontrast",),                   300),
    ("get_sc",            ("non-text-content",),           300),
    ("get_sc",            ("4.1.1",),                      200),
    ("get_definition",    ("assistive technology",),       200),
    ("get_techniques",    ("1.1.1",),                      200),
    ("get_technique",     ("G18",),                        500),
    ("get_technique",     ("g18",),                        500),
    ("get_technique",     ("G214",),                       300),
    ("get_failures",      ("2.4.7",),                      100),
    ("get_understanding", ("1.4.3",),                      500),
    ("get_understanding", ("1.4.3", True),                1000),
    ("check_contrast",    ("#047857", "#FFFFFF"),          200),
    ("check_contrast",    ("000", "fff"),                  200),
    ("get_principle",     ("1",),                          300),
    ("get_guideline",     ("2.4",),                        200),
    ("get_hierarchy",     ("2.4",),                        200),
    ("list_scs",          ("AA",),                         500),
    ("get_pattern",       ("combobox",),                   500),
    ("list_patterns",     (),                              500),
    # Progi dobrane tak, żeby odróżnić pełny indeks od trybu awaryjnego:
    # przy sprawnym FTS5 te zapytania zwracają odpowiednio ok. 2800, 1300 i 600
    # znaków, a bez indeksu — 665, 284 i 253.
    ("search",            ("keyboard focus",),            1200),
    ("search",            ("kontrast",),                   600),
    ("search",            ("aria-describedby",),           400),
    ("graph_query",       ("1.4.3",),                      300),
    ("graph_query",       ("combobox",),                   200),
    ("graph_between",     ("1.4.3", "1.4.1"),              200),
    ("graph_categories",  (),                             1000),
]


def load_server():
    spec = importlib.util.spec_from_file_location("wcag22_server", SERVER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    srv = load_server()
    failures = []

    # Podsystemy opcjonalne muszą być aktywne — to jest sedno tego testu.
    if srv.GRAPH is None:
        failures.append("graf wiedzy wyłączony (brak networkx?)")
    if srv.SEARCH_DB is None:
        failures.append("indeks FTS5 niedostępny (brak embeddings/search.db?)")

    for line in srv._subsystem_status_lines():
        print(f"  {line}")
    print()

    for name, args, min_len in CHECKS:
        label = f"{name}({', '.join(repr(a) for a in args)})"
        try:
            out = getattr(srv, name)(*args)
        except Exception as e:
            failures.append(f"{label} — wyjątek {type(e).__name__}: {e}")
            print(f"  FAIL {label}")
            continue

        first_line = out.splitlines()[0] if out.strip() else ""
        if len(out) < min_len:
            failures.append(f"{label} — odpowiedź krótsza niż {min_len} znaków ({len(out)})")
            print(f"  FAIL {label}  [{len(out)} znaków]")
        elif any(marker in first_line for marker in FAILURE_MARKERS):
            failures.append(f"{label} — odpowiedź wygląda na błąd: {first_line[:80]}")
            print(f"  FAIL {label}  [{first_line[:60]}]")
        else:
            print(f"  ok   {label}  [{len(out)} znaków]")

    print()
    if failures:
        print(f"❌ {len(failures)} problemów:")
        for f in failures:
            print(f"   - {f}")
        return 1

    print(f"✅ {len(CHECKS)} wywołań, wszystkie podsystemy aktywne")
    return 0


if __name__ == "__main__":
    sys.exit(main())
