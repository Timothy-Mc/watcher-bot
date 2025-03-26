import discord
import re
import datetime
from discord.ext import commands
from utils.constants import bets_FILE
from utils.json_manager import load_json, save_json
from utils.sqlite_manager import get_points, adjust_points
from utils.time_utils import now_sydney

class Betting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @staticmethod
    def parse_duration(duration_str):
        match = re.match(r"(\d+)([smhd])", duration_str)
        if not match:
            return None
        amount, unit = match.groups()
        amount = int(amount)
        if unit == "s": return datetime.timedelta(seconds=amount)
        if unit == "m": return datetime.timedelta(minutes=amount)
        if unit == "h": return datetime.timedelta(hours=amount)
        if unit == "d": return datetime.timedelta(days=amount)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def startbet(self, ctx, *, input_str: str):
        bets = load_json(bets_FILE)

        if "active_bet" in bets and not bets["active_bet"].get("resolved", False):
            await ctx.send("⚠️ A bet is already active. Resolve or cancel it first.")
            return

        # Parse input like: Question [option1, option2, option3] --duration 10m
        match = re.match(r'^(.+?)\s*\[(.+?)\](?:\s*--duration\s*(\S+))?$', input_str)
        if not match:
            await ctx.send("❌ Format: `~startbet Question here [Option1, Option2, Option3] --duration 30m`")
            return

        question, options_raw, duration_str = match.groups()
        options = [opt.strip().lower() for opt in options_raw.split(",") if opt.strip()]
        if len(options) < 2 or len(options) > 5:
            await ctx.send("❌ You must provide between 2 and 5 options.")
            return

        duration_td = self.parse_duration(duration_str or "10m")
        if not duration_td:
            await ctx.send("❌ Invalid duration. Use format like `10m`, `1h`, etc.")
            return

        end_time = (now_sydney() + duration_td).timestamp()

        bets["active_bet"] = {
            "question": question.strip(),
            "creator": str(ctx.author.id),
            "options": options,
            "bets": {opt: {} for opt in options},
            "resolved": False,
            "result": None,
            "end_time": end_time
        }

        save_json(bets_FILE, bets)

        embed = discord.Embed(
            title="🧠 New Bet Started!",
            description=(
                f"**{question.strip()}**\n"
                f"Place your bets using `~placebet [option] [amount]`\n\n"
                f"**Betting closes in `{duration_str}`!**"
            ),
            color=discord.Color.green(),
            timestamp=now_sydney()
        )
        for opt in options:
            embed.add_field(name=opt.upper(), value="0 user(s)", inline=True)

        embed.set_footer(text="You cannot bet after the window closes.")
        await ctx.send(embed=embed)

    @commands.command()
    async def placebet(self, ctx, option: str, amount: int):
        option = option.lower()
        user_id = str(ctx.author.id)
        balance = await get_points(ctx.author.id)
        bets = load_json(bets_FILE)

        if "active_bet" not in bets or bets["active_bet"]["resolved"]:
            await ctx.send("❌ There's no active bet right now.")
            return

        bet = bets["active_bet"]

        if now_sydney().timestamp() > bet.get("end_time", float("inf")):
            await ctx.send("⛔ Betting is closed for this bet.")
            return

        if option not in bet["options"]:
            await ctx.send(f"❌ Invalid option. Valid options: {', '.join(bet['options'])}")
            return

        if amount <= 0:
            await ctx.send("❌ Amount must be more than 0.")
            return

        if balance < amount:
            await ctx.send("💸 You don’t have enough aura.")
            return

        if any(user_id in bet["bets"][opt] for opt in bet["options"]):
            await ctx.send("⚠️ You've already placed a bet.")
            return

        bet["bets"][option][user_id] = amount

        await adjust_points(ctx.author.id, -amount)
        save_json(bets_FILE, bets)

        await ctx.send(f"✅ {ctx.author.mention} placed **{amount}** on **{option.upper()}**.")

    @commands.command()
    async def activebet(self, ctx):
        bets = load_json(bets_FILE)
        if "active_bet" not in bets or bets["active_bet"]["resolved"]:
            await ctx.send("ℹ️ No active bet right now.")
            return

        bet = bets["active_bet"]
        embed = discord.Embed(
            title="🎲 Active Bet",
            description=f"**{bet['question']}**\nUse `~placebet [option] [amount]` to join.",
            color=discord.Color.blurple(),
            timestamp=now_sydney()
        )

        for opt in bet["options"]:
            count = len(bet["bets"].get(opt, {}))
            embed.add_field(name=opt.upper(), value=f"{count} user(s)", inline=True)

        # Optional: Show time left
        seconds_left = int(bet["end_time"] - now_sydney().timestamp())
        if seconds_left > 0:
            minutes = seconds_left // 60
            seconds = seconds_left % 60
            embed.set_footer(text=f"Betting closes in {minutes}m {seconds}s")
        else:
            embed.set_footer(text="⛔ Betting is now closed.")

        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def resolvebet(self, ctx, winning_option: str):
        bets = load_json(bets_FILE)

        if "active_bet" not in bets or bets["active_bet"]["resolved"]:
            await ctx.send("❌ No unresolved active bet.")
            return

        bet = bets["active_bet"]
        winning_option = winning_option.lower()

        if winning_option not in bet["options"]:
            await ctx.send(f"❌ Winning option must be one of: {', '.join(bet['options'])}")
            return

        winners = bet["bets"].get(winning_option, {})
        losers = {
            uid: amt
            for opt, opt_bets in bet["bets"].items()
            if opt != winning_option
            for uid, amt in opt_bets.items()
        }

        total_winner_bet = sum(winners.values())
        total_pot = total_winner_bet + sum(losers.values())

        if not winners:
            bet["resolved"] = True
            bet["result"] = winning_option
            save_json(bets_FILE, bets)
            await ctx.send("💀 Nobody bet on the winning option. The pot disappears into the void.")
            return

        # Payout
        for uid, amt in winners.items():
            share = amt / total_winner_bet
            payout = int(total_pot * share)
            await adjust_points(int(uid), payout)

        bet["resolved"] = True
        bet["result"] = winning_option
        save_json(bets_FILE, bets)

        embed = discord.Embed(
            title="✅ Bet Resolved!",
            description=(
                f"**Result:** {winning_option.upper()}\n"
                f"**Pot:** {total_pot} aura\n"
                f"**Winners:** {len(winners)} user(s)\n"
                f"**Losers:** {len(losers)} user(s)"
            ),
            color=discord.Color.green(),
            timestamp=now_sydney()
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def cancelbet(self, ctx):
        bets = load_json(bets_FILE)
        if "active_bet" not in bets or bets["active_bet"].get("resolved", False):
            await ctx.send("⚠️ No active bet to cancel.")
            return

        question = bets["active_bet"].get("question", "Unknown question")
        del bets["active_bet"]
        save_json(bets_FILE, bets)

        await ctx.send(f"❌ Bet cancelled: `{question}`")

async def setup(bot):
    print("[SETUP] Registering Leaderboards cog")
    await bot.add_cog(Betting(bot))
