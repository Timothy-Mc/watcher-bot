import discord
import asyncio
import random
from discord.ext import commands
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

bot = commands.Bot(command_prefix="!", intents=intents)

last_person_to_leave = {vc_id: None for vc_id in VOICE_CHANNEL_IDS}
tracking_active = {vc_id: False for vc_id in VOICE_CHANNEL_IDS}


ROAST_MESSAGES = [
    "Biggest quitter of the night. Congrats.",
    "You were the last one in, but not the strongest.",
    "VC just got 100% cooler now that you're gone.",
    "No stamina. No willpower. Just disappointment.",
    "Legend has it, they're still recovering from that L.",
    "Guess you couldn’t handle the grind. Shame.",
]

@bot.event
async def on_voice_state_update(member, before, after):
    now = datetime.now(SYDNEY_TZ)

    for vc_id in VOICE_CHANNEL_IDS:
        voice_channel = bot.get_channel(vc_id)
        if not voice_channel:
            print(f"ERROR: Voice channel {vc_id} not found!")
            continue

        # Get only real users (ignore bots)
        real_users_in_vc = [m for m in voice_channel.members if not m.bot]
        num_real_users = len(real_users_in_vc)

        print(f"Current Real Users in {voice_channel.name} (Ignoring Bots): {num_real_users}")

        # Start tracking only if 2 or more real users are in VC
        if num_real_users >= 2:
            tracking_active[vc_id] = True
            print(f"Tracking started for {voice_channel.name}!")

        # If tracking is active and someone leaves
        if tracking_active[vc_id] and before.channel and before.channel.id == vc_id and not after.channel:
            print(f"{member.display_name} left {voice_channel.name}")

            # If VC is now empty (excluding bots), announce and reset
            if num_real_users == 0:
                last_person_to_leave[vc_id] = member

                # Ignore bots when selecting the "Biggest Loser"
                if last_person_to_leave[vc_id].bot:
                    print(f"{last_person_to_leave[vc_id].display_name} is a bot. Not announcing.")
                    return

                print(f"🔥 {member.display_name} was the last to leave {voice_channel.name}!")

                # Announce in log channel with a fun roast embed
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
                    embed.add_field(name="**Final VC Survivor**", value=f"**{member.display_name}** (but not for long)", inline=False)
                    embed.add_field(name="**Time of Defeat**", value=f"{datetime.now(SYDNEY_TZ).strftime('%I:%M %p AEDT')}", inline=False)
                    embed.set_footer(text="Try again tomorrow... if you dare.")

                    await log_channel.send(embed=embed)

                # Reset tracking for this VC
                last_person_to_leave[vc_id] = None
                tracking_active[vc_id] = False  # Stop tracking until 2 real users rejoin

async def enable_tracking():
    """ Enables tracking every night at 10 PM AEDT and stops at 4 AM """
    global tracking_active  
    while True:
        now = datetime.now(SYDNEY_TZ)  # Get current Sydney time
        print(f"Current Sydney Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

        # Set the tracking window (10 PM - 4 AM)
        start_time = datetime.combine(now.date(), time(22, 0), SYDNEY_TZ)  # 10 PM AEDT
        end_time = datetime.combine(now.date() + timedelta(days=1), time(4, 0), SYDNEY_TZ)  # 4 AM AEDT

        print(f"Tracking window: {start_time.strftime('%I:%M %p AEDT')} - {end_time.strftime('%I:%M %p AEDT')}")

        if start_time <= now < end_time:
            print("It's already past 10 PM but before 4 AM, waiting for users in multiple VCs.")
            for vc_id in VOICE_CHANNEL_IDS:
                tracking_active[vc_id] = False  # Wait for two real users per VC
        elif now >= end_time:
            print("It's past 4 AM, resetting for the next night...")
            for vc_id in VOICE_CHANNEL_IDS:
                tracking_active[vc_id] = False  # Reset tracking

        else:
            wait_time = (start_time - now).total_seconds()
            print(f"Waiting {wait_time} seconds until 10 PM AEDT to start tracking...")
            await asyncio.sleep(wait_time)

        wait_time = (end_time - datetime.now(SYDNEY_TZ)).total_seconds()
        print(f"Tracking active... Will stop in {wait_time} seconds (at 4 AM AEDT)")
        await asyncio.sleep(wait_time)

        # Stop tracking at 4 AM
        for vc_id in VOICE_CHANNEL_IDS:
            tracking_active[vc_id] = False
        print("Tracking ended at 4 AM AEDT. Resetting for the next night.")

with open('tokenWatcher.txt', 'r') as file:
    token = file.read().strip()

bot.run(token)
