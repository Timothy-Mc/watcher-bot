import discord
from discord.ext import commands
import aiosqlite

DB_PATH = "data/watcherbot.db"  # Adjust if needed

class AdminTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="adjustloser")
    @commands.has_permissions(administrator=True)
    async def adjust_losers(self, ctx, member: discord.Member, monthly: int = 0, lifetime: int = 0):
        async with aiosqlite.connect(DB_PATH) as db:
            if monthly != 0:
                await db.execute("""
                    INSERT INTO monthly_losers (user_id, count)
                    VALUES (?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET count = count + ?;
                """, (str(member.id), max(monthly, 0), monthly))

            if lifetime != 0:
                await db.execute("""
                    INSERT INTO lifetime_losers (user_id, count)
                    VALUES (?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET count = count + ?;
                """, (str(member.id), max(lifetime, 0), lifetime))

            await db.commit()

        await ctx.send(f"✅ Updated {member.display_name}'s Ls. Monthly: `{monthly}`, Lifetime: `{lifetime}`")

    @commands.command(name="loserstats")
    @commands.has_permissions(administrator=True)
    async def check_losers(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        uid = str(member.id)

        async with aiosqlite.connect(DB_PATH) as db:
            # Monthly
            async with db.execute("SELECT count FROM monthly_losers WHERE user_id = ?", (uid,)) as cur:
                monthly = await cur.fetchone()
            # Lifetime
            async with db.execute("SELECT count FROM lifetime_losers WHERE user_id = ?", (uid,)) as cur:
                lifetime = await cur.fetchone()

        monthly = monthly[0] if monthly else 0
        lifetime = lifetime[0] if lifetime else 0

        embed = discord.Embed(
            title=f"💀 Loser Stats for {member.display_name}",
            color=discord.Color.red()
        )
        embed.add_field(name="📉 Monthly Ls", value=f"**{monthly}**", inline=True)
        embed.add_field(name="💀 Lifetime Ls", value=f"**{lifetime}**", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)

        await ctx.send(embed=embed)

    @commands.command(name="adjustaura")
    @commands.has_permissions(administrator=True)
    async def adjust_aura(self, ctx, member: discord.Member, points: int = 0):
        async with aiosqlite.connect(DB_PATH) as db:
            if points != 0:
                await db.execute("""
                    INSERT INTO user_points (user_id, points)
                    VALUES (?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET points = points + ?;
                """, (str(member.id), points, points))

            await db.commit()

        await ctx.send(f"✅ Adjusted {member.display_name}'s aura by `{points}`")

async def setup(bot):
    print("[SETUP] Registering Admin Tools cog")
    await bot.add_cog(AdminTools(bot))