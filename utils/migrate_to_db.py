import json
import asyncio
import aiosqlite
import os

# DB_PATH = os.path.join("data", "watcherbot.db") 
DB_PATH = "data/watcherbot.db"
DATA_DIR = "data" # adjust if needed
 # adjust if needed

async def migrate():
    async with aiosqlite.connect(DB_PATH) as db:
        # Load files
        with open(os.path.join(DATA_DIR, "vc_stats.json"), "r") as f:
            vc_stats = json.load(f)

        with open(os.path.join(DATA_DIR, "points.JSON"), "r") as f:
            points = json.load(f)

        with open(os.path.join(DATA_DIR, "loserboard.json"), "r") as f:
            loserboard = json.load(f).get("loserboard", {})

        with open(os.path.join(DATA_DIR, "hallofshame.json"), "r") as f:
            hallofshame = json.load(f).get("hallofshame", {})

        # Migrate to user_points table
        for user_id in set(vc_stats) | set(points):
            vc_minutes = int(round(vc_stats.get(user_id, 0)))
            user_points = int(points.get(user_id, 0))
            await db.execute("""
                INSERT INTO user_points (user_id, points, vc_minutes)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    points = excluded.points,
                    vc_minutes = excluded.vc_minutes;
            """, (user_id, user_points, vc_minutes))

        # Migrate monthly_losers
        for user_id, count in loserboard.items():
            await db.execute("""
                INSERT INTO monthly_losers (user_id, count)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET count = excluded.count;
            """, (user_id, count))

        # Migrate lifetime_losers
        for user_id, count in hallofshame.items():
            await db.execute("""
                INSERT INTO lifetime_losers (user_id, count)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET count = excluded.count;
            """, (user_id, count))

        await db.commit()
        print("✅ Migration completed!")

asyncio.run(migrate())
