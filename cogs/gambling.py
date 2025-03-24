import discord
import random
import asyncio
from discord.ext import commands
from discord.ext.commands import BucketType
from utils.constants import points_FILE
from utils.json_manager import load_json, save_json

class Gambling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["cf"])
    @commands.cooldown(1, 10, BucketType.user)
    async def coinflip(self, ctx, choice: str, amount: int):
        choice = choice.lower()
        if choice not in ["heads", "tails"]:
            await ctx.send("Please choose `heads` or `tails`.")
            return

        if amount <= 0:
            await ctx.send("Bet must be more than 0.")
            return

        points = load_json(points_FILE)
        user_id = str(ctx.author.id)

        if points.get(user_id, 0) < amount:
            await ctx.send("You don't have enough points!")
            return

        result = random.choice(["heads", "tails"])
        win = result == choice

        if win:
            points[user_id] += amount
            outcome = f"It landed on **{result}**! You **won {amount} points**!"
        else:
            points[user_id] -= amount
            outcome = f"It landed on **{result}**! You **lost {amount} points**!"

        save_json(points_FILE, points)
        await ctx.send(f"{ctx.author.mention} {outcome}")

    @commands.command(aliases=["r"])
    @commands.cooldown(1, 10, BucketType.user)
    async def roll(self, ctx, opponent: discord.Member, amount: int):
        user1 = ctx.author
        user2 = opponent

        if user1 == user2:
            await ctx.send("You can't duel yourself.")
            return

        if amount <= 0:
            await ctx.send("Bet must be more than 0.")
            return

        points = load_json(points_FILE)
        uid1, uid2 = str(user1.id), str(user2.id)

        if points.get(uid1, 0) < amount or points.get(uid2, 0) < amount:
            await ctx.send("Both players must have enough points.")
            return

        challenge = await ctx.send(
            f"{user2.mention}, do you accept a **{amount} point** duel with {user1.mention}?\nReact ✅ to accept within 30 seconds."
        )
        await challenge.add_reaction("✅")

        def check(reaction, user):
            return (
                user == user2
                and str(reaction.emoji) == "✅"
                and reaction.message.id == challenge.id
            )

        try:
            await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(f"{user2.display_name} didn’t accept in time.")
            return

        roll1 = random.randint(1, 100)
        roll2 = random.randint(1, 100)

        embed = discord.Embed(
            title="🎲 Duel Roll!",
            color=discord.Color.gold(),
            description=f"**{user1.display_name}** vs **{user2.display_name}**\nBet: **{amount} points**"
        )

        embed.add_field(name=f"{user1.display_name}'s Roll", value=f"🎲 **{roll1}**", inline=True)
        embed.add_field(name=f"{user2.display_name}'s Roll", value=f"🎲 **{roll2}**", inline=True)

        embed.set_thumbnail(url=user1.display_avatar.url)
        embed.set_image(url=user2.display_avatar.url)

        if roll1 > roll2:
            points[uid1] += amount
            points[uid2] -= amount
            embed.add_field(name="🏆 Winner", value=f"{user1.mention} wins **{amount} points**!", inline=False)
            embed.color = discord.Color.green()
        elif roll2 > roll1:
            points[uid1] -= amount
            points[uid2] += amount
            embed.add_field(name="🏆 Winner", value=f"{user2.mention} wins **{amount} points**!", inline=False)
            embed.color = discord.Color.green()
        else:
            embed.add_field(name="🤝 Tie!", value="No points exchanged.", inline=False)
            embed.color = discord.Color.greyple()

        save_json(points_FILE, points)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 10, BucketType.user)
    async def slots(self, ctx, amount: int):
        if amount <= 0:
            await ctx.send("Bet must be more than 0.")
            return

        user_id = str(ctx.author.id)
        points = load_json(points_FILE)

        if points.get(user_id, 0) < amount:
            await ctx.send("You don't have enough points!")
            return

        emojis = ["🍒", "🍋", "🍇", "🔔", "⭐", "🍉"]
        result = [random.choice(emojis) for _ in range(3)]

        embed = discord.Embed(
            title="🎰 Slot Machine",
            description=f"{' | '.join(result)}",
            color=discord.Color.orange()
        )

        if result[0] == result[1] == result[2]:
            win_amount = amount * 3
            points[user_id] += win_amount
            embed.add_field(name="🎉 JACKPOT!", value=f"You won **{win_amount} points**!", inline=False)
        elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
            win_amount = amount * 2
            points[user_id] += win_amount
            embed.add_field(name="✨ Not bad!", value=f"You matched 2 and won **{win_amount} points**!", inline=False)
        else:
            points[user_id] -= amount
            embed.add_field(name="💀 Oof!", value=f"You lost **{amount} points**.", inline=False)

        save_json(points_FILE, points)
        await ctx.send(embed=embed)

async def setup(bot):
    print("[SETUP] Registering Leaderboards cog")
    await bot.add_cog(Gambling(bot))
