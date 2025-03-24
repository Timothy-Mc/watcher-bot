import discord
import random
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from utils.constants import WATCHED_USERS, summons_FILE
from utils.json_manager import load_json
from utils.time_utils import now_sydney

class Summoner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.recently_summoned = {}  # {user_id: datetime}
        self.auto_summon_enabled = True
        self.auto_summon_loop.start()

    def get_users_in_vc(self):
        present = set()
        for guild in self.bot.guilds:
            for vc in guild.voice_channels:
                for member in vc.members:
                    if not member.bot and member.id in WATCHED_USERS:
                        present.add(member.id)
        return present

    @tasks.loop(minutes=1)
    async def auto_summon_loop(self):
        if not self.auto_summon_enabled:
            return

        now = now_sydney()
        present = self.get_users_in_vc()
        missing = [uid for uid in WATCHED_USERS if uid not in present]

        if len(present) == 2 and len(missing) == 1:
            missing_user_id = missing[0]
            last_summon = self.recently_summoned.get(missing_user_id)

            if last_summon and now - last_summon < timedelta(hours=2):
                return  # Already summoned recently

            user = None
            for guild in self.bot.guilds:
                user = guild.get_member(missing_user_id)
                if user:
                    break

            if user and (not user.voice or not user.voice.channel):
                summon_lines = load_json(summons_FILE).get("summons_messages", [])
                message = random.choice(summon_lines) if summon_lines else "You are being summoned... 👻"

                try:
                    await user.send(message)
                    self.recently_summoned[missing_user_id] = now
                    print(f"[AutoSummon] Sent summon to {user.display_name}")
                except discord.Forbidden:
                    print(f"[AutoSummon] Failed to summon {user.display_name} (DMs closed)")

    @auto_summon_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

    # Allow admin to toggle it
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def autosummon(self, ctx, toggle: str = None):
        if toggle is None:
            state = "enabled" if self.auto_summon_enabled else "disabled"
            await ctx.send(f"Auto-summon is currently **{state}**.")
            return

        toggle = toggle.lower()
        if toggle == "enable":
            self.auto_summon_enabled = True
            await ctx.send("✅ Auto-summon has been **enabled**.")
        elif toggle == "disable":
            self.auto_summon_enabled = False
            await ctx.send("🚫 Auto-summon has been **disabled**.")
        else:
            await ctx.send("Usage: `~autosummon enable` or `~autosummon disable`.")

async def setup(bot):
    print("[SETUP] Registering Leaderboards cog")
    await bot.add_cog(Summoner(bot))