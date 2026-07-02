from __future__ import annotations

import asyncio
import importlib
import os
import socket
import sqlite3
import sys
from pathlib import Path

import boto3
import httpx
from telegram import Bot
from faster_whisper import WhisperModel

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
    "r2_account_id",
    "r2_access_key_id",
    "r2_secret_access_key",
    "r2_bucket_name",
    "r2_endpoint_url",
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
    "ollama",
    "boto3",
    "faster_whisper",
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

header("OLLAMA")

try:
    r = httpx.get(f"{settings.ollama_host}/api/tags", timeout=5)

    if r.status_code == 200:
        ok("Ollama server reachable")

        models = [m["name"] for m in r.json()["models"]]

        if settings.ollama_model in models:
            ok(f"Model {settings.ollama_model} installed")
        else:
            fail(f"{settings.ollama_model} not installed")

    else:
        fail("Ollama server not responding")

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

header("WHISPER")

try:

    WhisperModel(
        settings.whisper_model,
        device=settings.whisper_device,
        compute_type=settings.whisper_compute_type,
    )

    ok("Whisper model loaded")

except Exception as e:
    fail(str(e))


header("DATABASE")

try:

    db = ROOT / "creatorflow.db"

    if db.exists():
        sqlite3.connect(db).close()
        ok("SQLite database")
    else:
        fail("Database file missing")

except Exception as e:
    fail(str(e))


header("ALEMBIC")

if (ROOT / "alembic").exists():
    ok("Alembic directory")
else:
    fail("Alembic missing")


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