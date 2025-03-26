import os
import shutil
from discord.ext import commands, tasks
from utils.time_utils import now_sydney

class BackupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.backup_sqlite_db.start()

    @tasks.loop(hours=24)
    async def backup_sqlite_db(self):
        now = now_sydney()
        timestamp = now.strftime("%Y-%m-%d_%H-%M")

        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)

        db_file = "data/watcherbot.db"
        if not os.path.exists(db_file):
            print("[BACKUP] Database file not found, skipping.")
            return

        backup_name = f"{timestamp}_{db_file}"
        backup_path = os.path.join(backup_dir, backup_name)

        shutil.copy(db_file, backup_path)
        self.prune_old_backups(backup_dir, db_file, keep=1)

        print(f"[BACKUP] SQLite DB backed up at {timestamp}")

    def prune_old_backups(self, backup_dir, filename, keep=1):
        matching = [f for f in os.listdir(backup_dir) if f.endswith(filename)]
        matching.sort()  # Oldest first

        if len(matching) > keep:
            to_delete = matching[:-keep]
            for file in to_delete:
                try:
                    os.remove(os.path.join(backup_dir, file))
                    print(f"[CLEANUP] Deleted old backup: {file}")
                except Exception as e:
                    print(f"[ERROR] Could not delete {file}: {e}")

    @backup_sqlite_db.before_loop
    async def before_backup_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    print("[SETUP] Registering Backup cog")
    await bot.add_cog(BackupCog(bot))
