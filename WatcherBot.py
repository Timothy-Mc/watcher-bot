import json
import discord
import asyncio
import random
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

bot = commands.Bot(command_prefix="~", intents=intents)

last_person_to_leave = {vc_id: None for vc_id in VOICE_CHANNEL_IDS}
tracking_active = {vc_id: False for vc_id in VOICE_CHANNEL_IDS}

LEADERBOARD_FILE = "loser_leaderboard.json"

ROAST_MESSAGES = [
    "Biggest quitter of the night. Congrats.",
    "You were the last one in, but not the strongest.",
    "VC just got 100% cooler now that you're gone.",
    "No stamina. No willpower. Just disappointment.",
    "Legend has it, they're still recovering from that L.",
    "Guess you couldn’t handle the grind. Shame.",
    "You're like a cloud, when you disappear, it's a beautiful day.",
    "You're proof that even evolution takes a break sometimes.",
    "I'd agree with you, but then we’d both be wrong.",
    "Your jokes are like your WiFi—weak and barely connecting.",
    "You're the reason we need warning labels on shampoo bottles.",
    "If I had a dollar for every smart thing you said, I'd be broke.",
    "You're like a penny: two-faced, worthless, and nobody wants you.",
    "Your personality is like a black hole—sucks the life out of everything around it.",
    "You're about as useful as a screen door on a submarine.",
    "The only thing faster than your internet is how quickly people regret talking to you.",
    "Your comebacks are slower than a Windows XP startup.",
    "You're like a software update—nobody wants you, but we’re forced to deal with you.",
    "You bring everyone so much joy… when you leave the VC.",
    "Your presence is like a 404 error—unwanted and useless.",
    "Your voice is like a mosquito at 2 AM—annoying and impossible to ignore.",
    "You're the human equivalent of a lag spike.",
    "Your life is like your KD ratio—just pure disappointment.",
    "Your brain must be a rented server—barely running and always lagging.",
    "You're the reason Discord has a block feature.",
    "If ignorance was a currency, you’d be a billionaire."
]

def load_leaderboard():
    try:
        with open(LEADERBOARD_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_leaderboard(leaderboard):
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(leaderboard, f, indent=4)

@bot.command(name="loserboard")
async def loserboard(ctx):
    print("!loserboard command triggered")

    leaderboard_data = load_leaderboard()
    leaderboard = leaderboard_data.get("leaderboard", {})

    print("Loaded leaderboard data:", leaderboard)

    if not leaderboard:
        embed = discord.Embed(
            title="**Biggest Losers Leaderboard**",
            description="No losers recorded yet!",
            color=discord.Color.gold(),
            timestamp=datetime.now(SYDNEY_TZ)
        )
        embed.set_footer(text="Who will take the first L?")
        await ctx.send(embed=embed)
        return

    sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)

    embed = discord.Embed(
        title="**Biggest Losers Leaderboard**",
        color=discord.Color.gold(),
        timestamp=datetime.now(SYDNEY_TZ)
    )

    leaderboard_text = ""
    user_avatars = {}

    for rank, (user_id, count) in enumerate(sorted_leaderboard[:10], start=1):
        try:
            user = await bot.fetch_user(int(user_id))
            pfp_url = user.avatar.url if user.avatar else user.default_avatar.url
            user_avatars[rank] = pfp_url

            leaderboard_text += f"**{rank}.** [{user.display_name}](https://discord.com/users/{user_id}) - **{count} Ls**\n"

            embed.set_thumbnail(url=user_avatars[1]) if rank == 1 else None

        except discord.NotFound:
            leaderboard_text += f"**{rank}.** Unknown User ({user_id}) - **{count} Ls**\n"

    embed.description = leaderboard_text

    if sorted_leaderboard:
        top_user_id = sorted_leaderboard[0][0]
        try:
            top_user = await bot.fetch_user(int(top_user_id))
            top_pfp = top_user.avatar.url if top_user.avatar else top_user.default_avatar.url
            embed.set_thumbnail(url=top_pfp)
        except discord.NotFound:
            pass

    embed.set_footer(text="Who will take the next L?")

    await ctx.send(embed=embed)

