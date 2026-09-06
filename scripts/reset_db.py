"""Dev utility: wipe and recreate the database. python scripts/reset_db.py"""
import asyncio
import sys
from pathlib import Path

from creatorflow.config import settings

DB_PATH = Path("creatorflow.db")


async def reset():
    is_sqlite = settings.database_url.startswith("sqlite")
    target = str(DB_PATH) if is_sqlite else settings.database_url

    print(f"⚠️  This will PERMANENTLY WIPE ALL DATA in: {target}")
    if not is_sqlite:
        print("⚠️  This does NOT look like a local sqlite file — double-check DATABASE_URL before continuing.")
    if input("Type 'reset' to continue: ").strip() != "reset":
        print("Aborted — nothing was changed.")
        sys.exit(1)

    from creatorflow.db.engine import engine, Base, init_db
    from creatorflow.db.models import job, user  # noqa: F401 — register tables on Base.metadata

    if is_sqlite:
        if DB_PATH.exists():
            DB_PATH.unlink()
            print(f"🗑️  Deleted {DB_PATH}")
    else:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        print("🗑️  Dropped all tables")

    await init_db()
    print("✅ Database recreated.")


asyncio.run(reset())
