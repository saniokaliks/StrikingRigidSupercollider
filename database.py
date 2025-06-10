import json
from pathlib import Path

DB_PATH = Path("data/users.json")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def load_users():
    if DB_PATH.exists():
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users: dict):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)
