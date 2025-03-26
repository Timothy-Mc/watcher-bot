import discord
import asyncio
from discord.ext import commands
from utils.time_utils import now_sydney

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="help")
    async def help_command(self, ctx):
        pages = []

        # Page 1 - General Info
        embed1 = discord.Embed(
            title="📘 Watcher Bot Help (1/4)",
            description="**General & Leaderboards**",
            color=discord.Color.blurple(),
            timestamp=now_sydney()
        )
        embed1.add_field(name="`~vcleaderboard` / `~vc` / `~vclb`", value="Top 10 users by VC time this month.", inline=False)
        embed1.add_field(name="`~auraleaderbaord` / `~aura` / `~al`", value="Top 10 users by total aura.", inline=False)
        embed1.add_field(name="`~loserboard` / `~lb`", value="Top 10 monthly VC leavers (biggest Ls).", inline=False)
        embed1.add_field(name="`~hallofshame` / `~hs`", value="Lifetime biggest losers (all-time Ls).", inline=False)
        embed1.add_field(name="`~stats [@user]` / `~mystats` / `~profile`", value="See your or another user's stats.", inline=False)
        pages.append(embed1)

        # Page 2 - Gambling
        embed2 = discord.Embed(
            title="🎰 Watcher Bot Help (2/4)",
            description="**Gambling Commands**",
            color=discord.Color.orange(),
            timestamp=now_sydney()
        )
        embed2.add_field(name="`~coinflip heads/tails amount` / `~cf`", value="50/50 chance to double your bet.\nIf you win, you can react to go **double or nothing**!", inline=False)
        embed2.add_field(name="`~roll @user amount` / `~r`", value="Duel another user. Higher roll wins the pot.\nWinner gains **1.5x aura**, loser loses full bet.", inline=False)
        embed2.add_field(name="`~slots amount`", value="Slot machine for fun (and losses).", inline=False)
        pages.append(embed2)

        # Page 3 - Betting System
        embed3 = discord.Embed(
            title="🧠 Watcher Bot Help (3/4)",
            description="**Community Betting System**",
            color=discord.Color.green(),
            timestamp=now_sydney()
        )
        embed3.add_field(name="`~startbet question`", value="(Admin) Starts a new yes/no bet.", inline=False)
        embed3.add_field(name="`~placebet yes/no amount`", value="Join the bet with your prediction.", inline=False)
        embed3.add_field(name="`~resolvebet yes/no`", value="(Admin) Resolve the bet & payout winners.", inline=False)
        embed3.add_field(name="`~cancelbet`", value="(Admin) Cancel an active bet.", inline=False)
        embed3.add_field(name="`~activebet`", value="See the current bet and vote counts.", inline=False)
        pages.append(embed3)

        # Page 4 - Summoning
        embed4 = discord.Embed(
            title="🔮 Watcher Bot Help (4/4)",
            description="**Summon & Auto Summon**",
            color=discord.Color.purple(),
            timestamp=now_sydney()
        )
        embed4.add_field(name="`~summon @user`", value="Sends a creepy summon DM to a user not in VC.", inline=False)
        embed4.add_field(name="`~autosummon enable/disable`", value="(Admin) Toggles auto-summon for tracked users.", inline=False)
        pages.append(embed4)

        current_page = 0
        message = await ctx.send(embed=pages[current_page])
        await message.add_reaction("◀️")
        await message.add_reaction("▶️")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"] and reaction.message.id == message.id

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                if str(reaction.emoji) == "▶️":
                    current_page = (current_page + 1) % len(pages)
                    await message.edit(embed=pages[current_page])
                    await message.remove_reaction(reaction.emoji, user)

                elif str(reaction.emoji) == "◀️":
                    current_page = (current_page - 1) % len(pages)
                    await message.edit(embed=pages[current_page])
                    await message.remove_reaction(reaction.emoji, user)

            except asyncio.TimeoutError:
                try:
                    await message.clear_reactions()
                except discord.Forbidden:
                    pass
                break

async def setup(bot):
    print("[SETUP] Registering Leaderboards cog")
    await bot.add_cog(HelpCog(bot))    