from pydantic_settings import BaseSettings  


class Settings(BaseSettings):
    # Telegram
    telegram_bot_token:    str
    telegram_webhook_secret: str = "change-me"  # verifies incoming webhook calls are really from Telegram

    # Backblaze B2 (S3-compatible — same fields as R2). Free tier: 10 GB storage, egress up to
    # 3x average monthly storage. Set a bucket Lifecycle Rule (B2 console) to auto-expire old
    # job outputs so a long-running POC doesn't quietly grow past the free 10 GB — see DEPLOY.md.
    r2_account_id:        str
    r2_access_key_id:     str
    r2_secret_access_key: str
    r2_bucket_name:       str = "creatorFlow"
    r2_endpoint_url:      str

    # Groq (hosted Whisper transcription + LLM analysis — no local GPU needed).
    # Free "Developer" tier as of writing: whisper-large-v3 = 2,000 requests/day, 7,200
    # audio-sec/hour; llama-3.3-70b-versatile = 30 req/min, 1,000 req/day, 12K tokens/min.
    # Each video uses ~2 Whisper calls + 3 LLM calls, so a one-friend POC stays far under both —
    # re-check Groq's console if you scale up or the daily job count grows past a few dozen.
    groq_api_key:      str
    groq_whisper_model:str = "whisper-large-v3"
    groq_llm_model:    str = "llama-3.3-70b-versatile"

    # Database (Postgres in production, e.g. Neon; sqlite is fine for local dev).
    # Neon free tier: 100 CU-hours/month, 0.5 GB storage, autosuspends after ~5 min idle —
    # comfortably covers a POC that only connects on a webhook call or the hourly batch run.
    database_url: str = "sqlite+aiosqlite:///./creatorflow.db"

    # FastAPI (ingest service)
    api_host:       str = "0.0.0.0"
    api_port:       int = 8000
    api_secret_key: str = "change-me"

    # Processing limits
    max_video_duration_seconds: int = 180
    min_video_duration_seconds: int = 30
    max_upload_size_mb:         int = 500

    # UX
    use_guided_workflow: bool = True   # False → legacy !upload / !process commands

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
