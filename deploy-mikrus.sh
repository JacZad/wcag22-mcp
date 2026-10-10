#!/bin/bash
# deploy-mikrus.sh
# Wdraża WCAG MCP na Mikrusa (2.1+) jako kontener Dockera.
# Wymaga: ssh do mikrusa (najlepiej z kluczem), Docker na serwerze.
#
# Użycie (z Git Bash, w katalogu repo):
#   MIKRUS_HOST=srv12.mikr.us MIKRUS_SSH_PORT=10123 MIKRUS_APP_PORT=20123 ./deploy-mikrus.sh
#
# Wysyła stan z HEAD (git archive) — niezacommitowane zmiany NIE trafiają
# na serwer. Klucz API leży na serwerze w ~/wcag22-mcp/.env i nie jest
# nadpisywany przy kolejnych wdrożeniach.
#
# HTTPS: w panelu mikr.us → „Subdomeny" przypnij np. wcag.bieda.it
# do portu MIKRUS_APP_PORT. Ruch idzie przez Cloudflare po IPv6.

set -e

HOST="${MIKRUS_HOST:?Ustaw MIKRUS_HOST, np. srv12.mikr.us}"
SSH_PORT="${MIKRUS_SSH_PORT:?Ustaw MIKRUS_SSH_PORT (port SSH z maila powitalnego)}"
APP_PORT="${MIKRUS_APP_PORT:?Ustaw MIKRUS_APP_PORT (jeden z portów przydzielonych w panelu)}"
SSH_USER="${MIKRUS_USER:-root}"
REMOTE_DIR="wcag22-mcp"
IMAGE="wcag22-mcp"

SSH="ssh -p $SSH_PORT $SSH_USER@$HOST"

echo "=== Wdrażanie WCAG MCP na Mikrusa ==="
echo "Serwer:   $SSH_USER@$HOST:$SSH_PORT"
echo "Port app: $APP_PORT"
echo "Commit:   $(git rev-parse --short HEAD)"
echo ""

if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    echo "⚠️  Masz niezacommitowane zmiany — wdrażam tylko HEAD."
fi

echo "=== Wysyłanie kodu ==="
$SSH "mkdir -p ~/$REMOTE_DIR/src ~/$REMOTE_DIR/logs && rm -rf ~/$REMOTE_DIR/src/*"
git archive --format=tar HEAD | $SSH "tar -x -C ~/$REMOTE_DIR/src"

echo "=== Budowanie i restart kontenera ==="
$SSH bash -s -- "$REMOTE_DIR" "$IMAGE" "$APP_PORT" <<'REMOTE'
set -e
DIR="$HOME/$1"; IMAGE="$2"; PORT="$3"

if ! command -v docker >/dev/null; then
    echo "❌ Brak Dockera na serwerze. Zainstaluj: curl -fsSL https://get.docker.com | sh"
    exit 1
fi

if [ ! -f "$DIR/.env" ]; then
    echo "WCAG22_API_KEY=$(head -c 24 /dev/urandom | base64 | tr -d '/+=')" > "$DIR/.env"
    chmod 600 "$DIR/.env"
    echo "🔑 Wygenerowano klucz API w $DIR/.env"
fi

# Kontener działa jako uid 10001 — musi móc pisać log.
chown -R 10001:10001 "$DIR/logs"

docker build -t "$IMAGE" "$DIR/src"
docker rm -f "$IMAGE" 2>/dev/null || true
docker run -d \
    --name "$IMAGE" \
    --restart unless-stopped \
    --env-file "$DIR/.env" \
    -p "$PORT:8080" \
    --memory 300m \
    -v "$DIR/logs:/home/app/.hermes/logs" \
    --log-opt max-size=5m --log-opt max-file=2 \
    "$IMAGE"
docker image prune -f >/dev/null

sleep 3
if docker ps --filter "name=^$IMAGE$" --filter status=running -q | grep -q .; then
    echo "✅ Kontener działa."
    docker stats --no-stream --format "RAM: {{.MemUsage}}" "$IMAGE"
else
    echo "❌ Kontener nie wstał:"
    docker logs --tail 30 "$IMAGE"
    exit 1
fi
REMOTE

echo ""
echo "Klucz API: $SSH cat ~/$REMOTE_DIR/.env"
echo "Logi:      $SSH tail -f ~/$REMOTE_DIR/logs/wcag22-mcp.log"
echo "Endpoint:  https://<twoja-subdomena>/mcp  (nagłówek X-API-Key)"
