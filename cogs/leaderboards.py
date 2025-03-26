import discord
from discord.ext import commands
from utils.time_utils import now_sydney
from utils.sqlite_manager import (
    get_top_vc_minutes, get_top_points,
    get_monthly_losers, get_lifetime_losers
)

class Leaderboards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def mock_title_and_value(self, rank, user, value, board):
        name = user.display_name if user else "Unknown User"

        if board == "aura":
            titles = {
                1: ("🧙‍♂️ Supreme Aura Lord", f"💫 {int(value)} aura... cringe.", discord.Color.gold()),
                2: ("🦼 Assistant Aura Farmer", f"🦼 {int(value)} aura.", discord.Color.light_gray()),
                3: ("🤓 Spiritually Mid", f"🤓 {int(value)} aura.", discord.Color.orange()),
            }
        elif board == "vc":
            titles = {
                1: ("🎧 Ultimate VC Gremlin", f"⏰ {int(value)} mins in VC...", discord.Color.dark_green()),
                2: ("🛎️ Touch Grass Trainee", f"🌔 {int(value)} mins logged.", discord.Color.teal()),
                3: ("😵 Voice Addicted Goblin", f"😵 {int(value)} mins.", discord.Color.green()),
            }
        elif board == "loser":
            titles = {
                1: ("🚽 Certified Discord Loser", f"💀 {value} Ls taken.", discord.Color.from_rgb(101, 67, 33)),
                2: ("🐌 Runner-Up Loser", f"😢 {value} Ls.", discord.Color.from_rgb(120, 72, 35)),
                3: ("🫠 Third Place L Machine", f"🫠 {value} Ls.", discord.Color.from_rgb(139, 69, 19)),
            }
        elif board == "shame":
            titles = {
                1: ("🨻 L-ifetime Champion", f"🚨 {value} lifetime Ls.", discord.Color.from_rgb(102, 51, 0)),
                2: ("💩 Legendary Disgrace", f"😬 {value} Ls and counting.", discord.Color.from_rgb(111, 78, 55)),
                3: ("😶‍🌫️ Hall Monitor of Shame", f"😓 {value} Ls.", discord.Color.from_rgb(133, 94, 66)),
            }
        else:
            titles = {}

        if rank in titles:
            title, value_text, color = titles[rank]
            return f"{rank}. {name} — {title}", value_text, color
        else:
            return f"{rank}. {name}", f"**{int(value)}**" if isinstance(value, (int, float)) else f"**{value}**", discord.Color.default()

    async def generate_leaderboard(self, ctx, title, default_color, data, board_type):
        embed = discord.Embed(title=title, color=default_color, timestamp=now_sydney())
        if not data:
            embed.description = "No data found. Try being less irrelevant."
            await ctx.send(embed=embed)
            return

        for rank, (user_id, value) in enumerate(data, start=1):
            try:
                user = await self.bot.fetch_user(int(user_id))
            except:
                user = None

            field_name, field_value, color = self.mock_title_and_value(rank, user, value, board_type)
            embed.add_field(name=field_name, value=field_value, inline=False)

            if rank == 1:
                embed.color = color  # Set embed color to top 1's theme

        try:
            top_user = await self.bot.fetch_user(int(data[0][0]))
            embed.set_thumbnail(url=top_user.display_avatar.url)
        except:
            pass

        await ctx.send(embed=embed)

    @commands.command(aliases=["vc", "vclb"])
    async def vcleaderboard(self, ctx):
        data = await get_top_vc_minutes()
        await self.generate_leaderboard(ctx, "🎧 VC Degeneracy Leaderboard", discord.Color.dark_green(), data, "vc")

    @commands.command(aliases=["points", "ab", "aura", "auraleaderbaord"])
    async def pointsleaderboard(self, ctx):
        data = await get_top_points()
        await self.generate_leaderboard(ctx, "🌟 Aura Leaderboard", discord.Color.gold(), data, "aura")

    @commands.command(aliases=["lb"])
    async def loserboard(self, ctx):
        data = await get_monthly_losers()
        await self.generate_leaderboard(ctx, "🏆 Monthly Ls - Biggest Discord Losers", discord.Color.from_rgb(101, 67, 33), data, "loser")

    @commands.command(aliases=["hs"])
    async def hallofshame(self, ctx):
        data = await get_lifetime_losers()
        await self.generate_leaderboard(ctx, "💀 Hall of Shame - Lifetime L Takers", discord.Color.from_rgb(102, 51, 0), data, "shame")

async def setup(bot):
    print("[SETUP] Registering Mocked Leaderboards cog")
    await bot.add_cog(Leaderboards(bot))