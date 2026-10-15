#!/usr/bin/env python3
"""
test_api_keys.py — Sprawdza obsługę wielu kluczy API (WCAG22_API_KEYS).

Pokrywa parsowanie listy "etykieta:klucz", dopasowanie klucza oraz
APIKeyMiddleware: 401 dla złego/pustego klucza, przepuszczenie dobrego
i zapisanie etykiety klienta w scope["wcag_client"].

Użycie:
  python3 test_api_keys.py

Kod wyjścia 0, gdy wszystko działa; 1 przy pierwszej awarii.
"""

import asyncio
import importlib.util
import sys
from pathlib import Path

SERVER = Path(__file__).parent / "server.py"


def load_server():
    spec = importlib.util.spec_from_file_location("wcag22_server", SERVER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def call(srv, keys, headers):
    """Wywołaj middleware z podanymi nagłówkami; zwróć (status, scope aplikacji)."""
    seen = {}

    async def inner(scope, receive, send):
        seen.update(scope)
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    sent = []

    async def send(msg):
        sent.append(msg)

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    scope = {"type": "http", "headers": headers}
    asyncio.run(srv.APIKeyMiddleware(inner, keys)(scope, receive, send))
    return sent[0]["status"], seen


def main():
    srv = load_server()
    parse, match = srv.parse_api_keys, srv.match_api_key

    # parse_api_keys
    assert parse() == {}
    assert parse("a") == {"a": "default"}
    assert parse("", "jacek:k1, zespol-a:k2 ,") == {"k1": "jacek", "k2": "zespol-a"}
    assert parse("a", "jacek:k1") == {"a": "default", "k1": "jacek"}
    # klucz może zawierać dwukropek (dzielimy tylko po pierwszym)
    assert parse("", "x:a:b") == {"a:b": "x"}
    for bad in ("bez-dwukropka", ":k", "x:", "a:k1,b:k1"):
        try:
            parse("", bad)
        except ValueError:
            continue
        raise AssertionError(f"oczekiwano ValueError dla {bad!r}")
    try:
        parse("k1", "x:k1")
    except ValueError:
        pass
    else:
        raise AssertionError("klucz z --api-key powtórzony w WCAG22_API_KEYS")

    # match_api_key
    keys = parse("", "jacek:k1,zespol-a:k2")
    assert match("k1", keys) == "jacek"
    assert match("k2", keys) == "zespol-a"
    assert match("k3", keys) is None
    assert match("", keys) is None
    assert match("zażółć", keys) is None  # nie-ASCII nie wywala porównania

    # APIKeyMiddleware
    status, scope = call(srv, keys, [(b"x-api-key", b"k2")])
    assert status == 200 and scope["wcag_client"] == "zespol-a", (status, scope)
    for hdrs in ([(b"x-api-key", b"zly")], [(b"x-api-key", b"")], []):
        status, scope = call(srv, keys, hdrs)
        assert status == 401 and "wcag_client" not in scope, (hdrs, status)
    # brak kluczy = brak zabezpieczenia
    status, scope = call(srv, {}, [])
    assert status == 200 and "wcag_client" not in scope
    # zgodność wsteczna: pojedynczy klucz jako string
    status, scope = call(srv, "stary", [(b"x-api-key", b"stary")])
    assert status == 200 and scope["wcag_client"] == "default"

    print("✅ test_api_keys: wszystko działa")
    return 0


if __name__ == "__main__":
    sys.exit(main())
