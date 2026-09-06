# Deploying CreatorFlow

CreatorFlow runs as two small pieces, both scale-to-zero — nothing costs anything, or runs at all,
between an incoming message and the next hourly batch:

1. **Ingest service** (`Dockerfile.ingest`) — a Cloud Run *service* that receives the Telegram
   webhook and the `/jobs/*` API. Always deployed, but scales to 0 instances when idle.
2. **Batch worker** (`Dockerfile.worker`) — a Cloud Run *Job* that does the actual
   transcribe → analyse → edit → render → thumbnail work. Triggered hourly by Cloud Scheduler,
   runs once, exits.

You'll also need:
- A **Neon** Postgres database (free tier): https://neon.tech → create a project → copy the
  connection string. Use the `asyncpg`-flavoured URL: `postgresql+asyncpg://user:pass@host/db`.
- A **Groq** API key: https://console.groq.com → API Keys.
- Your existing **Backblaze B2** credentials (unchanged).
- A **Telegram bot token** (from [@BotFather](https://t.me/BotFather)) and a webhook secret you
  make up yourself (any long random string).

## Free tier budget (this whole stack is a $0/month POC)

Checked against each provider's published free tier for a one-friend, hourly-batch usage pattern:

| Service | Free tier | This POC's usage | Fits? |
|---|---|---|---|
| Cloud Run (service + job) | 2M requests/mo, 180K vCPU-sec, 360K GiB-sec/mo | A handful of webhook calls + ~24 one-minute batch runs/mo | ✅ trivially |
| Cloud Scheduler | 3 jobs/mo free per billing account | 1 job (the hourly trigger) | ✅ |
| Cloud Build | 120 build-min/day, 2,500/mo | A couple of builds per redeploy | ✅ |
| Artifact Registry | 0.5 GB storage/project free, then $0.10/GB/mo | Two Python+ffmpeg images, likely >0.5 GB combined | ⚠️ a few cents/month — see cleanup policy below |
| Neon Postgres | 100 CU-hours/mo, 0.5 GB storage, autosuspends after ~5 min idle | Wakes only for a webhook call or the hourly batch | ✅ |
| Groq (Whisper) | 2,000 req/day, 7,200 audio-sec/hour | ~2 calls/video | ✅ |
| Groq (LLM) | 30 req/min, 1,000 req/day, 12K tokens/min | ~3 calls/video | ✅ |
| Backblaze B2 | 10 GB storage free, egress up to 3x avg. monthly storage | Outputs + thumbnails accumulate over time — see lifecycle rule below | ⚠️ fine short-term, needs cleanup for long-running use |

The only line item that isn't strictly $0 is Artifact Registry image storage (a couple of cents a
month at most) — everything else is free at this usage level. Cloud Run's free tier only applies
in specific US regions (e.g. `us-central1`, `us-east1`, `us-west1`) — pick one of those for
`YOUR_REGION` below, not a region outside the US. Note that GCP still requires a billing account
linked to the project to use Cloud Run/Scheduler at all, even though usage stays within the
Always Free tier — new accounts also get a separate one-time $300/90-day trial credit as a buffer.

Two things worth setting up so a POC left running for weeks doesn't quietly start costing money
or hit a wall:

**1. Auto-expire old Backblaze B2 files** (nothing currently deletes rendered outputs/thumbnails):
in the B2 web console → your bucket → *Lifecycle Rules* → add a rule on prefix `jobs/` with
"Keep only the last version, hide/delete after N days" (e.g. 7). No code change needed.

**2. Clean up old container image versions in Artifact Registry**, keeping only the latest:

```bash
gcloud artifacts repositories set-cleanup-policies gcr.io/YOUR_PROJECT_ID \
  --location=YOUR_REGION \
  --policy=- <<'EOF'
[
  {"id": "keep-latest-only", "action": {"type": "KEEP"}, "mostRecentVersions": {"keepCount": 1}}
]
EOF
```

## 1. One-time GCP setup

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com cloudscheduler.googleapis.com \
    secretmanager.googleapis.com artifactregistry.googleapis.com
```

Store secrets (repeat for each — never bake these into the image or commit them):

```bash
printf '%s' "your-value" | gcloud secrets create TELEGRAM_BOT_TOKEN --data-file=-
printf '%s' "your-value" | gcloud secrets create TELEGRAM_WEBHOOK_SECRET --data-file=-
printf '%s' "your-value" | gcloud secrets create GROQ_API_KEY --data-file=-
printf '%s' "your-value" | gcloud secrets create DATABASE_URL --data-file=-
printf '%s' "your-value" | gcloud secrets create R2_ACCOUNT_ID --data-file=-
printf '%s' "your-value" | gcloud secrets create R2_ACCESS_KEY_ID --data-file=-
printf '%s' "your-value" | gcloud secrets create R2_SECRET_ACCESS_KEY --data-file=-
```

## 2. Run the database migration once

From your machine, pointed at the real Neon `DATABASE_URL` (via `.env` or an exported env var):

```bash
alembic upgrade head
```

## 3. Build & deploy the ingest service

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/creatorflow-ingest -f Dockerfile.ingest .

gcloud run deploy creatorflow-ingest \
  --image gcr.io/YOUR_PROJECT_ID/creatorflow-ingest \
  --region YOUR_REGION \
  --min-instances=0 --max-instances=2 \
  --cpu=1 --memory=512Mi \
  --set-env-vars R2_BUCKET_NAME=creatorFlow,R2_ENDPOINT_URL=https://s3.us-east-005.backblazeb2.com \
  --set-secrets TELEGRAM_BOT_TOKEN=TELEGRAM_BOT_TOKEN:latest,TELEGRAM_WEBHOOK_SECRET=TELEGRAM_WEBHOOK_SECRET:latest,GROQ_API_KEY=GROQ_API_KEY:latest,DATABASE_URL=DATABASE_URL:latest,R2_ACCOUNT_ID=R2_ACCOUNT_ID:latest,R2_ACCESS_KEY_ID=R2_ACCESS_KEY_ID:latest,R2_SECRET_ACCESS_KEY=R2_SECRET_ACCESS_KEY:latest \
  --allow-unauthenticated
```

`--allow-unauthenticated` is required so Telegram's servers can reach the webhook — the endpoint
itself is protected by the `X-Telegram-Bot-Api-Secret-Token` check (see `api/routes/telegram.py`).

Note the deployed URL (`https://creatorflow-ingest-xxxx.a.run.app`).

## 4. Point Telegram's webhook at it

```bash
curl -F "url=https://creatorflow-ingest-xxxx.a.run.app/telegram/webhook" \
     -F "secret_token=YOUR_TELEGRAM_WEBHOOK_SECRET" \
     "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook"
```

## 5. Build & deploy the batch worker as a Cloud Run Job

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/creatorflow-worker -f Dockerfile.worker .

gcloud run jobs create creatorflow-batch \
  --image gcr.io/YOUR_PROJECT_ID/creatorflow-worker \
  --region YOUR_REGION \
  --max-retries=0 \
  --task-timeout=3600 \
  --cpu=1 --memory=1Gi \
  --set-env-vars R2_BUCKET_NAME=creatorFlow,R2_ENDPOINT_URL=https://s3.us-east-005.backblazeb2.com \
  --set-secrets TELEGRAM_BOT_TOKEN=TELEGRAM_BOT_TOKEN:latest,GROQ_API_KEY=GROQ_API_KEY:latest,DATABASE_URL=DATABASE_URL:latest,R2_ACCOUNT_ID=R2_ACCOUNT_ID:latest,R2_ACCESS_KEY_ID=R2_ACCESS_KEY_ID:latest,R2_SECRET_ACCESS_KEY=R2_SECRET_ACCESS_KEY:latest
```

## 6. Schedule it hourly

```bash
gcloud scheduler jobs create http creatorflow-batch-hourly \
  --location YOUR_REGION \
  --schedule "0 * * * *" \
  --uri "https://YOUR_REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/YOUR_PROJECT_ID/jobs/creatorflow-batch:run" \
  --http-method POST \
  --oauth-service-account-email YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com
```

## Testing without waiting an hour

```bash
gcloud run jobs execute creatorflow-batch --region YOUR_REGION
```

## Redeploying after code changes

Re-run the relevant `gcloud builds submit` + `gcloud run deploy` / `gcloud run jobs update`
command for whichever image changed.

## Alternative: Fly.io instead of GCP

If you'd rather avoid GCP's IAM/Secret Manager ceremony, the same two-piece shape works on
[Fly.io](https://fly.io): deploy `Dockerfile.ingest` as a normal Fly app (`fly launch`, it
auto-stops machines when idle), and run `Dockerfile.worker` via `fly machine run` on a
[Fly cron schedule](https://fly.io/docs/machines/flyctl/fly-machine-run/#schedule) instead of a
long-lived app. Secrets go through `fly secrets set`. Not built out here — ask if you want the
exact commands.
