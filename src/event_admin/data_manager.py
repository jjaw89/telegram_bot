import sys
import os.path
sys.path.append("..")
from config.config import event_admins

def is_event_admin(user_id: int) -> bool:
    return user_id in event_admins

def save_events(context) -> None:
    # context.bot_data contains {"events": [...]}
    import json
    import os
    data_dir = os.path.join("data")
    data_file = os.path.join(data_dir, "events.json")
    data = {"events": context.bot_data.get("events", [])}
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_events(context) -> None:
    import json
    import os
    data_dir = os.path.join("data")
    data_file = os.path.join(data_dir, "events.json")
    with open(data_file, "r", encoding="utf-8") as f:
        context.bot_data = json.load(f)
