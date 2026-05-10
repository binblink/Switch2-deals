import logging
from igdb.client import IGDBClient

logging.basicConfig(level=logging.INFO)

client = IGDBClient()
games = client.get_switch2_games()
result = client.request("games", 'fields id, name; where platforms = (508) & game_type != (1, 7); sort id asc; limit 500;')
ids = [g["id"] for g in result]
print(f"Total batch: {len(result)}")
print(f"Pragmata in batch: {134612 in ids}")