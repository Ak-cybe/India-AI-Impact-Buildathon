#!/bin/bash
# ========================================
# Agentic Honeypot API - Deployment Script
# Deploy to Google Cloud Run
# ========================================

set -e  # Exit on error

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="honeypot-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Deploying Agentic Honeypot API to Google Cloud Run"
echo "   Project: ${PROJECT_ID}"
echo "   Region: ${REGION}"
echo "   Service: ${SERVICE_NAME}"

# 1. Build Docker image
echo "📦 Building Docker image..."
docker build -t ${IMAGE_NAME}:latest .

# 2. Push to Container Registry
echo "⬆️  Pushing to Container Registry..."
docker push ${IMAGE_NAME}:latest

# 3. Deploy to Cloud Run
echo "🌐 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME}:latest \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --set-env-vars "ENVIRONMENT=production" \
    --set-env-vars "LOG_LEVEL=INFO" \
    --set-secrets "GOOGLE_API_KEY=google-api-key:latest" \
    --set-secrets "API_KEY=honeypot-api-key:latest" \
    --memory 2Gi \
    --cpu 2 \
    --min-instances 1 \
    --max-instances 10 \
    --concurrency 80 \
    --timeout 300

# 4. Get service URL
echo "🔗 Getting service URL..."
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo ""
echo "✅ Deployment successful!"
echo "🌐 Service URL: ${SERVICE_URL}"
echo ""
echo "📋 Next steps:"
echo "   1. Set up secrets in GCP Secret Manager:"
echo "      gcloud secrets create google-api-key --data-file=-"
echo "      gcloud secrets create honeypot-api-key --data-file=-"
echo ""
echo "   2. Test the API:"
echo "      curl ${SERVICE_URL}/health"
echo ""
echo "   3. Submit to hackathon:"
echo "      URL: ${SERVICE_URL}"
echo "      Endpoint: ${SERVICE_URL}/api/analyze"
