# WCAG 2.2 MCP Server

Serwer MCP (Model Context Protocol) z pełną bazą wiedzy WCAG 2.2 — kryteria sukcesu, techniki, definicje, objaśnienia, wzorce ARIA APG i graf powiązań.

Umożliwia asystentom AI (Hermes, Claude Code, Cursor, Copilot i inne) udzielanie precyzyjnych odpowiedzi na pytania o dostępność cyfrową bez halucynacji — dane pochodzą bezpośrednio ze specyfikacji W3C.

---

## Spis treści

- [Funkcje](#funkcje)
- [Wymagania](#wymagania)
- [Szybki start](#szybki-start)
- [Transporty](#transporty)
- [Uwierzytelnianie API key](#uwierzytelnianie-api-key)
- [Dostępne narzędzia](#dostępne-narzędzia)
- [Konfiguracja klientów MCP](#konfiguracja-klientów-mcp)
  - [Hermes Agent](#hermes-agent)
  - [Claude Desktop / Code](#claude-desktop--code)
  - [Cursor](#cursor)
- [Deployment](#deployment)
  - [Cloudflare Tunnel](#cloudflare-tunnel)
  - [Systemd (Linux)](#systemd-linux)
  - [launchd (macOS)](#launchd-macos)
- [Logowanie i troubleshooting](#logowanie-i-troubleshooting)
- [Dane i budowa](#dane-i-budowa)
- [Licencja](#licencja)

---

## Funkcje

| Funkcja | Opis |
|---|---|
| **87 kryteriów sukcesu** | Wszystkie SC WCAG 2.2 (A, AA, AAA) z pełnym tekstem normatywnym |
| **520+ technik** | Techniki wystarczające, zalecane i błędów (G, H, F, ARIA, CSS, SCR, SVR, PDF…) |
| **101 definicji** | Słownik terminów WCAG z objaśnieniami i przykładami |
| **Objaśnienia (Understanding)** | Pełne dokumenty Understanding dla każdego SC |
| **Polskie tytuły** | SC wyświetlane z oficjalnym tłumaczeniem PL |
| **Wzorce ARIA APG** | Combobox, Dialog, Tooltip, Tree, Treegrid, Carousel i więcej — z kodem HTML, klawiaturą, zarządzaniem fokusem |
| **Graf wiedzy** | Połączenia między SC, technikami, definicjami i kategoriami — szukaj powiązań i najkrótszych ścieżek |
| **Kontrast** | Kalkulator WCAG AA/AAA dla hex kolorów |
| **Wyszukiwanie pełnotekstowe** | SQLite FTS5 po kryteriach, definicjach i technikach; zapytania PL i EN |
| **API key** | Opcjonalne zabezpieczenie dla deploymentów publicznych |
| **Logowanie** | Wszystkie żądania i odpowiedzi logowane do pliku |

---

## Wymagania

- **Python 3.10+**
- **pip: `mcp`** (pakiet SDK) — `pip install mcp`
- Opcjonalnie: `networkx` — narzędzia grafu (`graph_query`, `graph_between`, `graph_categories`)
- Wyszukiwanie nie wymaga żadnej usługi zewnętrznej — indeks FTS5 jest wbudowany w `embeddings/search.db`

```bash
pip install mcp networkx
```

---

## Szybki start

```bash
# 1. Sklonuj repozytorium
git clone <repo-url>
cd hermes-mcp-wcag22

# 2. (Opcjonalnie) Utwórz venv
python3 -m venv .venv
source .venv/bin/activate
pip install mcp networkx

# 3. Uruchom w trybie stdio (dla lokalnych klientów MCP)
python3 server.py

# 4. Albo jako serwer HTTP
python3 server.py --transport streamable-http --port 9100
```

Po uruchomieniu serwer loguje się do `~/.hermes/logs/wcag22-mcp.log`.

---

## Transporty

### stdio (domyślny)

Dla lokalnych klientów MCP (Hermes, Claude Desktop). Komunikacja przez stdin/stdout.

```bash
python3 server.py
```

### SSE (Server-Sent Events)

Klasyczny HTTP SSE. Endpoint: `/sse`.

```bash
python3 server.py --transport sse --port 9099
```

### streamable-http (zalecany dla HTTP)

Nowoczesny transport HTTP MCP, obsługuje strumieniowanie. Endpoint: `/mcp`.

```bash
python3 server.py --transport streamable-http --port 9100
```

Klient wysyła POST z ciałem JSON-RPC na `http://host:port/mcp`.

---

## Uwierzytelnianie API key

Opcjonalne zabezpieczenie przed nieautoryzowanym dostępem.

### Włączenie

```bash
# Przez argument CLI
python3 server.py --transport streamable-http --port 9100 --api-key "tajny-klucz"

# Lub przez zmienną środowiskową
export WCAG22_API_KEY="tajny-klucz"
python3 server.py --transport streamable-http --port 9100
```

### Działanie

- Klient musi wysłać nagłówek `X-API-Key: tajny-klucz` w każdym żądaniu
- Brak klucza → `401 Unauthorized`
- Błędny klucz → `401 Unauthorized`
- Jeśli `--api-key` nie jest ustawiony — serwer działa bez zabezpieczenia (kompatybilność wsteczna)

### Przykład curl

```bash
# Z kluczem
curl -X POST http://host:9100/mcp \
  -H "Content-Type: application/json" \
  -H "X-API-Key: tajny-klucz" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# Bez klucza — 401
curl -X POST http://host:9100/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

### Wygenerowanie klucza

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## Dostępne narzędzia

Serwer udostępnia następujące narzędzia MCP:

| Narzędzie | Opis |
|---|---|
| `get_sc(identifier)` | Pobiera kryterium sukcesu (np. `"1.1.1"`, `"non-text-content"`) |
| `get_definition(term)` | Definicja terminu WCAG (np. `"assistive technology"`) |
| `get_techniques(identifier)` | Lista technik dla SC |
| `get_technique(technique_id)` | Pełna treść techniki (np. `"G18"`, `"H37"`, `"F3"`) |
| `get_failures(identifier)` | Najczęstsze błędy dla SC |
| `get_understanding(identifier)` | Dokument Understanding dla SC |
| `list_scs(level)` | Lista SC, opcjonalnie filtrowana (`"A"`, `"AA"`, `"AAA"`) |
| `get_hierarchy(id)` | Zasada (1-4) lub wytyczna (np. `"2.4"`) z listą SC |
| `check_contrast(fg, bg)` | Kalkulator kontrastu WCAG (hex) |
| `search(query)` | Wyszukiwanie pełnotekstowe FTS5 (kryteria, definicje, techniki; PL i EN) |
| `get_pattern(name)` | Wzorzec ARIA APG (np. `"combobox"`, `"dialog"`, `"tooltip"`) |
| `list_patterns()` | Lista dostępnych wzorców |
| `graph_query(entity)` | Zapytanie do grafu wiedzy |
| `graph_between(a, b)` | Połączenia między dwoma encjami w grafie |
| `graph_categories()` | Kategorie tematyczne ze statystykami |
| `status()` | Status serwera i statystyki danych |

---

## Konfiguracja klientów MCP

### Hermes Agent

Dodaj do `~/.hermes/config.yaml`:

#### Lokalnie (stdio)

```yaml
mcp_servers:
  wcag22:
    command: ".venv/bin/python3"
    args: ["ścieżka/do/server.py"]
```

#### Zdalnie (streamable-http)

```yaml
mcp_servers:
  wcag22:
    url: "https://twoja-domena.pl/mcp"
    headers:
      X-API-Key: "tajny-klucz"
    connect_timeout: 30
    timeout: 60
```

Po restarcie Hermesa narzędzia będą dostępne jako `mcp_wcag22_get_sc`, `mcp_wcag22_search` itd.

### Claude Desktop / Code

```json
{
  "mcpServers": {
    "wcag22": {
      "command": "python3",
      "args": ["ścieżka/do/server.py"],
      "env": {}
    }
  }
}
```

### Cursor

W ustawieniach Cursor → Features → MCP → Add Server:

```
Typ: stdio
Polecenie: python3
Argumenty: ścieżka/do/server.py
```

---

## Deployment

### Cloudflare Tunnel

> **Uwaga:** Przy deploymencie przez Cloudflare Tunnel mogą wystąpić błędy `502 Bad Gateway` lub `520 unknown origin error`. Poniższa konfiguracja rozwiązuje te problemy.

#### 1. Uruchom serwer

```bash
python3 server.py --transport streamable-http --port 9100 --api-key "$WCAG22_API_KEY"
```

Upewnij się, że serwer nasłuchuje na `127.0.0.1:9100`.

#### 2. Plik konfiguracyjny tunnel (`config.yml`)

```yaml
tunnel: <id-tunelu>
credentials-file: /root/.cloudflared/<id-tunelu>.json

ingress:
  - hostname: twoja-domena.pl
    service: http://localhost:9100
    originRequest:
      noTLSVerify: true
      noHappyEyeballs: false
      keepAliveConnections: 25
      keepAliveTimeout: 120s
      httpHostHeader: twoja-domena.pl
      proxyConnectionTimeout: 30s
  - service: http_status:404
```

#### 3. Rozwiązywanie problemów z Cloudflare

| Objaw | Rozwiązanie |
|---|---|
| `502 Bad Gateway` | Sprawdź, czy serwer faktycznie nasłuchuje na porcie. `cloudflared` musi mieć dostęp do `localhost:9100`. |
| `520 unknown origin error` | Dodaj `originRequest.noTLSVerify: true`. Upewnij się, że `originRequest.httpHostHeader` wskazuje na domenę docelową. |
| `406 Not Acceptable` | Klient musi wysłać `Accept: application/json`. Niektóre klienty MCP tego nie robią — rozważ dodanie `X-Accel-Buffering: no`. |
| Timeout | Zwiększ `originRequest.keepAliveTimeout` do 120s. Sprawdź, czy `cloudflared` jest w najnowszej wersji. |
| Client must accept application/json | FastMCP wymaga `Accept: application/json` — wszystkie nowoczesne biblioteki MCP SDK wysyłają go automatycznie. |

### Systemd (Linux)

Plik `/etc/systemd/system/wcag22-mcp.service`:

```ini
[Unit]
Description=WCAG 2.2 MCP Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/hermes-mcp-wcag22
Environment=WCAG22_API_KEY=tajny-klucz
ExecStart=/opt/hermes-mcp-wcag22/.venv/bin/python3 server.py --transport streamable-http --port 9100
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now wcag22-mcp
```

### launchd (macOS)

Plik `~/Library/LaunchAgents/com.wcag22.mcp.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.wcag22.mcp</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/bot/hermes-mcp-wcag22/.venv/bin/python3</string>
        <string>/Users/bot/hermes-mcp-wcag22/server.py</string>
        <string>--transport</string>
        <string>streamable-http</string>
        <string>--port</string>
        <string>9100</string>
        <string>--api-key</string>
        <string>tajny-klucz</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>/Users/bot/hermes-mcp-wcag22</string>
    <key>StandardOutPath</key>
    <string>/Users/bot/.hermes/logs/wcag22-mcp-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/bot/.hermes/logs/wcag22-mcp-stderr.log</string>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.wcag22.mcp.plist
```

---

## Logowanie i troubleshooting

### Lokalizacja logów

```
~/.hermes/logs/wcag22-mcp.log
```

Każde żądanie i odpowiedź są logowane z timestampem, nazwą narzędzia, argumentami, czasem wykonania i rozmiarem odpowiedzi.

### Przykład logu

```
========================================================================
  📥 ZAPYTANIE  |  2026-07-25 12:30:15
========================================================================
  Narzędzie:    get_pattern()
  Argumenty:    pattern_name=combobox
  Źródło:       127.0.0.1
------------------------------------------------------------------------
  📤 ODPOWIEDŹ  |  2026-07-25 12:30:15  |  ✅ OK  |  6.2 KB  |  4ms
========================================================================
```

### Najczęstsze problemy

| Problem | Przyczyna | Rozwiązanie |
|---|---|---|
| `mcp package not installed` | Brak zależności | `pip install mcp` |
| Serwer nie startuje | Brak `wcag-data.json` | Uruchom `python3 build_data.py` |
| `401 Unauthorized` | Brak/wrong API key | Dodaj `X-API-Key` do żądania |
| `406 Not Acceptable` | Brak `Accept: application/json` | Klient MCP SDK wysyła go automatycznie |
| `502 Bad Gateway` | Cloudflare nie ma dostępu do backendu | Sprawdź port i `originRequest` w configu |
| Wyszukiwanie zwraca „tryb awaryjny" | Brak `embeddings/search.db` w obrazie | Sprawdź `COPY` w Dockerfile, przebuduj: `python3 build_search_index.py` |

### Testowanie ręczne

```bash
# Lista narzędzi (stdio)
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 server.py

# Lista narzędzi (HTTP)
curl -X POST http://127.0.0.1:9100/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "X-API-Key: tajny-klucz" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# Wywołanie narzędzia
curl -X POST http://127.0.0.1:9100/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "X-API-Key: tajny-klucz" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_sc","arguments":{"identifier":"1.4.3"}}}'
```

### Sprawdzenie statusu

```bash
curl -X POST http://127.0.0.1:9100/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"status","arguments":{}}}'
```

---

## Dane i budowa

### Struktura repozytorium

```
├── server.py            # Serwer MCP (główny plik)
├── build_data.py        # Skrypt budujący wcag-data.json ze źródeł W3C
├── wcag-data.json       # Baza danych WCAG 2.2 (generowana)
├── build_search_index.py # Skrypt budujący indeks FTS5
├── smoke_test.py        # Test dymny wszystkich narzędzi (uruchamiany w Cloud Build)
├── embeddings/          # Indeks wyszukiwania (generowany)
│   ├── search.db        # Baza SQLite FTS5 — jedyny plik używany w czasie działania
│   └── tech_index.json  # Podsumowania technik (materiał wejściowy dla indeksu)
├── patterns/            # Definicje wzorców ARIA APG (YAML/JSON)
└── README.md
```

### Dodawanie nowych wzorców ARIA

Dodaj wpis do `patterns/` w formacie:

```json
{
  "nazwa-wzorca": {
    "name": "Pełna nazwa",
    "apg_url": "https://www.w3.org/WAI/ARIA/apg/patterns/nazwa/",
    "first_rule_of_aria": "Zanim użyjesz ARIA...",
    "native_alternatives": [
      { "when": "Gdy potrzebujesz...", "html": "…", "benefits": "…" }
    ],
    "roles": { "element": "role" },
    "required_attributes": { "element": ["atrybut"] },
    "keyboard": ["Strzałka → rozwija"],
    "focus_management": ["Roving tabindex"],
    "scs": ["1.3.1", "2.1.1", "4.1.2"],
    "techniques": ["ARIA14", "H91"]
  }
}
```

Następnie przebuduj dane: `python3 build_data.py` i restart serwera.

---

## Licencja

MIT. Dane WCAG 2.2 pochodzą z W3C (https://www.w3.org/TR/WCAG22/) i podlegają licencji W3C Document License.

---

*WCAG 2.2 MCP Server — precyzyjna wiedza o dostępności cyfrowej dla Twoich asystentów AI.*
