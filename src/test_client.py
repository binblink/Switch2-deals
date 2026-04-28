from igdb.client import IGDBClient

client = IGDBClient()
games = client.get_switch2_games()

print(f"Nombre de jeux trouvés : {len(games)}")
for game in games[:5]:  # affiche les 5 premiers
    print(game)