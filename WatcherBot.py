import json
import discord
import asyncio
import random
import os
from discord.ext import commands, tasks
from discord.ext.commands import BucketType
from datetime import datetime, time, timedelta
import pytz

SYDNEY_TZ = pytz.timezone('Australia/Sydney')

# Channel IDs (Replace with actual IDs)
VOICE_CHANNEL_IDS = [851038508810240015, 910091498358464572, 1342051891739230279, 1010130915416084520, 942761000334159882, 877137739328413736, 990191271060602920]
LOG_CHANNEL_ID = 975760066659639417

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="~", intents=intents, help_command=None)

last_person_to_leave = {vc_id: None for vc_id in VOICE_CHANNEL_IDS}
tracking_active = {vc_id: False for vc_id in VOICE_CHANNEL_IDS}
user_join_times = {}
vc_current_users = {vc_id: set() for vc_id in VOICE_CHANNEL_IDS}


loserboard_FILE = "loserboard.json"
vc_stats_FILE = "vc_stats.json"
points_FILE = "points.json"
hallofshame_FILE = "hallofshame.json"
bets_FILE = "bets.json"
roasts_FILE = "roasts.json"
summons_FILE = "summons.json"

def load_json(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def load_roasts():
    roasts = load_json(roasts_FILE)
    return roasts.get("roast_messages", [])

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.loop.create_task(enable_tracking())
    backup_json_files.start()
    # monthly_reset_task.start()

@bot.event
async def on_voice_state_update(member, before, after):
    now = datetime.now(SYDNEY_TZ)
    vc_stats = load_json(vc_stats_FILE)
    points = load_json(points_FILE)
    loserboard_data = load_json(loserboard_FILE)
    hallofshame_data = load_json(hallofshame_FILE)
    user_id = str(member.id)

    for vc_id in VOICE_CHANNEL_IDS:
        if before.channel and before.channel.id == vc_id:
            if not member.bot:
                vc_current_users[vc_id].discard(member.id)

            if tracking_active[vc_id] and not after.channel and len(vc_current_users[vc_id]) == 0:
                last_person_to_leave[vc_id] = member

                if last_person_to_leave[vc_id].bot:
                    return

                loserboard = loserboard_data.get("loserboard", {})
                hallofshame = hallofshame_data.get("hallofshame", {})
                loserboard[user_id] = loserboard.get(user_id, 0) + 1
                hallofshame[user_id] = hallofshame.get(user_id, 0) + 1
                loserboard_data["loserboard"] = loserboard
                hallofshame_data["hallofshame"] = hallofshame
                save_json(loserboard_FILE, loserboard_data)
                save_json(hallofshame_FILE, hallofshame_data)

                log_channel = bot.get_channel(LOG_CHANNEL_ID)
                if log_channel:
                    roast_message = random.choice(load_roasts())
                    embed = discord.Embed(
                        title="**Tonight's BIGGEST LOSER!**",
                        description=f"{member.mention} just took the **BIGGEST L** in **{before.channel.name}**! {roast_message}",
                        color=discord.Color.red(),
                        timestamp=datetime.now(SYDNEY_TZ)
                    )
                    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
                    embed.set_footer(text="The peasant of the day.")

                    await asyncio.sleep(10)
                    await log_channel.send(embed=embed)

                last_person_to_leave[vc_id] = None
                tracking_active[vc_id] = False

        if after.channel and after.channel.id == vc_id:
            if not member.bot:
                vc_current_users[vc_id].add(member.id)

            if len(vc_current_users[vc_id]) > 2:
                tracking_active[vc_id] = True

    if after.channel and after.channel.id in VOICE_CHANNEL_IDS:
        user_join_times[user_id] = now

    if before.channel and before.channel.id in VOICE_CHANNEL_IDS and not after.channel:
        if user_id in user_join_times:
            time_spent = (now - user_join_times[user_id]).total_seconds() / 60
            vc_stats[user_id] = round(vc_stats.get(user_id, 0) + time_spent, 2)
            points[user_id] = round(points.get(user_id, 0) + time_spent, 2)
            save_json(vc_stats_FILE, vc_stats)
            save_json(points_FILE, points)
            del user_join_times[user_id]

    if after.channel and after.channel.id in VOICE_CHANNEL_IDS:
        user_join_times[user_id] = now
    
    if before.channel and before.channel.id in VOICE_CHANNEL_IDS and not after.channel:
        if user_id in user_join_times:
            time_spent = (now - user_join_times[user_id]).total_seconds() / 60
            vc_stats[user_id] = round(vc_stats.get(user_id, 0) + time_spent, 2)
            points[user_id] = round(points.get(user_id, 0) + time_spent, 2)
            save_json(vc_stats_FILE, vc_stats)
            save_json(points_FILE, points)
            del user_join_times[user_id]

@bot.command(aliases=['vc', 'vclb'])
async def vcleaderboard(ctx):
    vc_stats = load_json(vc_stats_FILE)
    sorted_vc = sorted(vc_stats.items(), key=lambda x: x[1], reverse=True)
    
    embed = discord.Embed(
        title="**VC Activity Leaderboard**",
        color=discord.Color.blue(),
        timestamp=datetime.now(SYDNEY_TZ)
    )
    leaderboard_text = ""
    for rank, (user_id, minutes) in enumerate(sorted_vc[:10], start=1):
        try:
            user = await bot.fetch_user(int(user_id))
            leaderboard_text += f"**{rank}.** {user.display_name} - **{minutes} minutes**\n"
        except discord.NotFound:
            leaderboard_text += f"**{rank}.** Unknown User ({user_id}) - **{minutes} minutes**\n"
    
    embed.description = leaderboard_text
    await ctx.send(embed=embed)

@bot.command(aliases=['lb'])
async def loserboard(ctx):
    loserboard_data = load_json(loserboard_FILE)
    loserboard = loserboard_data.get("loserboard", {})


    if not loserboard:
        embed = discord.Embed(
            title="**Biggest Losers of the Month**",
            description="No losers recorded yet!",
            color=discord.Color.gold(),
            timestamp=datetime.now(SYDNEY_TZ)
        )
        embed.set_footer(text="Who will take the first L?")
        await ctx.send(embed=embed)
        return
    
    sorted_loserboard = sorted(loserboard.items(), key=lambda x: x[1], reverse=True)

    embed = discord.Embed(
        title="**Biggest Losers of the Month**",
        color=discord.Color.gold(),
        timestamp=datetime.now(SYDNEY_TZ)
    )

    loserboard_text = ""
    user_avatars = {}

    for rank, (user_id, count) in enumerate(sorted_loserboard[:10], start=1):
        try:
            user = await bot.fetch_user(int(user_id))
            pfp_url = user.avatar.url if user.avatar else user.default_avatar.url
            user_avatars[rank] = pfp_url

            loserboard_text += f"**{rank}.** {user.display_name} - **{count} Ls**\n"

        except discord.NotFound:
            loserboard_text += f"**{rank}.** Unknown User ({user_id}) - **{count} Ls**\n"

    embed.description = loserboard_text

    if sorted_loserboard:
        top_user_id = sorted_loserboard[0][0]
        try:
            top_user = await bot.fetch_user(int(top_user_id))
            top_pfp = top_user.avatar.url if top_user.avatar else top_user.default_avatar.url
            embed.set_thumbnail(url=top_pfp)
        except discord.NotFound:
            pass

    embed.set_footer(text="Who will take the next L?")

    await ctx.send(embed=embed)

@bot.command(aliases=['pl', 'points'])
async def pointsleaderboard(ctx):
    points = load_json(points_FILE)
    sorted_points = sorted(points.items(), key=lambda x: x[1], reverse=True)
    
    embed = discord.Embed(
        title="**Points Leaderboard**",
        color=discord.Color.green(),
        timestamp=datetime.now(SYDNEY_TZ)
    )
    leaderboard_text = ""
    for rank, (user_id, points) in enumerate(sorted_points[:10], start=1):
        try:
            user = await bot.fetch_user(int(user_id))
            leaderboard_text += f"**{rank}.** {user.display_name} - **{points} points**\n"
        except discord.NotFound:
            leaderboard_text += f"**{rank}.** Unknown User ({user_id}) - **{points} points**\n"
    
    embed.description = leaderboard_text
    await ctx.send(embed=embed)

@bot.command(aliases=['hs'])
async def hallofshame(ctx):
    data = load_json(hallofshame_FILE)
    hallofshame = data.get("hallofshame", {})

    if not hallofshame:
        embed = discord.Embed(
            title="**Hall of Shame - Lifetime Ls**",
            description="Nobody's been publicly shamed... yet.",
            color=discord.Color.dark_red(),
            timestamp=datetime.now(SYDNEY_TZ)
        )
        await ctx.send(embed=embed)
        return

    sorted_hall = sorted(hallofshame.items(), key=lambda x: x[1], reverse=True)

    embed = discord.Embed(
        title="**Hall of Shame - Lifetime Ls**",
        color=discord.Color.red(),
        timestamp=datetime.now(SYDNEY_TZ)
    )

    leaderboard_text = ""
    top_user_id = sorted_hall[0][0]

    for rank, (user_id, count) in enumerate(sorted_hall[:10], start=1):
        try:
            user = await bot.fetch_user(int(user_id))
            leaderboard_text += f"**{rank}.** {user.display_name} - **{count} Ls**\n"

            # Set top loser thumbnail
            if user_id == top_user_id:
                pfp = user.avatar.url if user.avatar else user.default_avatar.url
                embed.set_thumbnail(url=pfp)

        except (discord.NotFound, ValueError):
            leaderboard_text += f"**{rank}.** Unknown User ({user_id}) - **{count} Ls**\n"

    embed.description = leaderboard_text
    await ctx.send(embed=embed)

@bot.command()
async def bet(ctx, target: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send("You must bet a positive amount!")
        return
    
    points = load_json(points_FILE)
    user_id = str(ctx.author.id)
    target_id = str(target.id)
    
    if points.get(user_id, 0) < amount:
        await ctx.send("You don't have enough points to bet!")
        return
    
    bets_data = load_json(bets_FILE)
    if user_id not in bets_data:
        bets_data[user_id] = {"bet_on": target_id, "amount": amount}
    else:
        await ctx.send("You've already placed a bet!")
        return
    
    save_json(bets_FILE, bets_data)
    await ctx.send(f"{ctx.author.mention} bet **{amount} points** on {target.mention} being the last to leave!")
    
@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="📖 Watcher Bot Help Menu",
        description="Here's a list of available commands:",
        color=discord.Color.blurple(),
        timestamp=datetime.now(SYDNEY_TZ)
    )

    embed.add_field(name="`~vcleaderboard` / `~vc` / `~vclb`", value="Shows top 10 users by VC time.", inline=False)
    embed.add_field(name="`~pointsleaderboard` / `~points` / `~pl`", value="Shows top 10 users by points.", inline=False)
    embed.add_field(name="`~loserboard` / `~lb`", value="Shows this month's biggest losers.", inline=False)
    embed.add_field(name="`~hallofshame` / `~hs`", value="Shows lifetime Ls (all-time biggest losers).", inline=False)
    embed.add_field(name="`~bet @user amount`", value="Bet points on who will be the last to leave VC.", inline=False)
    embed.add_field(name="`~stats [@user]` / `~mystats` / `~profile`", value="Check your or another user's detailed stats.", inline=False)
    embed.add_field(name="`~coinflip heads/tails amount`", value="50/50 bet to double your points.", inline=False)
    embed.add_field(name="`~roll @user amount`", value="1v1 duel: highest roll wins both bets.", inline=False)
    embed.add_field(name="`~slots amount`", value="Emoji slots: 3 match = 3x, 2 match = 2x, else lose.", inline=False)


    embed.set_footer(text="Use your Ls wisely... or bet on someone else's.")
    await ctx.send(embed=embed)

@bot.command(aliases=["profile", "mystats"])
async def stats(ctx, member: discord.Member = None):
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
        title=f"Stats for {member.display_name}",
        color=discord.Color.teal(),
        timestamp=datetime.now(SYDNEY_TZ)
    )
    
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)

    embed.add_field(name="Total VC Minutes", value=f"**{round(vc_minutes, 2)} minutes**", inline=True)
    embed.add_field(name="Points", value=f"**{round(user_points, 2)}**", inline=True)
    embed.add_field(name="Monthly Ls", value=f"**{monthly_ls}**", inline=True)
    embed.add_field(name="Lifetime Ls", value=f"**{lifetime_ls}**", inline=True)

    if bet_data:
        try:
            bet_target = await bot.fetch_user(int(bet_data['bet_on']))
            embed.add_field(name="Current Bet", value=f"{bet_data['amount']} points on {bet_target.display_name}", inline=False)
        except discord.NotFound:
            embed.add_field(name="Current Bet", value=f"{bet_data['amount']} points on Unknown User", inline=False)

    await ctx.send(embed=embed)

