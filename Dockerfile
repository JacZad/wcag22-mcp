# Dockerfile dla WCAG 2.2 MCP Server — Google Cloud Run (fast build)
FROM python:3.12-slim

WORKDIR /app

# Zależności Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kod serwera + gotowe dane (pre-built)
COPY server.py .
COPY wcag-data.json .

# Bez przebudowy — dane już wygenerowane lokalnie

ENV PYTHONUNBUFFERED=1
EXPOSE 8080

CMD exec python3 server.py \
  --transport streamable-http \
  --host 0.0.0.0 \
  --port ${PORT:-8080} \
  ${WCAG22_API_KEY:+--api-key "$WCAG22_API_KEY"}
