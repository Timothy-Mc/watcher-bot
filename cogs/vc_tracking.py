import discord
import random
import asyncio
from discord.ext import commands
from datetime import datetime
from utils.constants import (
    vc_stats_FILE, points_FILE,
    loserboard_FILE, hallofshame_FILE, roasts_FILE
)
from utils.sqlite_manager import add_vc_time_and_points, increment_loser
from utils.json_manager import load_json, save_json, get_log_channel_id
from utils.time_utils import now_sydney
from datetime import datetime, time

class VCTracking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_join_times = {}
        self.vc_current_users = {}  # {vc_id: set(user_ids)}
        self.tracking_active = {}   # {vc_id: bool}
        self.last_person_to_leave = {}

    def get_all_vc_ids(self):
        return [vc.id for g in self.bot.guilds for vc in g.voice_channels]
    

    @commands.Cog.listener()
    async def on_ready(self):
        print("[VCTracking] Bot is ready — rebuilding voice state tracking...")
        now = now_sydney()

        for guild in self.bot.guilds:
            for vc in guild.voice_channels:
                for member in vc.members:
                    if not member.bot:
                        self.user_join_times[str(member.id)] = now
                        self.vc_current_users.setdefault(vc.id, set()).add(member.id)

        print(f"[VCTracking] Reconstructed join state for {len(self.user_join_times)} users.")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        now = now_sydney()
        user_id = str(member.id)
        vc_ids = self.get_all_vc_ids()

        # vc_stats = load_json(vc_stats_FILE)
        # points = load_json(points_FILE)
        # loserboard = load_json(loserboard_FILE)
        # hallofshame = load_json(hallofshame_FILE)
        roast_data = load_json(roasts_FILE)

        # Leaving VC
        if before.channel and before.channel.id in vc_ids:
            vc_id = before.channel.id
            self.vc_current_users.setdefault(vc_id, set()).discard(member.id)

            # if user_id in self.user_join_times:
            #     minutes = (now - self.user_join_times[user_id]).total_seconds() / 60
            #     vc_stats[user_id] = round(vc_stats.get(user_id, 0) + minutes, 2)
            #     points[user_id] = int(points.get(user_id, 0) + minutes)
            #     save_json(vc_stats_FILE, vc_stats)
            #     save_json(points_FILE, points)
            #     del self.user_join_times[user_id]
            if user_id in self.user_join_times:
                minutes = (now - self.user_join_times[user_id]).total_seconds() / 60
                minutes_rounded = round(minutes)
                await add_vc_time_and_points(member.id, minutes_rounded)
                del self.user_join_times[user_id]

            await asyncio.sleep(1)
            channel = self.bot.get_channel(vc_id)

            # ✅ Only log a "loser" during tracking hours
            if self.tracking_active.get(vc_id) and len(channel.members) == 0:
                self.last_person_to_leave[vc_id] = member

                if not member.bot:
                    uid = str(member.id)
                    # loserboard.setdefault("loserboard", {})
                    # hallofshame.setdefault("hallofshame", {})

                    # loserboard["loserboard"][uid] = loserboard["loserboard"].get(uid, 0) + 1
                    # hallofshame["hallofshame"][uid] = hallofshame["hallofshame"].get(uid, 0) + 1

                    # save_json(loserboard_FILE, loserboard)
                    # save_json(hallofshame_FILE, hallofshame)

                    await increment_loser(member.id)

                    log_channel = self.bot.get_channel(get_log_channel_id())
                    roast_line = random.choice(roast_data.get("roast_messages", ["took the L."]))
                    if log_channel:
                        embed = discord.Embed(
                            title="**Tonight's BIGGEST LOSER!**",
                            description=f"{member.mention} just took the **BIGGEST L** in **{before.channel.name}**! {roast_line}",
                            color=discord.Color.red(),
                            timestamp=now
                        )
                        embed.set_thumbnail(url=member.display_avatar.url)
                        embed.set_footer(text="The peasant of the day.")
                        await asyncio.sleep(5)
                        await log_channel.send(embed=embed)

                self.last_person_to_leave[vc_id] = None
                self.tracking_active[vc_id] = False

        # Joining VC
        if after.channel and after.channel.id in vc_ids:
            if member.bot:
                return

            vc_id = after.channel.id
            self.vc_current_users.setdefault(vc_id, set()).add(member.id)
            self.user_join_times[user_id] = now

            # Start tracking if 2 or more users
            if len(self.vc_current_users[vc_id]) >= 2:
                self.tracking_active[vc_id] = True

    @commands.command()
    async def trackingstatus(self, ctx):
        embed = discord.Embed(
            title="🎯 VC Tracking Status",
            color=discord.Color.teal(),
            timestamp=now_sydney()
        )

        global_status = any(self.tracking_active.values())
        embed.description = f"**Global Tracking Active:** `{global_status}`"

        for vc_id, is_active in self.tracking_active.items():
            vc = self.bot.get_channel(vc_id)
            user_count = len(self.vc_current_users.get(vc_id, []))
            name = vc.name if vc else f"Unknown VC ({vc_id})"
            embed.add_field(
                name=f"{name}",
                value=f"Tracking: `{is_active}`\nUsers in VC: `{user_count}`",
                inline=False
            )

        await ctx.send(embed=embed)

async def setup(bot):
    print("[SETUP] Registering Leaderboards cog")
    await bot.add_cog(VCTracking(bot))