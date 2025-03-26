import discord
import random
import asyncio
from discord.ext import commands, tasks
from datetime import datetime
from utils.constants import roasts_FILE
from utils.sqlite_manager import add_vc_time_and_points, increment_loser
from utils.json_manager import load_json, get_log_channel_id
from utils.time_utils import now_sydney
from datetime import datetime, time

class VCTracking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_join_times = {}
        self.vc_current_users = {}  # {vc_id: set(user_ids)}
        self.tracking_active = {}   # {vc_id: bool}
        self.last_person_to_leave = {}
        self.session_points = {}

    def get_all_vc_ids(self):
        return [vc.id for g in self.bot.guilds for vc in g.voice_channels]
    
    def cog_load(self):
        self.periodic_vc_update.start()

    def cog_unload(self):
        self.periodic_vc_update.cancel()

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

        roast_data = load_json(roasts_FILE)

        # Leaving VC
        if before.channel and before.channel.id in vc_ids:
            vc_id = before.channel.id
            self.vc_current_users.setdefault(vc_id, set()).discard(member.id)

            if user_id in self.user_join_times:
                minutes = (now - self.user_join_times[user_id]).total_seconds() / 60
                minutes_rounded = round(minutes)
                await add_vc_time_and_points(member.id, minutes_rounded)
                self.session_points[str(member.id)] = self.session_points.get(str(member.id), 0) + minutes_rounded
                del self.user_join_times[user_id]

            await asyncio.sleep(1)
            channel = self.bot.get_channel(vc_id)

            if self.tracking_active.get(vc_id) and len(channel.members) == 0:
                self.last_person_to_leave[vc_id] = member

                if not member.bot:
                    uid = str(member.id)
                    aura_lost = self.session_points.get(uid, 0)
                    await add_vc_time_and_points(member.id, -aura_lost)

                    await increment_loser(member.id)

                    log_channel = self.bot.get_channel(get_log_channel_id())
                    roast_line = random.choice(roast_data.get("roast_messages", ["took the L."]))
                    if log_channel:
                        embed = discord.Embed(
                            title="**Tonight's BIGGEST LOSER!**",
                            description=f"{member.mention} just took the **BIGGEST L** in **{before.channel.name}**! {roast_line}\n\n"
                            f"They lost `-{aura_lost} aura` earned tonight",
                            color=discord.Color.red(),
                            timestamp=now
                        )
                        embed.set_thumbnail(url=member.display_avatar.url)
                        embed.set_footer(text="The peasant of the day.")
                        await asyncio.sleep(5)
                        await log_channel.send(embed=embed)

                self.session_points[uid] = 0
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

    @tasks.loop(minutes=10)
    async def periodic_vc_update(self):
        now = now_sydney()
        for user_id_str, join_time in list(self.user_join_times.items()):
            try:
                user_id = int(user_id_str)
                minutes_total = (now - join_time).total_seconds() / 60
                minutes_since_last = round(minutes_total)

                if minutes_since_last < 1:
                    continue

                bonus_multiplier = 2 if minutes_total >= 60 else 1
                points_awarded = minutes_since_last * bonus_multiplier

                await add_vc_time_and_points(user_id, minutes_since_last)
                self.session_points[user_id] = self.session_points.get(user_id, 0) + minutes_total
                

                # Reset the user's join time to now for next tracking cycle
                self.user_join_times[user_id_str] = now

                print(f"[VC TRACKING] Auto-added {minutes_since_last} mins ({'2x' if bonus_multiplier > 1 else '1x'}) to {user_id}")
            except Exception as e:
                print(f"[ERROR] Failed VC update for user {user_id_str}: {e}")
    
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
    cog = VCTracking(bot)
    await bot.add_cog(cog)
    cog.cog_load()