import logging
from igdb.client import IGDBClient

logging.basicConfig(level=logging.INFO)

client = IGDBClient()
games = client.get_switch2_games()
ids = [g["id"] for g in games]
print(sorted(ids))
print(f"250925 in ids: {250925 in ids}")