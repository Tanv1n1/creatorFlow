"""Dev utility: wipe and recreate the database. python scripts/reset_db.py"""
import asyncio
from pathlib import Path

DB_PATH = Path("creatorflow.db")


async def reset():
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"🗑️  Deleted {DB_PATH}")
    from creatorflow.db.engine import init_db
    await init_db()
    print("✅ Database recreated.")


asyncio.run(reset())
