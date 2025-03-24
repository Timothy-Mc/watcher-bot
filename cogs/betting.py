import discord
from discord.ext import commands
from utils.constants import bets_FILE, points_FILE
from utils.json_manager import load_json, save_json
from utils.time_utils import now_sydney

class Betting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def startbet(self, ctx, *, question: str):
        bets = load_json(bets_FILE)

        if "active_bet" in bets and not bets["active_bet"].get("resolved", False):
            await ctx.send("⚠️ A bet is already active. Resolve or cancel it first.")
            return

        bets["active_bet"] = {
            "question": question,
            "creator": str(ctx.author.id),
            "bets": {"yes": {}, "no": {}},
            "resolved": False,
            "result": None
        }

        save_json(bets_FILE, bets)

        embed = discord.Embed(
            title="🧠 New Bet Started!",
            description=f"> {question}\n\nUse `~placebet yes/no amount` to join.",
            color=discord.Color.green(),
            timestamp=now_sydney()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def placebet(self, ctx, option: str, amount: int):
        option = option.lower()
        user_id = str(ctx.author.id)
        points = load_json(points_FILE)
        bets = load_json(bets_FILE)

        if option not in ["yes", "no"]:
            await ctx.send("❌ Option must be `yes` or `no`.")
            return

        if "active_bet" not in bets or bets["active_bet"]["resolved"]:
            await ctx.send("❌ There's no active bet right now.")
            return

        if amount <= 0:
            await ctx.send("❌ Amount must be more than 0.")
            return

        if points.get(user_id, 0) < amount:
            await ctx.send("💸 You don’t have enough points.")
            return

        if user_id in bets["active_bet"]["bets"]["yes"] or user_id in bets["active_bet"]["bets"]["no"]:
            await ctx.send("⚠️ You've already placed a bet.")
            return

        points[user_id] -= amount
        bets["active_bet"]["bets"][option][user_id] = amount

        save_json(points_FILE, points)
        save_json(bets_FILE, bets)

        await ctx.send(f"✅ {ctx.author.mention} placed **{amount}** on **{option.upper()}**.")

    @commands.command()
    async def activebet(self, ctx):
        bets = load_json(bets_FILE)
        if "active_bet" not in bets or bets["active_bet"]["resolved"]:
            await ctx.send("ℹ️ No active bet right now.")
            return

        bet = bets["active_bet"]
        yes_bets = len(bet["bets"]["yes"])
        no_bets = len(bet["bets"]["no"])

        embed = discord.Embed(
            title="🎲 Active Bet",
            description=f"**{bet['question']}**\nUse `~placebet yes/no amount` to join.",
            color=discord.Color.blurple(),
            timestamp=now_sydney()
        )
        embed.add_field(name="🟢 YES", value=f"{yes_bets} user(s)", inline=True)
        embed.add_field(name="🔴 NO", value=f"{no_bets} user(s)", inline=True)

        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def resolvebet(self, ctx, winning_option: str):
        winning_option = winning_option.lower()
        if winning_option not in ["yes", "no"]:
            await ctx.send("❌ Winning option must be `yes` or `no`.")
            return

        bets = load_json(bets_FILE)
        points = load_json(points_FILE)

        if "active_bet" not in bets or bets["active_bet"]["resolved"]:
            await ctx.send("❌ No unresolved active bet.")
            return

        bet = bets["active_bet"]
        winners = bet["bets"][winning_option]
        losers = bet["bets"]["no" if winning_option == "yes" else "yes"]

        total_pot = sum(winners.values()) + sum(losers.values())
        total_winner_bet = sum(winners.values())

        if not winners:
            bet["resolved"] = True
            bet["result"] = winning_option
            save_json(bets_FILE, bets)
            await ctx.send("💀 Nobody bet on the winning side. The pot disappears into the void.")
            return

        # Payout
        for uid, amt in winners.items():
            share = amt / total_winner_bet
            payout = int(total_pot * share)
            points[uid] = points.get(uid, 0) + payout

        bet["resolved"] = True
        bet["result"] = winning_option
        save_json(bets_FILE, bets)
        save_json(points_FILE, points)

        embed = discord.Embed(
            title="✅ Bet Resolved!",
            description=(
                f"**Result:** {winning_option.upper()}\n"
                f"**Pot:** {total_pot} points\n"
                f"**Winners:** {len(winners)} user(s)"
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
