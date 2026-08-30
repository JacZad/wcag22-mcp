# Dockerfile dla WCAG 2.2 MCP Server — Google Cloud Run
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUTF8=1

WORKDIR /app

# Zależności Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kod serwera + gotowe dane (pre-built, bez przebudowy w obrazie)
COPY server.py smoke_test.py ./
COPY wcag-data.json .
# Indeks FTS5 — bez niego search() spada do trybu awaryjnego
COPY embeddings/search.db ./embeddings/search.db

# Serwer niczego nie zapisuje: w Cloud Run logi idą na stderr.
RUN useradd --create-home --uid 10001 app && chown -R app:app /app
USER app

EXPOSE 8080

# Klucz API czytany jest z WCAG22_API_KEY bezpośrednio przez serwer.
CMD exec python3 server.py \
  --transport streamable-http \
  --host 0.0.0.0 \
  --port ${PORT:-8080}
