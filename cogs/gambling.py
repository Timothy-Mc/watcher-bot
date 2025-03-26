import discord
import random
import asyncio
from discord.ext import commands
from discord.ext.commands import BucketType
from utils.sqlite_manager import get_points, adjust_points

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
            await ctx.send("Must have more than 0 aura.")
            return

        user_id = ctx.author.id
        balance = await get_points(user_id)

        if balance < amount:
            await ctx.send("You don't have enough aura!")
            return

        result = random.choice(["heads", "tails"])
        win = result == choice

        if win:
            await adjust_points(user_id, +amount)
            msg = await ctx.send(
                f"{ctx.author.mention} It landed on **{result}**! You **won {amount} aura**!\n"
                "💥 Want to go **Double or Nothing**? React with ✅ to accept within 10 seconds!"
            )
            await msg.add_reaction("✅")
            await msg.add_reaction("❌")

            def check(reaction, user):
                return (
                    user == ctx.author and str(reaction.emoji) == "✅" and reaction.message.id == msg.id
                )
            
            try:
                await self.bot.wait_for("reaction_add", timeout=10.0, check=check)
                result2 = random.choice(["heads", "tails"])
                if result2 == choice:
                    await adjust_points(user_id, +amount)  # Win again
                    await ctx.send(f"🎉 It landed on **{result2}**! You doubled up and gained **{amount * 2} aura total!**")
                else:
                    await adjust_points(user_id, -amount * 2)  # Lose what they just won + original
                    await ctx.send(f"💀 It landed on **{result2}**... you lost **everything**. Total loss: -{amount} aura.")
            except asyncio.TimeoutError:
                await ctx.send("⌛ No reaction in time. You kept your original winnings.")
        else:
            await adjust_points(user_id, -amount)
            outcome = f"It landed on **{result}**! You **lost -{amount} aura**!"

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
            await ctx.send("Must have more than 0 aura.")
            return

        uid1, uid2 = user1.id, user2.id
        bal1 = await get_points(uid1)
        bal2 = await get_points(uid2)

        if bal1 < amount or bal2 < amount:
            await ctx.send("Both players must have enough aura.")
            return

        embed = discord.Embed(
            title="⚔️ Duel Challenge!",
            description=(
                f"{user2.mention}, do you accept a **{amount} aura** duel with {user1.mention}?\n\n"
                "React ✅ to accept within **30 seconds** or be marked a coward 😤"
            ),
            color=discord.Color.orange(),
            timestamp=ctx.message.created_at
        )
        embed.set_footer(text="Duel issued")
        embed.set_thumbnail(url=user1.display_avatar.url)

        challenge = await ctx.send(embed=embed)
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
            embed = discord.Embed(
                title="😴 Coward Detected!",
                description=f"{user2.mention} backed out of the duel.\nBOOOORING. Scared you might lose? Wimp. 😭😭😭",
                color=discord.Color.dark_red()
            )
            embed.set_footer(text="Step up or step aside.")
            await ctx.send(embed=embed)
            return

        roll1 = random.randint(1, 100)
        roll2 = random.randint(1, 100)

        embed = discord.Embed(
            title="🎲 Duel Roll!",
            color=discord.Color.gold(),
            description=f"**{user1.display_name}** vs **{user2.display_name}**\nBet: **{amount} aura**"
        )
        embed.add_field(name=f"{user1.display_name}'s Roll", value=f"🎲 **{roll1}**", inline=True)
        embed.add_field(name=f"{user2.display_name}'s Roll", value=f"🎲 **{roll2}**", inline=True)
        embed.set_thumbnail(url=user1.display_avatar.url)

        bonus = int(amount * 1.5)

        if roll1 > roll2:
            await adjust_points(uid1, bonus)
            await adjust_points(uid2, -amount)
            embed.add_field(name="🏆 Winner", value=f"{user1.mention} wins **{amount} aura**!", inline=False)
            embed.set_image(url=user1.display_avatar.url)
            embed.color = discord.Color.green()
        elif roll2 > roll1:
            await adjust_points(uid1, -amount)
            await adjust_points(uid2, bonus)
            embed.add_field(name="🏆 Winner", value=f"{user2.mention} wins **{amount} aura**!", inline=False)
            embed.set_image(url=user2.display_avatar.url)
            embed.color = discord.Color.green()
        else:
            embed.add_field(name="🤝 Tie!", value="No aura exchanged.", inline=False)
            embed.color = discord.Color.greyple()

        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 10, BucketType.user)
    async def slots(self, ctx, amount: int):
        if amount <= 0:
            await ctx.send("Must have more than 0 aura.")
            return

        user_id = ctx.author.id
        balance = await get_points(user_id)

        if balance < amount:
            await ctx.send("You don't have enough aura!")
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
            await adjust_points(user_id, win_amount)
            embed.add_field(name="🎉 JACKPOT!", value=f"You won **{win_amount} aura**!", inline=False)
        elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
            win_amount = amount * 2
            await adjust_points(user_id, win_amount)
            embed.add_field(name="✨ Not bad!", value=f"You matched 2 and won **{win_amount} aura**!", inline=False)
        else:
            await adjust_points(user_id, -amount)
            embed.add_field(name="💀 Oof!", value=f"You lost **-{amount} aura**.", inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    print("[SETUP] Registering Leaderboards cog")
    await bot.add_cog(Gambling(bot))
