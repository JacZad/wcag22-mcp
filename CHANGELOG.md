# Changelog

Format oparty na [Keep a Changelog](https://keepachangelog.com/pl/1.1.0/), wersjonowanie według [SemVer](https://semver.org/lang/pl/). Do wersji 1.0 zmiana drugiej cyfry może oznaczać niekompatybilne zmiany w narzędziach.

## [Niewydane]

### Naprawione

- Mapowanie technika → kryterium pochodzi teraz z `understanding.11tydata.js` (dane W3C), a nie z heurystyki po treści techniki. Wcześniej `get_techniques("2.1.1")` zwracało F105 (dotyczy 2.5.1, 2.1.1 pojawia się tylko w uwadze). Do przebudowy danych potrzebny jest `node`.
- `get_pattern(name)` — parametr nazywał się `pattern_name`, więc `name` i `pattern_id` były ignorowane i zwracany był indeks wzorców.

## [0.2.0] — 2026-10-10

### Zmienione (niekompatybilne)

- Narzędzi jest 13 zamiast 18. Zmiany nazw i parametrów:

  | Było | Jest |
  |---|---|
  | `get_sc`, `get_principle`, `get_guideline`, `get_hierarchy` | `get(identifier)` — `"1"` zwraca zasadę, `"2.4"` wytyczną, ID/slug/tytuł zwraca SC |
  | `get_failures(id)` | `get_techniques(id, failures_only=True)` |
  | `list_patterns()` | `get_pattern()` bez nazwy |
  | `graph_categories()` | `graph_query()` bez argumentu |
  | `get_understanding(id, full=True)` | `get_full_understanding(id)` |

- `get_understanding` zwraca tylko streszczenie. Pełny dokument W3C (5–40 KB) jest dostępny przez osobne `get_full_understanding`, przeznaczone do wywoływania na wyraźną prośbę użytkownika.

### Dodane

- 87 ręcznie napisanych streszczeń dokumentów Understanding (`understanding_summaries.md`), opartych na pełnych dokumentach W3C: cel, rozróżnienia i sposób decyzji, wyjątki, typowe błędy, powiązane SC. Zastępują mechaniczny wyciąg sekcji Intent.
- `apply_summaries.py` wgrywa streszczenia do `wcag-data.json` bez pełnej przebudowy; `build_data.py` ich nie nadpisuje.
- Wersja serwera widoczna w `status()` i w banerze startowym.

### Usunięte

- Techniki Flash i Silverlight (71 z 523) — zaśmiecały wyniki wyszukiwania. `build_data.py` pomija je na stałe.
- Pozostałości po wyszukiwaniu wektorowym (skrypty `rebuild_*`, testy embedderów, pliki `.npy`) oraz pipeline streszczeń technik generowanych przez Gemmę. Indeks technik powstaje z ich pełnej treści; pomiar na 20 zapytaniach nie wykazał przewagi streszczeń.

### Naprawione

- Poziomy zgodności: 2.4.7 Focus Visible (AA), 2.4.13 Focus Appearance, 2.5.6 Concurrent Input Mechanisms i 3.3.5 Help (AAA).
- `build_search_index.py` zapisuje indeks przez SQLite backup API, więc działa także, gdy serwer trzyma `search.db` otwarty.
- `build_data.py` odczytuje wynik pandoca w UTF-8 (na Windows przerywał się na znakach spoza cp1250).

## [0.1.0] — 2026-08-31

Pierwsza wersja wdrożona na Cloud Run.

- Kryteria sukcesu, techniki, definicje i dokumenty Understanding WCAG 2.2 ze źródeł W3C, polskie tytuły SC.
- Wszystkie wzorce ARIA APG, kalkulator kontrastu, graf wiedzy (networkx).
- Wyszukiwanie pełnotekstowe SQLite FTS5 (PL i EN) zamiast Ollamy.
- Transporty stdio, SSE i streamable-http, opcjonalna ochrona kluczem API.
- Obraz Docker dla Cloud Run z testem dymnym w pipeline.

[0.2.0]: https://github.com/JacZad/wcag22-mcp/compare/14d84ad...v0.2.0
[0.1.0]: https://github.com/JacZad/wcag22-mcp/commit/14d84ad
