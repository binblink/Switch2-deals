import logging
# from igdb.client import IGDBClient

# logging.basicConfig(level=logging.INFO)

# client = IGDBClient()
# games = client.get_switch2_games()
# ids = [g["id"] for g in games]
# print(sorted(ids))
# print(f"250925 in ids: {250925 in ids}")

import requests
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")

key = os.getenv("RAWG_API_KEY")

# Trouver l'ID de la plateforme Switch 2
res = requests.get(f"https://api.rawg.io/api/platforms?key={key}&page_size=100")
data = res.json()
for p in data["results"]:
    print(p["id"], p["name"])