import json
import os
from pathlib import Path
from database import load_users, save_users
from data.auction_data import load_auction, save_auction

# Централізований файл користувачів
users = load_users()

# Централізований файл аукціонів
auction = load_auction()
