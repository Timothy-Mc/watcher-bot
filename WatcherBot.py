import discord
import asyncio
import random
from discord.ext import commands
from datetime import datetime, time, timedelta
import pytz

SYDNEY_TZ = pytz.timezone('Australia/Sydney')

# Channel IDs (Replace with actual IDs)
VOICE_CHANNEL_ID = [851038508810240015, 910091498358464572, 1342051891739230279, 1010130915416084520, 942761000334159882, 877137739328413736, 990191271060602920]
LOG_CHANNEL_ID = 975760066659639417

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

last_person_to_leave = None
tracking_active = False


ROAST_MESSAGES = [
    "Biggest quitter of the night. Congrats. 🎉",
    "You were the last one in, but not the strongest. 😂",
    "VC just got 100% cooler now that you're gone.",
    "No stamina. No willpower. Just disappointment.",
    "Legend has it, they're still recovering from that L.",
    "Guess you couldn’t handle the grind. Shame.",
]

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    bot.loop.create_task(enable_tracking())

@bot.event
async def on_voice_state_update(member, before, after):
    global last_person_to_leave, tracking_active

    now = datetime.now(SYDNEY_TZ)
    voice_channel = bot.get_channel(VOICE_CHANNEL_ID)

    if not voice_channel:
        print("❌ ERROR: Voice channel not found!")
        return

    real_users_in_vc = [m for m in voice_channel.members if not m.bot]
    num_real_users = len(real_users_in_vc)

    print(f"👥 Current Real Users in VC (Ignoring Bots): {num_real_users}")

    if num_real_users >= 2:
        tracking_active = True
        print("✅ Tracking has started, as there are at least 2 real people in VC.")

    if tracking_active and before.channel and before.channel.id == VOICE_CHANNEL_ID and not after.channel:
        print(f"👀 {member.display_name} left {voice_channel.name}")

        if num_real_users == 0:
            last_person_to_leave = member

            if last_person_to_leave.bot:
                print(f"🤖 {last_person_to_leave.display_name} is a bot. Not announcing.")
                return

            print(f"🔥 {member.display_name} is the last recorded person to leave!")

            log_channel = bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                roast_message = random.choice(ROAST_MESSAGES)

                embed = discord.Embed(
                    title="🎤 **Tonight's BIGGEST LOSER!**",
                    description=f"{member.mention} just took the **BIGGEST L** of the night! {roast_message}",
                    color=discord.Color.red(),
                    timestamp=datetime.now(SYDNEY_TZ)
                )
                embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
                embed.add_field(name="🏆 **Final VC Survivor**", value=f"**{member.display_name}** (but not for long)", inline=False)
                embed.add_field(name="⌛ **Time of Defeat**", value=f"{datetime.now(SYDNEY_TZ).strftime('%I:%M %p AEDT')}", inline=False)
                embed.set_footer(text="Try again tomorrow... if you dare.")

                await log_channel.send(embed=embed)

            last_person_to_leave = None
            tracking_active = False

async def enable_tracking():
    """ Enables tracking every night at 10 PM AEDT and stops at 4 AM """
    global tracking_active  
    while True:
        now = datetime.now(SYDNEY_TZ)
        print(f"🕒 Current Sydney Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

        # Set the tracking window (10 PM - 4 AM)
        start_time = datetime.combine(now.date(), time(22, 0), SYDNEY_TZ)  # 10 PM AEDT
        end_time = datetime.combine(now.date() + timedelta(days=1), time(4, 0), SYDNEY_TZ)  # 4 AM AEDT

        print(f"🎯 Target start time (10 PM AEDT): {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Target end time (4 AM AEDT): {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

        if start_time <= now < end_time:
            print("🚀 It's already past 10 PM but before 4 AM, waiting for at least 2 real users to join VC.")
            tracking_active = False
        elif now >= end_time:
            print("🛑 It's past 4 AM, waiting for the next tracking cycle...")
            tracking_active = False

        else:
            wait_time = (start_time - now).total_seconds()
            print(f"⏳ Waiting {wait_time} seconds until 10 PM AEDT to start tracking...")
            await asyncio.sleep(wait_time)

        wait_time = (end_time - datetime.now(SYDNEY_TZ)).total_seconds()
        print(f"⏳ Tracking active... Will stop in {wait_time} seconds (at 4 AM AEDT)")
        await asyncio.sleep(wait_time)

        tracking_active = False
        print("🛑 Tracking ended at 4 AM AEDT. Resetting for the next night.")

with open('tokenWatcher.txt', 'r') as file:
    token = file.read().strip()

bot.run(token)
