import discord
from discord.ext import commands
from utils.constants import vc_stats_FILE, points_FILE, loserboard_FILE, hallofshame_FILE
from utils.json_manager import load_json
from utils.time_utils import now_sydney

class Leaderboards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["vc", "vclb"])
    async def vcleaderboard(self, ctx):
        vc_stats = load_json(vc_stats_FILE)
        sorted_vc = sorted(vc_stats.items(), key=lambda x: x[1], reverse=True)

        embed = discord.Embed(
            title="🎤 VC Activity Leaderboard",
            color=discord.Color.blue(),
            timestamp=now_sydney()
        )

        for rank, (user_id, minutes) in enumerate(sorted_vc[:10], start=1):
            try:
                user = await self.bot.fetch_user(int(user_id))
                embed.add_field(name=f"{rank}. {user.display_name}", value=f"**{round(minutes, 2)} mins**", inline=False)
            except:
                embed.add_field(name=f"{rank}. Unknown User", value=f"{round(minutes, 2)} mins", inline=False)

        await ctx.send(embed=embed)

    @commands.command(aliases=["pl", "points"])
    async def pointsleaderboard(self, ctx):
        points = load_json(points_FILE)
        sorted_points = sorted(points.items(), key=lambda x: x[1], reverse=True)

        embed = discord.Embed(
            title="💰 Points Leaderboard",
            color=discord.Color.green(),
            timestamp=now_sydney()
        )

        for rank, (user_id, pts) in enumerate(sorted_points[:10], start=1):
            try:
                user = await self.bot.fetch_user(int(user_id))
                embed.add_field(name=f"{rank}. {user.display_name}", value=f"**{int(pts)} points**", inline=False)
            except:
                embed.add_field(name=f"{rank}. Unknown User", value=f"**{int(pts)} points**", inline=False)

        await ctx.send(embed=embed)

    @commands.command(aliases=["lb"])
    async def loserboard(self, ctx):
        data = load_json(loserboard_FILE)
        loserboard = data.get("loserboard", {})

        if not loserboard:
            embed = discord.Embed(
                title="🏆 Biggest Losers of the Month",
                description="No Ls recorded yet this month!",
                color=discord.Color.gold(),
                timestamp=now_sydney()
            )
            await ctx.send(embed=embed)
            return

        sorted_losers = sorted(loserboard.items(), key=lambda x: x[1], reverse=True)

        embed = discord.Embed(
            title="🏆 Biggest Losers of the Month",
            color=discord.Color.gold(),
            timestamp=now_sydney()
        )

        for rank, (user_id, count) in enumerate(sorted_losers[:10], start=1):
            try:
                user = await self.bot.fetch_user(int(user_id))
                embed.add_field(name=f"{rank}. {user.display_name}", value=f"**{count} Ls**", inline=False)
            except:
                embed.add_field(name=f"{rank}. Unknown User", value=f"**{count} Ls**", inline=False)

        top_user_id = sorted_losers[0][0]
        try:
            top_user = await self.bot.fetch_user(int(top_user_id))
            embed.set_thumbnail(url=top_user.display_avatar.url)
        except:
            pass

        await ctx.send(embed=embed)

    @commands.command(aliases=["hs"])
    async def hallofshame(self, ctx):
        data = load_json(hallofshame_FILE)
        hall = data.get("hallofshame", {})

        if not hall:
            embed = discord.Embed(
                title="💀 Hall of Shame - Lifetime Ls",
                description="No one has been publicly shamed yet.",
                color=discord.Color.dark_red(),
                timestamp=now_sydney()
            )
            await ctx.send(embed=embed)
            return

        sorted_hall = sorted(hall.items(), key=lambda x: x[1], reverse=True)

        embed = discord.Embed(
            title="💀 Hall of Shame - Lifetime Ls",
            color=discord.Color.red(),
            timestamp=now_sydney()
        )

        for rank, (user_id, count) in enumerate(sorted_hall[:10], start=1):
            try:
                user = await self.bot.fetch_user(int(user_id))
                embed.add_field(name=f"{rank}. {user.display_name}", value=f"**{count} Ls**", inline=False)
            except:
                embed.add_field(name=f"{rank}. Unknown User", value=f"**{count} Ls**", inline=False)

        top_user_id = sorted_hall[0][0]
        try:
            top_user = await self.bot.fetch_user(int(top_user_id))
            embed.set_thumbnail(url=top_user.display_avatar.url)
        except:
            pass

        await ctx.send(embed=embed)

async def setup(bot):
    print("[SETUP] Registering Leaderboards cog")
    await bot.add_cog(Leaderboards(bot))
