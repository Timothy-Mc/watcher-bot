import aiosqlite
import os
from datetime import datetime
import pytz

DB_PATH = "data/watcherbot.db"

async def init_db():
    if not os.path.exists(DB_PATH):
        print("[DB] Creating database...")

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_points (
                user_id TEXT PRIMARY KEY,
                points INTEGER DEFAULT 0,
                vc_minutes INTEGER DEFAULT 0
            );
        """)
        await db.commit()
        print("[DB] Tables initialized.")

async def get_user(user_id: int) -> tuple[int, int]:
    user_id = str(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT points, vc_minutes FROM user_points WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row if row else (0, 0)

async def update_user(user_id: int, points_delta: int = 0, minutes_delta: int = 0):
    user_id = str(user_id)
    current_points, current_minutes = await get_user(user_id)
    new_points = current_points + points_delta
    new_minutes = current_minutes + minutes_delta

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO user_points (user_id, points, vc_minutes)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                points = excluded.points,
                vc_minutes = excluded.vc_minutes;
        """, (user_id, new_points, new_minutes))
        await db.commit()


async def init_loser_tables():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS monthly_losers (
                user_id TEXT PRIMARY KEY,
                count INTEGER DEFAULT 0
            );
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS lifetime_losers (
                user_id TEXT PRIMARY KEY,
                count INTEGER DEFAULT 0
            );
        """)
        await db.commit()

async def add_vc_time_and_points(user_id: int, minutes: float):
    await update_user(user_id, points_delta=int(minutes), minutes_delta=int(minutes))

async def increment_loser(user_id: int):
    user_id = str(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO monthly_losers (user_id, count)
            VALUES (?, 1)
            ON CONFLICT(user_id) DO UPDATE SET count = count + 1;
        """, (user_id,))
        await db.execute("""
            INSERT INTO lifetime_losers (user_id, count)
            VALUES (?, 1)
            ON CONFLICT(user_id) DO UPDATE SET count = count + 1;
        """, (user_id,))
        await db.commit()

async def get_top_vc_minutes(limit=10):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id, vc_minutes FROM user_points ORDER BY vc_minutes DESC LIMIT ?",
            (limit,)
        ) as cursor:
            return await cursor.fetchall()

async def get_top_points(limit=10):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id, points FROM user_points ORDER BY points DESC LIMIT ?",
            (limit,)
        ) as cursor:
            return await cursor.fetchall()

async def get_monthly_losers(limit=10):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id, count FROM monthly_losers ORDER BY count DESC LIMIT ?",
            (limit,)
        ) as cursor:
            return await cursor.fetchall()

async def get_lifetime_losers(limit=10):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id, count FROM lifetime_losers ORDER BY count DESC LIMIT ?",
            (limit,)
        ) as cursor:
            return await cursor.fetchall()
        
async def init_meta_table():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        """)
        await db.commit()

async def maybe_reset_monthly_losers():
    now = datetime.now(pytz.timezone("Australia/Sydney"))
    current_month = now.strftime("%Y-%m")

    async with aiosqlite.connect(DB_PATH) as db:
        # Get last reset month
        async with db.execute("SELECT value FROM meta WHERE key = 'last_monthly_reset'") as cursor:
            row = await cursor.fetchone()
            last_reset = row[0] if row else None

        # If new month, reset
        if current_month != last_reset:
            print(f"[DB] Resetting monthly losers for {current_month}")
            await db.execute("DELETE FROM monthly_losers;")
            await db.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", ("last_monthly_reset", current_month))
            await db.commit()

async def get_points(user_id: int) -> int:
    user_id = str(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT points FROM user_points WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def adjust_points(user_id: int, delta: int):
    user_id = str(user_id)
    current = await get_points(user_id)
    new_total = max(current + delta, 0)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO user_points (user_id, points, vc_minutes)
            VALUES (?, ?, 0)
            ON CONFLICT(user_id) DO UPDATE SET points = ?;
        """, (user_id, new_total, new_total))
        await db.commit()