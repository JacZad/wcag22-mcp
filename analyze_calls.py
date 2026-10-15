"""Podsumowanie logu wywołań (calls.jsonl) do optymalizacji opisów narzędzi.

Użycie:
    python analyze_calls.py [ścieżka/do/calls.jsonl]

Domyślnie czyta ~/.hermes/logs/calls.jsonl (na Mikrusie: ~/wcag22-mcp/logs/).
"""
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

# Narzędzia zwracają „nie znaleziono" jako zwykły tekst, więc flaga error
# prawie nigdy się nie zapala — chybienia poznajemy po początku odpowiedzi.
MISS_MARKERS = ("not found", "Nic nie znaleziono", "Empty query",
                "contains no searchable", "Invalid ", "not available")

# Kolejne wywołania tego samego klienta w tym oknie traktujemy jako jedną rozmowę.
SESSION_GAP_S = 120


def is_miss(rec):
    head = rec["result"][:200]
    return (bool(rec.get("error")) or any(m in head for m in MISS_MARKERS)
            or re.search(r"\b0 matches", head) is not None)


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / ".hermes" / "logs" / "calls.jsonl"
    recs = [json.loads(l) for l in path.open(encoding="utf-8") if l.strip()]
    if not recs:
        print("Pusty log.")
        return
    print(f"{len(recs)} wywołań, {recs[0]['ts'][:10]} … {recs[-1]['ts'][:10]}\n")

    by_tool = defaultdict(list)
    for r in recs:
        by_tool[r["tool"]].append(r)

    print("== Narzędzia: liczba, chybienia, czas (p50/p95 ms), rozmiar odpowiedzi (mediana B)")
    for tool, rs in sorted(by_tool.items(), key=lambda kv: -len(kv[1])):
        ms = sorted(r["ms"] for r in rs)
        p95 = ms[min(len(ms) - 1, int(len(ms) * 0.95))]
        miss = sum(is_miss(r) for r in rs)
        size = int(statistics.median(r["bytes"] for r in rs))
        print(f"  {tool:24} {len(rs):5}  chybienia {miss:4} ({miss/len(rs):.0%})  "
              f"{int(statistics.median(ms)):5}/{p95:<6} {size:7}")

    # Rekordy sprzed obsługi wielu kluczy nie mają pola client.
    print("\n== Klienci (etykieta klucza API): wywołania, chybienia, narzędzia")
    by_client = defaultdict(list)
    for r in recs:
        by_client[r.get("client") or "(brak)"].append(r)
    for name, rs in sorted(by_client.items(), key=lambda kv: -len(kv[1])):
        tools = Counter(r["tool"] for r in rs).most_common(3)
        print(f"  {name:20} {len(rs):5}  chybienia {sum(is_miss(r) for r in rs):4}  "
              + ", ".join(f"{t} {n}" for t, n in tools))

    print("\n== Chybione wywołania (co model wpisał, a nie zadziałało)")
    misses = Counter((r["tool"], json.dumps(r["args"], ensure_ascii=False)) for r in recs if is_miss(r))
    for (tool, args), n in misses.most_common(25):
        print(f"  {n:3}x {tool}({args})")

    print("\n== Najczęstsze zapytania do search()")
    q = Counter(r["args"].get("query", "").lower() for r in by_tool.get("search", []))
    for text, n in q.most_common(15):
        print(f"  {n:3}x {text}")

    # Sekwencje: po czym model sięga do kolejnego narzędzia. Dużo
    # search → search albo get → get(not found) znaczy, że opis nie wystarcza.
    print("\n== Częste sekwencje narzędzi w jednej rozmowie (klient = ip + user-agent + etykieta klucza)")
    clients = defaultdict(list)
    for r in recs:
        clients[(r["ip"], r["ua"], r.get("client", ""))].append(r)
    pairs = Counter()
    for rs in clients.values():
        for a, b in zip(rs, rs[1:]):
            gap = (datetime.fromisoformat(b["ts"]) - datetime.fromisoformat(a["ts"])).total_seconds()
            if gap <= SESSION_GAP_S:
                pairs[(a["tool"], b["tool"])] += 1
    for (a, b), n in pairs.most_common(15):
        print(f"  {n:3}x {a} -> {b}")


if __name__ == "__main__":
    main()
