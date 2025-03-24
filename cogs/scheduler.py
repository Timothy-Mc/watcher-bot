import discord
import asyncio
from discord.ext import commands, tasks
from datetime import datetime, time, timedelta
from utils.constants import SYDNEY_TZ
from utils.time_utils import now_sydney

class Scheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vc_tracking = None
        self.time_check_loop.start()

    def get_all_vc_ids(self):
        return [vc.id for g in self.bot.guilds for vc in g.voice_channels]

    @tasks.loop(minutes=1)
    async def time_check_loop(self):
        now = now_sydney()

        # Between 10 PM and 10 AM
        start = now.replace(hour=22, minute=0, second=0, microsecond=0)
        end = now.replace(hour=10, minute=0, second=0, microsecond=0)

        # If it's before 10AM, then "end" is today. Otherwise "end" is next day.
        if now.hour < 10:
            end = end
        else:
            end += timedelta(days=1)

        tracking = start <= now < end

        if not self.vc_tracking:
            self.vc_tracking = self.bot.get_cog("VCTracking")

        if self.vc_tracking:
            for vc_id in self.get_all_vc_ids():
                self.vc_tracking.tracking_active[vc_id] = tracking

    @time_check_loop.before_loop
    async def before_loop(self):
        print("Waiting for bot to be ready before starting time_check_loop...")
        await self.bot.wait_until_ready()

async def setup(bot):
    print("[SETUP] Registering Leaderboards cog")
    await bot.add_cog(Scheduler(bot))