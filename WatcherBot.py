import json
import discord
import asyncio
import random
import os
from discord.ext import commands, tasks
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

loserboard_FILE = "loserboard.json"
vc_stats_FILE = "vc_stats.json"
points_FILE = "points.json"
hallofshame_FILE = "hallofshame.json"
bets_FILE = "bets.json"
roasts_FILE = "roasts.json"

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
    monthly_reset_task.start()

@bot.event
async def on_voice_state_update(member, before, after):
    now = datetime.now(SYDNEY_TZ)
    vc_stats = load_json(vc_stats_FILE)
    points = load_json(points_FILE)
    loserboard_data = load_json(loserboard_FILE)
    hallofshame_data = load_json(hallofshame_FILE)
    user_id = str(member.id)
    
    for vc_id in VOICE_CHANNEL_IDS:
        voice_channel = bot.get_channel(vc_id)
        if not voice_channel:
            continue

        real_users_in_vc = [m for m in voice_channel.members if not m.bot]
        num_real_users = len(real_users_in_vc)

        if num_real_users > 2:
            tracking_active[vc_id] = True

        if tracking_active[vc_id] and before.channel and before.channel.id == vc_id and not after.channel:
            if num_real_users == 0:
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
                        description=f"{member.mention} just took the **BIGGEST L** in **{voice_channel.name}**! {roast_message}",
                        color=discord.Color.red(),
                        timestamp=datetime.now(SYDNEY_TZ)
                    )
                    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
                    embed.set_footer(text="The peasant of the day.")

                    await asyncio.sleep(10)
                    await log_channel.send(embed=embed)

                last_person_to_leave[vc_id] = None
                tracking_active[vc_id] = False

    if after.channel and after.channel.id in VOICE_CHANNEL_IDS:
        user_join_times[user_id] = now
    
    if before.channel and before.channel.id in VOICE_CHANNEL_IDS and not after.channel:
        if user_id in user_join_times:
            time_spent = (now - user_join_times[user_id]).total_seconds() / 60
            vc_stats[user_id] = vc_stats.get(user_id, 0) + round(time_spent, 2)
            points[user_id] = points.get(user_id, 0) + round(time_spent, 2)
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

    embed.set_footer(text="Use your Ls wisely... or bet on someone else's.")
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

with open('tokenWatcher.txt', 'r') as file:
    token = file.read().strip()

bot.run(token)