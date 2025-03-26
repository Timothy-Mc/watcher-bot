import discord
from discord.ext import commands
import os
import asyncio
import traceback
from utils.sqlite_manager import (
    init_db, init_loser_tables, init_meta_table,
    maybe_reset_monthly_losers
)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="~", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"[LOADED] Cog: {filename}")
            except Exception as e:
                print(f"[ERROR] Failed to load {filename}: {e}")
                traceback.print_exc()

async def main():
    await init_db()
    await init_loser_tables()
    await init_meta_table()
    # await maybe_reset_monthly_losers()

    async with bot:
        await load_cogs()
        with open("tokenWatcher.txt", "r") as f:
            token = f.read().strip()
        await bot.start(token)

asyncio.run(main())
