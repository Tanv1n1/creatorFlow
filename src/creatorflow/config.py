from pydantic_settings import BaseSettings  


class Settings(BaseSettings):
    # Telegram
    telegram_bot_token: str

    # Backblaze B2 (S3-compatible — same fields as R2)
    r2_account_id:        str
    r2_access_key_id:     str
    r2_secret_access_key: str
    r2_bucket_name:       str = "creatorFlow"
    r2_endpoint_url:      str

    # Ollama (local LLM)
    ollama_host:  str = "http://localhost:11434"
    ollama_model: str = "gemma3:12b"

    # Whisper
    whisper_model:        str = "large-v3"
    whisper_device:       str = "cuda"
    whisper_compute_type: str = "float16"

    # FastAPI
    api_host:       str = "0.0.0.0"
    api_port:       int = 8000
    api_secret_key: str = "change-me"

    # Processing limits
    max_video_duration_seconds: int = 180
    min_video_duration_seconds: int = 30
    max_upload_size_mb:         int = 500

    # UX
    use_guided_workflow:      bool = True   # False → legacy !upload / !process commands
    progress_update_interval: int  = 10     # seconds between progress message edits

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
