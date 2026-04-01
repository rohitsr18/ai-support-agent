# Cloud Run Deployment

## Prerequisites

1. Google Cloud project
2. gcloud CLI installed
3. OpenAI and Gemini API keys

## Enable Required Services

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com
```

## Deploy

From the repository root:

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

gcloud run deploy pragna \
  --source . \
  --region us-west1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=YOUR_OPENAI_KEY,GEMINI_API_KEY=YOUR_GEMINI_KEY
```

## Verify

```powershell
# Health
Invoke-RestMethod -Uri "https://YOUR_SERVICE_URL/"

# Chat
$body = @{ session_id = 'test-1'; message = 'Where is my order ORD123?' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "https://YOUR_SERVICE_URL/chat" -ContentType 'application/json' -Body $body
```

## Logs

```bash
gcloud run logs read pragna --limit 50
```

## Common Issues

- Service fails to start:
  - Check logs with `gcloud run logs read pragna`
  - Verify env vars are set
- Chat endpoint errors:
  - Confirm API keys are valid
  - Confirm quotas are available
