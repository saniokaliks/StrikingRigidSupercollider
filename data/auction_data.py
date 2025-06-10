import json
import os

AUCTION_FILE = "data/auction.json"  # Шлях до файлу

def load_auction():
    if not os.path.exists(AUCTION_FILE):
        with open(AUCTION_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(AUCTION_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_auction(data):
    with open(AUCTION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ВАЖЛИВО: оголошення auction ПІСЛЯ функцій!
auction = load_auction()
