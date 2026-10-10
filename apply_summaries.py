#!/usr/bin/env python3
"""
Wgrywa ręcznie napisane streszczenia Understanding (understanding_summaries.md)
do pola understanding_short_md w wcag-data.json.

Format pliku źródłowego: sekcje zaczynające się od linii "=== <ID SC>".
build_data.py korzysta z load_summaries(), więc pełna przebudowa danych
zachowuje streszczenia; ten skrypt służy do szybkiej aktualizacji bez niej.

Po zmianie streszczeń przebuduj indeks wyszukiwania: python build_search_index.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SUMMARIES = ROOT / "understanding_summaries.md"
DATA = ROOT / "wcag-data.json"


def load_summaries(path=SUMMARIES):
    """Mapa ID SC → streszczenie w Markdownie. Brak pliku daje pustą mapę."""
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    parts = re.split(r"^=== (\S+)\n", text, flags=re.M)[1:]
    return {parts[i]: parts[i + 1].strip() for i in range(0, len(parts), 2)}


def main():
    summaries = load_summaries()
    if not summaries:
        sys.exit(f"Brak streszczeń w {SUMMARIES.name}")

    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)

    scs = data["scs"]
    unknown = sorted(set(summaries) - set(scs))
    missing = sorted(set(scs) - set(summaries))
    if unknown:
        sys.exit(f"Streszczenia dla nieznanych SC: {', '.join(unknown)}")

    for sc_id, summary in summaries.items():
        scs[sc_id]["understanding_short_md"] = summary

    with open(DATA, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Wgrano {len(summaries)} streszczeń do {DATA.name}")
    if missing:
        print(f"Bez streszczenia (zostaje wyciąg mechaniczny): {', '.join(missing)}")


if __name__ == "__main__":
    main()
