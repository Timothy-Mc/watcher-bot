from discord.ext import commands
from utils.json_manager import set_log_channel_id

class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setlogchannel(self, ctx):
        set_log_channel_id(ctx.channel.id)
        await ctx.send(f"This channel is now set as the log channel.")

async def setup(bot):
    print("[SETUP] Registering Leaderboards cog")
    await bot.add_cog(Config(bot))