@tasks.loop(hours=168)
async def weekly_leaderboard_task():
    leaderboard_data = load_leaderboard()
    leaderboard = leaderboard_data.get("leaderboard", {})

    if not leaderboard:
        return

    sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
    log_channel = bot.get_channel(LOG_CHANNEL_ID)

    if not log_channel:
        print("ERROR: Log channel not found!")
        return

    embed = discord.Embed(
        title="**Weekly Biggest Loser Leaderboard!**",
        color=discord.Color.gold(),
        timestamp=datetime.now(SYDNEY_TZ)
    )

    leaderboard_text = ""
    user_avatars = {}

    for rank, (user_id, count) in enumerate(sorted_leaderboard[:10], start=1):
        try:
            user = await bot.fetch_user(int(user_id))
            pfp_url = user.avatar.url if user.avatar else user.default_avatar.url
            user_avatars[rank] = pfp_url

            leaderboard_text += f"**{rank}.** [{user.display_name}](https://discord.com/users/{user_id}) - **{count} Ls**\n"

        except discord.NotFound:
            leaderboard_text += f"**{rank}.** Unknown User ({user_id}) - **{count} Ls**\n"

    embed.description = leaderboard_text

    if sorted_leaderboard:
        top_user_id = sorted_leaderboard[0][0]
        try:
            top_user = await bot.fetch_user(int(top_user_id))
            top_pfp = top_user.avatar.url if top_user.avatar else top_user.default_avatar.url
            embed.set_thumbnail(url=top_pfp)
        except discord.NotFound:
            pass

    embed.set_footer(text="Who will take the L next?")

    await log_channel.send(embed=embed)

@tasks.loop(hours=720)
async def monthly_reset_task():
    leaderboard_data = load_leaderboard()
    leaderboard = leaderboard_data.get("leaderboard", {})

    if not leaderboard:
        return

    sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
    log_channel = bot.get_channel(LOG_CHANNEL_ID)

    if not log_channel:
        print("ERROR: Log channel not found!")
        return

    top_loser_id = sorted_leaderboard[0][0]
    loser_count = leaderboard[top_loser_id] if top_loser_id else 0

    embed = discord.Embed(
        title="**BIGGEST LOSER OF THE MONTH!**",
        color=discord.Color.red(),
        timestamp=datetime.now(SYDNEY_TZ)
    )

    leaderboard_text = ""
    user_avatars = {}

    for rank, (user_id, count) in enumerate(sorted_leaderboard[:10], start=1):
        try:
            user = await bot.fetch_user(int(user_id))
            pfp_url = user.avatar.url if user.avatar else user.default_avatar.url
            user_avatars[rank] = pfp_url

            leaderboard_text += f"**{rank}.** [{user.display_name}](https://discord.com/users/{user_id}) - **{count} Ls**\n"

        except discord.NotFound:
            leaderboard_text += f"**{rank}.** Unknown User ({user_id}) - **{count} Ls**\n"

    embed.description = leaderboard_text

    if top_loser_id:
        try:
            top_user = await bot.fetch_user(int(top_loser_id))
            top_pfp = top_user.avatar.url if top_user.avatar else top_user.default_avatar.url
            embed.set_thumbnail(url=top_pfp)  # Large profile picture
            embed.description = f"**{top_user.display_name}** took **{loser_count} Ls** this month!\n\n{leaderboard_text}"
        except discord.NotFound:
            embed.description = f"<@{top_loser_id}> took **{loser_count} Ls** this month!\n\n{leaderboard_text}"

    embed.set_footer(text="Try again next month... if you dare.")

    await log_channel.send(embed=embed)

    # Reset leaderboard after posting
    leaderboard_data["leaderboard"] = {}
    save_leaderboard(leaderboard_data)

@bot.event
async def on_voice_state_update(member, before, after):
    now = datetime.now(SYDNEY_TZ)

    for vc_id in VOICE_CHANNEL_IDS:
        voice_channel = bot.get_channel(vc_id)
        if not voice_channel:
            print(f"ERROR: Voice channel {vc_id} not found!")
            continue

        real_users_in_vc = [m for m in voice_channel.members if not m.bot]
        num_real_users = len(real_users_in_vc)

        if num_real_users >= 2:
            tracking_active[vc_id] = True

        if tracking_active[vc_id] and before.channel and before.channel.id == vc_id and not after.channel:
            print(f"{member.display_name} left {voice_channel.name}")

            if num_real_users == 0:
                last_person_to_leave[vc_id] = member

                if last_person_to_leave[vc_id].bot:
                    return
                
                leaderboard_data = load_leaderboard()
                leaderboard = leaderboard_data.get("leaderboard", {})

                user_id = str(member.id)
                leaderboard[user_id] = leaderboard.get(user_id, 0) + 1
                leaderboard_data["leaderboard"] = leaderboard

                save_leaderboard(leaderboard_data)

                log_channel = bot.get_channel(LOG_CHANNEL_ID)
                if log_channel:
                    roast_message = random.choice(ROAST_MESSAGES)

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

async def enable_tracking():
    global tracking_active  
    while True:
        now = datetime.now(SYDNEY_TZ)
        print(f"Current Sydney Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

        start_time = datetime.combine(now.date(), time(22, 0), SYDNEY_TZ)
        end_time = datetime.combine(now.date() + timedelta(days=1), time(22, 0), SYDNEY_TZ)

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

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.loop.create_task(enable_tracking())
    weekly_leaderboard_task.start()
    monthly_reset_task.start()

with open('tokenWatcher.txt', 'r') as file:
    token = file.read().strip()

bot.run(token)
