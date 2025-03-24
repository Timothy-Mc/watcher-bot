from datetime import datetime
from utils.constants import SYDNEY_TZ

def now_sydney():
    return datetime.now(SYDNEY_TZ)

def format_sydney_time(dt=None):
    dt = dt or now_sydney()
    return dt.strftime("%Y-%m-%d %H:%M:%S %Z")