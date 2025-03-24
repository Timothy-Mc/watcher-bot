import discord
from discord.ext import commands
from utils.json_manager import load_json
from utils.constants import vc_stats_FILE, points_FILE, loserboard_FILE, hallofshame_FILE, bets_FILE
from utils.time_utils import now_sydney

class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["profile", "mystats"])
    async def stats(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user_id = str(member.id)

        vc_stats = load_json(vc_stats_FILE)
        points = load_json(points_FILE)
        loserboard = load_json(loserboard_FILE).get("loserboard", {})
        hallofshame = load_json(hallofshame_FILE).get("hallofshame", {})
        bets = load_json(bets_FILE)

        vc_minutes = vc_stats.get(user_id, 0)
        user_points = points.get(user_id, 0)
        monthly_ls = loserboard.get(user_id, 0)
        lifetime_ls = hallofshame.get(user_id, 0)
        bet_data = bets.get(user_id)

        embed = discord.Embed(
            title=f"📊 Stats for {member.display_name}",
            color=discord.Color.teal(),
            timestamp=now_sydney()
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(name="🎤 VC Minutes", value=f"**{round(vc_minutes, 2)}**", inline=True)
        embed.add_field(name="💰 Points", value=f"**{int(user_points)}**", inline=True)
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