@bot.command(aliases=["cf"])
@commands.cooldown(1, 10, BucketType.user)
async def coinflip(ctx, choice:str, amount: int):
    choice = choice.lower()
    if choice not in ["heads", "tails"]:
        await ctx.send("Please choose `heads` or `tails`!")
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
        
@bot.command(aliases=["r"])
@commands.cooldown(1, 10, BucketType.user)
async def roll(ctx, opponent: discord.Member, amount: int):
    user1 = ctx.author
    user2 = opponent
    uid1, uid2 = str(user1.id), str(user2.id)

    if uid1 == uid2:
        await ctx.send("You can't duel yourself.")
        return

    if amount <= 0:
        await ctx.send("Bet must be greater than 0.")
        return

    points = load_json(points_FILE)
    if points.get(uid1, 0) < amount or points.get(uid2, 0) < amount:
        await ctx.send("Both players must have enough points to duel.")
        return

    challenge_msg = await ctx.send(f"{user2.mention}, do you accept a **{amount} point** duel with {user1.mention}? React ✅ to accept within 30 seconds.")

    await challenge_msg.add_reaction("✅")

    def check(reaction, user):
        return (
            user == user2 and
            str(reaction.emoji) == "✅" and
            reaction.message.id == challenge_msg.id
        )

    try:
        await bot.wait_for("reaction_add", timeout=30.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send(f"{user2.display_name} didn’t accept the duel in time.")
        return

    roll1 = random.randint(1, 100)
    roll2 = random.randint(1, 100)

    result = f"{user1.display_name} rolled **{roll1}**\n{user2.display_name} rolled **{roll2}**\n"

    if roll1 > roll2:
        points[uid1] += amount
        points[uid2] -= amount
        result += f"🎉 {user1.mention} wins **{amount} points**!"
    elif roll2 > roll1:
        points[uid1] -= amount
        points[uid2] += amount
        result += f"🎉 {user2.mention} wins **{amount} points**!"
    else:
        result += "🤝 It's a tie! No points lost."

    save_json(points_FILE, points)
    await ctx.send(result)

@bot.command()
@commands.cooldown(1, 10, BucketType.user)
async def slots(ctx, amount: int):
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
        embed.add_field(name="JACKPOT!", value=f"You won **{win_amount} points**!", inline=False)
    elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
        win_amount = amount * 2
        points[user_id] += win_amount
        embed.add_field(name="Nice!", value=f"You matched 2 and won **{win_amount} points**!", inline=False)
    else:
        points[user_id] -= amount
        embed.add_field(name="Better luck next time!", value=f"You lost **{amount} points**.", inline=False)

    save_json(points_FILE, points)
    await ctx.send(embed=embed)

@tasks.loop(hours=720)
async def monthly_reset_task():
    loserboard_data = load_json(loserboard_FILE)
    loserboard = loserboard_data.get("loserboard", {})
    if not loserboard:
        return

    sorted_loserboard = sorted(loserboard.items(), key=lambda x: x[1], reverse=True)
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if not log_channel:
        return

    top_loser_id = sorted_loserboard[0][0]
    loser_count = loserboard.get(top_loser_id, 0)

    try:
        top_user = await bot.fetch_user(int(top_loser_id))
        top_display_name = top_user.display_name
        top_pfp = top_user.avatar.url if top_user.avatar else top_user.default_avatar.url
    except discord.NotFound:
        top_display_name = f"Unknown User ({top_loser_id})"
        top_pfp = None

    embed = discord.Embed(
        title="**BIGGEST LOSER OF THE MONTH!**",
        color=discord.Color.red(),
        timestamp=datetime.now(SYDNEY_TZ)
    )
    embed.description = f"**{top_display_name}** took **{loser_count} Ls** this month!"
    if top_pfp:
        embed.set_thumbnail(url=top_pfp)
    
    await log_channel.send(embed=embed)
    loserboard_data["loserboard"] = {}
    save_json(loserboard_FILE, loserboard_data)

@bot.command()
@commands.cooldown(1, 30, commands.BucketType.user)
async def summon(ctx, target: discord.Member):
    summons = load_json(summons_FILE)
    
    if target.bot:
        await ctx.send("You cannot summon bots, mere mortal.")
        return

    if target.voice and target.voice.channel:
        await ctx.send(f"{target.display_name} is already in a voice channel! You must summon someone who's lost in the void.")
        return

    creepy_messages = summons

    if not creepy_messages:
        await ctx.send("No summon messages found. The spirits are speechless.")
        return

    try:
        await target.send(random.choice(creepy_messages))
        await ctx.send(f"🔔 {target.mention} has been summoned. Let’s see if they answer the call...")
    except discord.Forbidden:
        await ctx.send(f"I tried to summon {target.display_name}, but their DMs are closed. The void is silent... 😔")

# @bot.command()
# @commands.has_permissions(administrator=True)
# async def startbet(ctx, *, question: str):
#     bets = load_json(bets_FILE)

#     if "active_bet" in bets and not bets["active_bet"].get("resolved", False):
#         await ctx.send("A bet is already active! Resolve it first.")
#         return

#     bets["active_bet"] = {
#         "question": question,
#         "creator": str(ctx.author.id),
#         "bets": {
#             "yes": {},
#             "no": {}
#         },
#         "resolved": False,
#         "result": None
#     }

#     save_json(bets_FILE, bets)
#     await ctx.send(f"🧠 **New Bet Started!**\n> {question}\nUse `~placebet yes|no amount` to join.")

# @bot.command()
# async def placebet(ctx, option: str, amount: int):
#     user_id = str(ctx.author.id)
#     option = option.lower()
#     points = load_json(points_FILE)
#     bets = load_json(bets_FILE)

#     if option not in ["yes", "no"]:
#         await ctx.send("Bet option must be `yes` or `no`.")
#         return

#     if "active_bet" not in bets or bets["active_bet"]["resolved"]:
#         await ctx.send("There is no active bet right now.")
#         return

#     if amount <= 0:
#         await ctx.send("You must bet more than 0 points.")
#         return

#     if points.get(user_id, 0) < amount:
#         await ctx.send("You don't have enough points!")
#         return

#     active_bet = bets["active_bet"]

#     if user_id in active_bet["bets"]["yes"] or user_id in active_bet["bets"]["no"]:
#         await ctx.send("You've already placed a bet!")
#         return

#     # Deduct points and place bet
#     points[user_id] -= amount
#     active_bet["bets"][option][user_id] = amount

#     save_json(points_FILE, points)
#     save_json(bets_FILE, bets)

#     await ctx.send(f"{ctx.author.mention} bet **{amount} points** on **{option.upper()}**.")

# @bot.command()
# @commands.has_permissions(administrator=True)
# async def resolvebet(ctx, winning_option: str):
#     winning_option = winning_option.lower()
#     if winning_option not in ["yes", "no"]:
#         await ctx.send("Result must be `yes` or `no`.")
#         return

#     bets = load_json(bets_FILE)
#     points = load_json(points_FILE)

#     if "active_bet" not in bets or bets["active_bet"]["resolved"]:
#         await ctx.send("No active bet to resolve.")
#         return

#     bet = bets["active_bet"]
#     winners = bet["bets"][winning_option]
#     losers = bet["bets"]["no" if winning_option == "yes" else "yes"]

#     total_pot = sum(winners.values()) + sum(losers.values())
#     total_winner_bet = sum(winners.values())

#     if not winners:
#         await ctx.send("Nobody bet on the winning side. The pot vanishes into the void 💀")
#         bet["resolved"] = True
#         bet["result"] = winning_option
#         save_json(bets_FILE, bets)
#         return

#     # Distribute winnings proportionally
#     for uid, amt in winners.items():
#         share = amt / total_winner_bet
#         payout = int(total_pot * share)
#         points[uid] = points.get(uid, 0) + payout

#     bet["resolved"] = True
#     bet["result"] = winning_option
#     save_json(bets_FILE, bets)
#     save_json(points_FILE, points)

#     await ctx.send(f"✅ **Bet Resolved!**\nWinning side: **{winning_option.upper()}**\nPot: **{total_pot} points** split among {len(winners)} winner(s).")

# @bot.command()
# async def activebet(ctx):
#     bets = load_json(bets_FILE)
#     if "active_bet" not in bets or bets["active_bet"]["resolved"]:
#         await ctx.send("No active bet at the moment.")
#         return

#     bet = bets["active_bet"]
#     embed = discord.Embed(
#         title="🎲 Active Bet",
#         description=f"**{bet['question']}**\n\nPlace your bet with `~placebet yes|no amount`",
#         color=discord.Color.blurple()
#     )
#     embed.add_field(name="Yes", value=str(len(bet['bets']['yes'])) + " user(s)", inline=True)
#     embed.add_field(name="No", value=str(len(bet['bets']['no'])) + " user(s)", inline=True)
#     await ctx.send(embed=embed)

async def enable_tracking():
    global tracking_active  
    while True:
        now = datetime.now(SYDNEY_TZ)
        print(f"Current Sydney Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

        start_time = datetime.combine(now.date(), time(22, 0), SYDNEY_TZ)
        end_time = datetime.combine(now.date() + timedelta(days=1), time(10, 0), SYDNEY_TZ)

        print(f"Tracking window: {start_time.strftime('%I:%M %p AEDT')} - {end_time.strftime('%I:%M %p AEDT')}")

        if start_time <= now < end_time:
            print("It's already past 10 PM but before 4 AM, waiting for users in multiple VCs.")
            for vc_id in VOICE_CHANNEL_IDS:
                tracking_active[vc_id] = False
        elif now >= end_time:
            print("It's past 4 AM, resetting for the next night...")
            for vc_id in VOICE_CHANNEL_IDS:
                tracking_active[vc_id] = False

        else:
            wait_time = (start_time - now).total_seconds()
            print(f"Waiting {wait_time} seconds until 10 PM AEDT to start tracking...")
            await asyncio.sleep(wait_time)

        wait_time = (end_time - datetime.now(SYDNEY_TZ)).total_seconds()
        print(f"Tracking active... Will stop in {wait_time} seconds (at 4 AM AEDT)")
        await asyncio.sleep(wait_time)

        for vc_id in VOICE_CHANNEL_IDS:
            tracking_active[vc_id] = False
        print("Tracking ended at 4 AM AEDT. Resetting for the next night.")

@tasks.loop(hours=24)
async def backup_json_files():
    now = datetime.now(SYDNEY_TZ)
    timestamp = now.strftime("%Y-%m-%d_%H-%M")

    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)

    files_to_backup = [
        loserboard_FILE,
        vc_stats_FILE,
        points_FILE,
        hallofshame_FILE,
        bets_FILE,
        roasts_FILE
    ]

    for file in files_to_backup:
        if os.path.exists(file):
            base = os.path.basename(file)
            backup_path = os.path.join(backup_dir, f"{timestamp}_{base}")
            with open(file, "r") as original, open(backup_path, "w") as backup:
                backup.write(original.read())

    print(f"[BACKUP] JSON files backed up at {timestamp}")

with open('tokenWatcher.txt', 'r') as file:
    token = file.read().strip()

bot.run(token)
