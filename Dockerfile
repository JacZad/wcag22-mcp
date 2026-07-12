FROM python:3.12-slim

WORKDIR /app

# Kopiujemy i instalujemy zależności
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiujemy serwer i dane
COPY server.py .
COPY wcag-data.json .

# Cloud Run ustawia PORT=8080
ENV PORT=8080

EXPOSE 8080

CMD ["sh", "-c", "python3 server.py --transport streamable-http --port ${PORT} --host 0.0.0.0"]
