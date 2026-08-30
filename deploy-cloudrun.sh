#!/bin/bash
# deploy-cloudrun.sh
# Wdraża WCAG MCP na Google Cloud Run.
# Wymaga: gcloud CLI, projekt GCP z włączonym Cloud Run + Artifact Registry
#
# Użycie:
#   1. gcloud auth login
#   2. gcloud config set project NAZWA_PROJEKTU
#   3. ./deploy-cloudrun.sh
#
# Albo jednym poleceniem (buduje obraz w chmurze):
#   gcloud run deploy wcag22-mcp --source . --region europe-central2 \
#     --allow-unauthenticated --memory=512Mi --timeout=600 \
#     --min-instances=0 --max-instances=3 --concurrency=80
#
# Pełny pipeline z testem dymnym przed wdrożeniem: cloudbuild.yaml

set -e

PROJECT_ID="${1:-$(gcloud config get project)}"
REGION="${2:-europe-central2}"
SERVICE_NAME="${3:-wcag22-mcp}"

echo "=== Wdrażanie WCAG MCP na Cloud Run ==="
echo "Projekt:  $PROJECT_ID"
echo "Region:   $REGION"
echo "Usługa:   $SERVICE_NAME"
echo ""

# Sprawdź czy gcloud jest zalogowany
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &>/dev/null; then
    echo "❌ Zaloguj się przez: gcloud auth login"
    exit 1
fi

# Sprawdź czy Cloud Run API jest włączone
if ! gcloud services list --enabled --filter="name:run.googleapis.com" --format="value(name)" | grep -q run; then
    echo "Włączam Cloud Run API..."
    gcloud services enable run.googleapis.com
fi

# Deploy z źródła (Cloud Build buduje obraz automatycznie)
echo "=== Deploy z źródła (Cloud Build w tle) ==="
gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --region="$REGION" \
    --allow-unauthenticated \
    --memory=512Mi \
    --cpu=1 \
    --cpu-boost \
    --timeout=600 \
    --min-instances=0 \
    --max-instances=3 \
    --concurrency=80 \
    --port=8080

echo ""
echo "✅ WCAG MCP wdrożony!"
echo "URL: $(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')"
echo ""
echo "Następnie dodaj CNAME w DNS (NS1):"
echo "  mcp IN CNAME <url>.run.app"
