"""Quick pre-flight check: python scripts/check_env.py — for a full diagnostic (Telegram/Groq/B2/DB
reachability) use scripts/health_check.py instead."""
import sys
import os
from pathlib import Path

REQUIRED = [
    "TELEGRAM_BOT_TOKEN", "TELEGRAM_WEBHOOK_SECRET",
    "R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY",
    "R2_BUCKET_NAME", "R2_ENDPOINT_URL",
    "GROQ_API_KEY",
]

env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

missing = [k for k in REQUIRED if not os.environ.get(k)]
if missing:
    print("❌ Missing required environment variables:")
    for k in missing:
        print(f"   {k}")
    print("\nCopy .env.example to .env and fill in the values.")
    sys.exit(1)

print("✅ All required environment variables are set.")
