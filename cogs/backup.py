import os
import shutil
from discord.ext import commands, tasks
from datetime import datetime
from utils.constants import (
    vc_stats_FILE, points_FILE, loserboard_FILE, hallofshame_FILE,
    bets_FILE, roasts_FILE, summons_FILE
)
from utils.time_utils import now_sydney

class BackupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.backup_json_files.start()

    @tasks.loop(hours=24)
    async def backup_json_files(self):
        now = now_sydney()
        timestamp = now.strftime("%Y-%m-%d_%H-%M")

        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)

        files_to_backup = [
            vc_stats_FILE,
            points_FILE,
            loserboard_FILE,
            hallofshame_FILE,
            bets_FILE,
            roasts_FILE,
            summons_FILE,
        ]

        for file_path in files_to_backup:
            if not os.path.exists(file_path):
                continue

            filename = os.path.basename(file_path)
            backup_name = f"{timestamp}_{filename}"
            backup_path = os.path.join(backup_dir, backup_name)

            # Copy current file to backup
            shutil.copy(file_path, backup_path)

            # Clean older backups of the same file
            self.prune_old_backups(backup_dir, filename, keep=2)

        print(f"[BACKUP] JSON files backed up at {timestamp}")

    def prune_old_backups(self, backup_dir, filename, keep=2):
        """Deletes old backups of the same filename, keeping only the most recent `keep`."""
        matching = [f for f in os.listdir(backup_dir) if f.endswith(filename)]
        matching.sort()  # Oldest first due to timestamp

        if len(matching) > keep:
            to_delete = matching[:-keep]
            for file in to_delete:
                try:
                    os.remove(os.path.join(backup_dir, file))
                    print(f"[CLEANUP] Deleted old backup: {file}")
                except Exception as e:
                    print(f"[ERROR] Could not delete {file}: {e}")

    @backup_json_files.before_loop
    async def before_backup_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    print("[SETUP] Registering Leaderboards cog")
    await bot.add_cog(BackupCog(bot))
