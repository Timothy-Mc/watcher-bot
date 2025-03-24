import pytz

SYDNEY_TZ = pytz.timezone('Australia/Sydney')

WATCHED_USERS = [
    353494340494163968,
    231001052856582145,
    220065649123131392
]

DATA_DIR = "data/"

vc_stats_FILE = f"{DATA_DIR}vc_stats.json"
points_FILE = f"{DATA_DIR}points.json"
loserboard_FILE = f"{DATA_DIR}loserboard.json"
hallofshame_FILE = f"{DATA_DIR}hallofshame.json"
bets_FILE = f"{DATA_DIR}bets.json"
roasts_FILE = f"{DATA_DIR}roasts.json"
summons_FILE = f"{DATA_DIR}summons.json"
config_FILE = f"{DATA_DIR}config.json"