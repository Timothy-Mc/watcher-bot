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
intents.message_content = True

bot = commands.Bot(command_prefix="~", intents=intents)

last_person_to_leave = {vc_id: None for vc_id in VOICE_CHANNEL_IDS}
tracking_active = {vc_id: False for vc_id in VOICE_CHANNEL_IDS}

loserboard_FILE = "loserboard.json"

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

def load_loserboard():
    try:
        with open(loserboard_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_loserboard(loserboard):
    with open(loserboard_FILE, "w") as f:
        json.dump(loserboard, f, indent=4)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.loop.create_task(enable_tracking())
    weekly_loserboard_task.start()
    monthly_reset_task.start()

@bot.command()
async def loserboard(ctx):

    loserboard_data = load_loserboard()
    loserboard = loserboard_data.get("loserboard", {})


    if not loserboard:
        embed = discord.Embed(
            title="**Biggest Losers loserboard**",
            description="No losers recorded yet!",
            color=discord.Color.gold(),
            timestamp=datetime.now(SYDNEY_TZ)
        )
        embed.set_footer(text="Who will take the first L?")
        await ctx.send(embed=embed)
        return
    
    sorted_loserboard = sorted(loserboard.items(), key=lambda x: x[1], reverse=True)

    embed = discord.Embed(
        title="**Biggest Losers loserboard**",
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

@tasks.loop(hours=168)
async def weekly_loserboard_task():
    loserboard_data = load_loserboard()
    loserboard = loserboard_data.get("loserboard", {})

    if not loserboard:
        return

    sorted_loserboard = sorted(loserboard.items(), key=lambda x: x[1], reverse=True)
    log_channel = bot.get_channel(LOG_CHANNEL_ID)

    if not log_channel:
        print("ERROR: Log channel not found!")
        return

    embed = discord.Embed(
        title="**Weekly Biggest Loser loserboard!**",
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

    embed.set_footer(text="Who will take the L next?")

    await log_channel.send(embed=embed)


@tasks.loop(hours=720)
async def monthly_reset_task():
    loserboard_data = load_loserboard()
    loserboard = loserboard_data.get("loserboard", {})

    if not loserboard:
        return

    sorted_loserboard = sorted(loserboard.items(), key=lambda x: x[1], reverse=True)
    log_channel = bot.get_channel(LOG_CHANNEL_ID)

    if not log_channel:
        print("ERROR: Log channel not found!")
        return

    if not sorted_loserboard:
        print("No valid loserboard data for monthly reset.")
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

    loserboard_text = ""

    for rank, (user_id, count) in enumerate(sorted_loserboard[:10], start=1):
        try:
            user = await bot.fetch_user(int(user_id))
            loserboard_text += f"**{rank}.** {user.display_name} - **{count} Ls**\n"
        except discord.NotFound:
            loserboard_text += f"**{rank}.** Unknown User ({user_id}) - **{count} Ls**\n"

    embed.description = f"**{top_display_name}** took **{loser_count} Ls** this month!\n\n{loserboard_text}"

    if top_pfp:
        embed.set_thumbnail(url=top_pfp)

    embed.set_footer(text="Try again next month... if you dare.")

    await log_channel.send(embed=embed)

    if datetime.now().day == 1:
        print("Resetting loserboard for a new month!")
        loserboard_data["loserboard"] = {}
        save_loserboard(loserboard_data)

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
                
                loserboard_data = load_loserboard()
                loserboard = loserboard_data.get("loserboard", {})

                user_id = str(member.id)
                loserboard[user_id] = loserboard.get(user_id, 0) + 1
                loserboard_data["loserboard"] = loserboard

                save_loserboard(loserboard_data)

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

with open('tokenWatcher.txt', 'r') as file:
    token = file.read().strip()

bot.run(token)
