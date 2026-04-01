# Google Cloud Run Deployment Guide

## Prerequisites
1. Google Cloud account (free tier available at https://cloud.google.com/free)
2. GitHub repository with this project
3. Google Cloud CLI installed locally
4. Valid API keys for OpenAI and Gemini

---

## Step 1: Set Up Google Cloud Project (5 min)

1. Go to https://console.cloud.google.com
2. Click **"Create Project"** at the top
3. Name it: `ai-support-agent` (or your choice)
4. Click **Create**
5. Wait for it to activate, then select the project

---

## Step 2: Enable Required APIs (3 min)

1. Search for **"Cloud Run"** in the search bar
2. Click the result and **Enable** the API
3. Search for **"Cloud Build"** and **Enable** it

---

## Step 3: Set Up Authentication (Optional but Recommended)

For automatic deployments from GitHub:

1. Go to **Cloud Build** in the console
2. Click **Settings**
3. Connect your GitHub repository
4. Authorize Google Cloud to access your GitHub account
5. Select this repository

---

## Step 4: Deploy from Command Line (Easiest)

### Option A: Using `gcloud` CLI

```bash
# 1. Install gcloud CLI if not already done
# Visit: https://cloud.google.com/sdk/docs/install

# 2. Authenticate
gcloud auth login

# 3. Set your project
gcloud config set project YOUR_PROJECT_ID

# 4. Navigate to project folder
cd D:\my_projects\ai-support-agent

# 5. Deploy
gcloud run deploy ai-support-agent `
  --source . `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --set-env-vars OPENAI_API_KEY=your_key_here,GEMINI_API_KEY=your_key_here
```

**Replace `your_key_here` with actual keys!**

### Option B: Via Google Cloud Console (No CLI Needed)

1. Go to **Cloud Run**
2. Click **Create Service**
3. Click **Deploy one revision from an image source** → **Container Registry**
4. Click **Set up with Cloud Build** (this will build from your repo)
5. Follow the wizard and select this repository
6. Under **Environment variables**, add:
   ```
   OPENAI_API_KEY = your_key_here
   GEMINI_API_KEY = your_key_here
   ```
7. Click **Deploy**

---

## Step 5: Configure Environment Variables Securely

### Option 1: Via Console UI (Simple)
1. Go to Cloud Run → Select your service
2. Click **Edit & Deploy New Revision**
3. Expand **Runtime Settings**
4. Add environment variables for API keys
5. Click **Deploy**

### Option 2: Via Secret Manager (More Secure)
```bash
# Store API keys in Google Secret Manager
gcloud secrets create openai-api-key --data-file=-
# Then paste your OpenAI key and press Ctrl+D

gcloud secrets create gemini-api-key --data-file=-
# Then paste your Gemini key and press Ctrl+D

# Grant Cloud Run service access
gcloud run services add-iam-policy-binding ai-support-agent \
  --member=serviceAccount:PROJECT_ID@appspot.gserviceaccount.com \
  --role=roles/iam.securityAdmin
```

---

## Step 6: Get Your Public URL

After deployment:
1. Go to **Cloud Run** in console
2. Click your service name
3. Copy the **Service URL** at the top
4. This is your live API endpoint!

**Example:** `https://ai-support-agent-xxxxx.a.run.app`

---

## Step 7: Test Your Deployment

```powershell
# Health check
Invoke-RestMethod -Uri "https://YOUR_SERVICE_URL/" | ConvertTo-Json

# Chat test
$body = @{ session_id = 'test-1'; message = 'Where is my order ORD123?' } | ConvertTo-Json
Invoke-RestMethod -Method Post `
  -Uri "https://YOUR_SERVICE_URL/chat" `
  -ContentType 'application/json' `
  -Body $body | ConvertTo-Json -Compress
```

Replace `YOUR_SERVICE_URL` with the actual URL from Step 6.

---

## Step 8: Set Up Auto-Deployment (Optional)

Enable automatic redeployment when you push to GitHub:

```bash
gcloud builds submit \
  --gcs-log-dir=gs://YOUR_BUCKET_NAME/builds \
  --substitutions _SERVICE_NAME="ai-support-agent",_REGION="us-central1"
```

Or use Cloud Build trigger:
1. Go to **Cloud Build** → **Triggers**
2. Click **Create Trigger**
3. Select your GitHub repo
4. Set build configuration to `Dockerfile`
5. Click **Create**

Now every push to main branch auto-deploys!

---

## Pricing (Google Cloud Run Free Tier)

- **Free monthly:** 2 million requests
- **Free memory:** 512 MB per request
- **Free CPU:** 2 CPU-seconds per request
- **Free uptime:** Always free tier enabled by default

Cost only applies if you exceed free tier. Estimate: ~$0.40 per million requests.

---

## Monitoring & Logs

```bash
# View live logs
gcloud run logs read ai-support-agent --limit 50 --follow

# View specific time range
gcloud run logs read ai-support-agent --since "2 hours ago"
```

Or via console:
1. Go to Cloud Run → Your service
2. Click **Logs** tab
3. View real-time request logs

---

## Troubleshooting

### **Service won't start**
- Check logs: `gcloud run logs read ai-support-agent`
- Ensure port 8000 is exposed
- Verify all dependencies installed correctly

### **API calls failing**
- Check environment variables are set correctly
- Verify API keys are valid and have quota
- Check Cloud Run logs for specific errors

### **High latency**
- Scale up instances: Go to Cloud Run service → **Edit & Deploy**
- Increase **Memory** (512 MB → 1 GB)
- Increase **Timeout** (300s default)

---

## Next Steps

1. **Add custom domain:** Cloud Run → Service → **Managed CORS** setup
2. **Set up CI/CD pipeline:** Auto-deploy on every GitHub push
3. **Enable authentication:** Restrict API access to authorized users only
4. **Add monitoring:** Set up alerts for errors and high latency

---

## Quick Deploy Command (Copy-Paste)

```bash
gcloud run deploy ai-support-agent --source . --platform managed --region us-central1 --allow-unauthenticated --set-env-vars OPENAI_API_KEY=sk-xxx,GEMINI_API_KEY=AIza-xxx
```

Replace API keys with real ones!

---

Questions? Check official docs: https://cloud.google.com/run/docs
