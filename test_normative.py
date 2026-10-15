#!/usr/bin/env python3
"""
test_normative.py — Pilnuje, żeby serwer podawał strukturę kryteriów tak,
jak stoi w normie.

Przegląd raportów (10 i 15.10.2026) pokazał, że agent mylił warunki AND/OR
z wyjątkami i dopisywał własne wyjątki. Źródłem był build_data.py, który
każdą listę <dl> oznaczał jako "Exceptions". Tu sprawdzamy typ listy dla
spornych kryteriów, wycofane 4.1.1 i ostrzeżenie o "złym kryterium".

Użycie:
  uv run python test_normative.py
"""

import importlib.util
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("server", Path(__file__).parent / "server.py")
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)

failures = []


def check(cond, msg):
    print(f"  {'ok  ' if cond else 'FAIL'} {msg}")
    if not cond:
        failures.append(msg)


# Typ listy pod zdaniem wiodącym — zgodnie z tekstem WCAG 2.2.
EXPECTED_KIND = {
    "2.2.2": "all",         # "all of the following are true"
    "1.4.13": "all",
    "1.2.1": "all",         # "the following are true, except when…" — wyjątek jest w zdaniu
    "2.2.1": "any",
    "2.5.2": "any",
    "3.3.8": "any",         # "unless that step provides at least one of the following"
    "1.4.11": "each",       # dwa osobne zakresy, nie wyjątki
    "1.4.3": "exceptions",
    "2.5.8": "exceptions",
    "1.1.1": "exceptions",
    "1.4.1": "",            # bez listy — uwaga o percepcji koloru jest informacyjna
}

print("Typy list w kryteriach:")
for sc_id, kind in EXPECTED_KIND.items():
    got = server.SCS[sc_id].get("list_kind", "")
    check(got == kind, f"{sc_id}: list_kind={got!r}, oczekiwano {kind!r}")

print("Uwagi oddzielone od treści normatywnej:")
check("color perception" not in server.SCS["1.4.1"]["normative_md"], "1.4.1: uwaga poza normative_md")
check(server.SCS["1.4.1"]["notes"], "1.4.1: uwaga w notes")
check("New" not in server.SCS["3.3.8"]["normative_md"].split("\n")[0], "3.3.8: bez znacznika 'New'")

print("Renderowanie get():")
out = server.get("2.2.2")
check("ALL must be true (AND)" in out, "2.2.2: nagłówek AND")
check("Exceptions" not in out, "2.2.2: brak sekcji Exceptions")
check("AT LEAST ONE must be true (OR)" in server.get("3.3.8"), "3.3.8: nagłówek OR")
check("closed list" in server.get("2.5.8"), "2.5.8: wyjątki jako lista zamknięta")
check("NORMATIVE" in out, "get(): etykieta źródła")

print("Wycofane 4.1.1:")
check(server.SCS["4.1.1"].get("removed") is True, "4.1.1: removed=True")
check("Obsolete and removed" in server.get("4.1.1"), "4.1.1: ostrzeżenie w get()")

print("get_technique:")
f78 = server.get_technique("F78")
check(all(s in f78 for s in ("1.4.11", "2.4.7", "2.4.13")), "F78: wszystkie trzy kryteria")
check("maps to 3 criteria" in f78, "F78: ostrzeżenie o wielu kryteriach")
check("Wrong criterion?" in server.get_technique("F78", sc="1.4.1"), "F78 + 1.4.1: ostrzeżenie")
check("is documented for 2.4.7" in server.get_technique("F78", sc="focus-visible"), "F78 + slug 2.4.7: potwierdzenie")

print("Etykiety źródła:")
check("INFORMATIVE" in server.get_understanding("1.4.3"), "get_understanding")
check("NOT a WCAG requirement" in server.get_pattern("dialog"), "get_pattern")
check("INFORMATIVE" in server.get_techniques("1.1.1"), "get_techniques")

if failures:
    print(f"\n❌ {len(failures)} błędów")
    sys.exit(1)
print("\n✅ test_normative: wszystko działa")
