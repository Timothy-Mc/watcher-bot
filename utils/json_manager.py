import json
import os
from utils.constants import config_FILE

def load_json(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# Log Channel Config
def get_log_channel_id():
    config = load_json(config_FILE)
    return config.get("log_channel_id")

def set_log_channel_id(channel_id):
    config = load_json(config_FILE)
    config["log_channel_id"] = channel_id
    save_json(config_FILE, config)