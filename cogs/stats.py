import discord
from discord.ext import commands
from utils.constants import bets_FILE
from utils.json_manager import load_json
from utils.sqlite_manager import (
    get_points,
    get_user,
    get_monthly_losers,
    get_lifetime_losers
)
from utils.time_utils import now_sydney

class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["profile", "mystats"])
    async def stats(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user_id = str(member.id)

        points, vc_minutes = await get_user(member.id)

        losers = dict(await get_monthly_losers(100))
        shame = dict(await get_lifetime_losers(100))
        monthly_ls = losers.get(user_id, 0)
        lifetime_ls = shame.get(user_id, 0)

        bets = load_json(bets_FILE)
        bet_data = bets.get(user_id)

        embed = discord.Embed(
            title=f"📊 Stats for {member.display_name}",
            color=discord.Color.teal(),
            timestamp=now_sydney()
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(name="🎤 VC Minutes", value=f"**{round(vc_minutes, 2)}**", inline=True)
        embed.add_field(name="💰 Points", value=f"**{int(points)}**", inline=True)
        embed.add_field(name="📉 Monthly Ls", value=f"**{monthly_ls}**", inline=True)
        embed.add_field(name="💀 Lifetime Ls", value=f"**{lifetime_ls}**", inline=True)

        if bet_data and isinstance(bet_data, dict):
            try:
                target = await self.bot.fetch_user(int(bet_data.get("bet_on", 0)))
                embed.add_field(name="🎲 Active Bet", value=f"{bet_data['amount']} on {target.display_name}", inline=False)
            except:
                embed.add_field(name="🎲 Active Bet", value=f"{bet_data['amount']} on Unknown", inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    print("[SETUP] Registering Leaderboards cog")
    await bot.add_cog(StatsCog(bot))
