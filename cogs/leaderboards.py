import discord
from discord.ext import commands
from utils.constants import vc_stats_FILE, points_FILE, loserboard_FILE, hallofshame_FILE
from utils.json_manager import load_json
from utils.time_utils import now_sydney
from utils.sqlite_manager import (
    get_top_vc_minutes, get_top_points,
    get_monthly_losers, get_lifetime_losers
)

class Leaderboards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["vc", "vclb"])
    async def vcleaderboard(self, ctx):
        top_users = await get_top_vc_minutes()

        embed = discord.Embed(
            title="🎤 VC Activity Leaderboard",
            color=discord.Color.blue(),
            timestamp=now_sydney()
        )

        for rank, (user_id, minutes) in enumerate(top_users, start=1):
            try:
                user = await self.bot.fetch_user(int(user_id))
                embed.add_field(name=f"{rank}. {user.display_name}", value=f"**{int(minutes)} mins**", inline=False)
            except:
                embed.add_field(name=f"{rank}. Unknown User", value=f"**{int(minutes)} mins**", inline=False)

        await ctx.send(embed=embed)

    @commands.command(aliases=["pl", "points"])
    async def pointsleaderboard(self, ctx):
        top_users = await get_top_points()

        embed = discord.Embed(
            title="💰 Points Leaderboard",
            color=discord.Color.green(),
            timestamp=now_sydney()
        )

        for rank, (user_id, points) in enumerate(top_users, start=1):
            try:
                user = await self.bot.fetch_user(int(user_id))
                embed.add_field(name=f"{rank}. {user.display_name}", value=f"**{int(points)} points**", inline=False)
            except:
                embed.add_field(name=f"{rank}. Unknown User", value=f"**{int(points)} points**", inline=False)

        await ctx.send(embed=embed)

    @commands.command(aliases=["lb"])
    async def loserboard(self, ctx):
        losers = await get_monthly_losers()

        embed = discord.Embed(
            title="🏆 Biggest Losers of the Month",
            color=discord.Color.gold(),
            timestamp=now_sydney()
        )

        if not losers:
            embed.description = "No Ls recorded yet this month!"
            await ctx.send(embed=embed)
            return

        for rank, (user_id, count) in enumerate(losers, start=1):
            try:
                user = await self.bot.fetch_user(int(user_id))
                embed.add_field(name=f"{rank}. {user.display_name}", value=f"**{count} Ls**", inline=False)
            except:
                embed.add_field(name=f"{rank}. Unknown User", value=f"**{count} Ls**", inline=False)

        try:
            top_user = await self.bot.fetch_user(int(losers[0][0]))
            embed.set_thumbnail(url=top_user.display_avatar.url)
        except:
            pass

        await ctx.send(embed=embed)

    @commands.command(aliases=["hs"])
    async def hallofshame(self, ctx):
        shame = await get_lifetime_losers()

        embed = discord.Embed(
            title="💀 Hall of Shame - Lifetime Ls",
            color=discord.Color.red(),
            timestamp=now_sydney()
        )

        if not shame:
            embed.description = "No one has been publicly shamed yet."
            await ctx.send(embed=embed)
            return

        for rank, (user_id, count) in enumerate(shame, start=1):
            try:
                user = await self.bot.fetch_user(int(user_id))
                embed.add_field(name=f"{rank}. {user.display_name}", value=f"**{count} Ls**", inline=False)
            except:
                embed.add_field(name=f"{rank}. Unknown User", value=f"**{count} Ls**", inline=False)

        try:
            top_user = await self.bot.fetch_user(int(shame[0][0]))
            embed.set_thumbnail(url=top_user.display_avatar.url)
        except:
            pass

        await ctx.send(embed=embed)

async def setup(bot):
    print("[SETUP] Registering Leaderboards cog")
    await bot.add_cog(Leaderboards(bot))
