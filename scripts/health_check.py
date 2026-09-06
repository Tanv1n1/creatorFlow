from __future__ import annotations

import asyncio
import importlib
import socket
import sys
from pathlib import Path

import boto3
from telegram import Bot

from creatorflow.config import settings

ROOT = Path(__file__).resolve().parents[1]

passed = 0
failed = 0

def ok(msg):
    global passed
    passed += 1
    print(f"✅ {msg}")

def fail(msg):
    global failed
    failed += 1
    print(f"❌ {msg}")

def header(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)

header("CONFIGURATION")

required = [
    "telegram_bot_token",
    "telegram_webhook_secret",
    "r2_account_id",
    "r2_access_key_id",
    "r2_secret_access_key",
    "r2_bucket_name",
    "r2_endpoint_url",
    "groq_api_key",
    "database_url",
]

for field in required:
    value = getattr(settings, field, None)
    if value:
        ok(field)
    else:
        fail(f"{field} missing")

header("PYTHON IMPORTS")

modules = [
    "fastapi",
    "sqlalchemy",
    "alembic",
    "telegram",
    "groq",
    "boto3",
    "cv2",
    "pydantic_settings",
]

for module in modules:
    try:
        importlib.import_module(module)
        ok(module)
    except Exception as e:
        fail(f"{module}: {e}")

header("TELEGRAM")

async def check_bot():
    try:
        bot = Bot(settings.telegram_bot_token)
        me = await bot.get_me()

        ok(f"Connected to @{me.username}")
    except Exception as e:
        fail(str(e))

asyncio.run(check_bot())

header("GROQ")

try:
    from groq import Groq

    client = Groq(api_key=settings.groq_api_key)
    models = [m.id for m in client.models.list().data]
    ok("Groq API reachable")

    if settings.groq_llm_model in models:
        ok(f"LLM model {settings.groq_llm_model} available")
    else:
        fail(f"LLM model {settings.groq_llm_model} not found on Groq")

    if settings.groq_whisper_model in models:
        ok(f"Whisper model {settings.groq_whisper_model} available")
    else:
        fail(f"Whisper model {settings.groq_whisper_model} not found on Groq")

except Exception as e:
    fail(str(e))

header("BACKBLAZE")

try:
    s3 = boto3.client(
        "s3",
        endpoint_url=settings.r2_endpoint_url,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
    )

    response = s3.list_objects_v2(
        Bucket=settings.r2_bucket_name,
        MaxKeys=1,
    )

    ok(f"Bucket '{settings.r2_bucket_name}' is accessible")

except Exception as e:
    fail(f"Backblaze B2 bucket '{settings.r2_bucket_name}' is not accessible: {e}")


header("DATABASE")

async def check_db():
    try:
        from sqlalchemy import text
        from creatorflow.db.engine import engine

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        kind = settings.database_url.split("://")[0]
        ok(f"Database reachable ({kind})")
    except Exception as e:
        fail(str(e))

asyncio.run(check_db())


header("ALEMBIC")

if (ROOT / "alembic").exists():
    ok("Alembic directory")
else:
    fail("Alembic missing")

if list((ROOT / "alembic" / "versions").glob("*.py")):
    ok("Alembic has at least one migration")
else:
    fail("No Alembic migrations found — run `alembic revision --autogenerate`")


header("PROJECT")

folders = [
    "src",
    "tests",
    "scripts",
]

for f in folders:
    if (ROOT / f).exists():
        ok(f)
    else:
        fail(f"{f} missing")


header("PERMISSIONS")

try:

    test = ROOT / ".health"

    test.write_text("ok")

    test.unlink()

    ok("Write permission")

except Exception as e:
    fail(str(e))

header("NETWORK")

try:

    socket.create_connection(("google.com", 80), timeout=5)

    ok("Internet")

except Exception:

    fail("No internet")


print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)

print(f"Passed : {passed}")
print(f"Failed : {failed}")

if failed == 0:
    print("\n*** CreatorFlow is READY. ***")
    sys.exit(0)

print("\n*** CreatorFlow has configuration issues. ***")
sys.exit(1)
