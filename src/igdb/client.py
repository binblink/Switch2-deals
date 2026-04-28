from dotenv import load_dotenv
from pathlib import Path
import os
import requests
import time
import logging

load_dotenv(Path(__file__).parent.parent.parent / ".env")
logger = logging.getLogger(__name__)
PLATFORM_ID = 508 

class IGDBClient:
    def __init__(self):
        self._client_id = os.getenv("IGDB_CLIENT_ID")
        self._client_secret = os.getenv("IGDB_CLIENT_SECRET")
        self._token = None
        self._token_expires_at = 0

    def _get_token(self):
        # Si le token est encore valide, on le réutilise
        if self._token and time.time() < self._token_expires_at:
            return self._token
        
        # Sinon on en demande un nouveau
        self._token, self._token_expires_at = self._fetch_new_token()
        return self._token

    def _fetch_new_token(self):
        url = "https://id.twitch.tv/oauth2/token"
        
        # Appel POST à l'API Twitch OAuth
        response = requests.post(url, params={
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "grant_type": "client_credentials"
        })

        # Vérifie que la requête a réussi
        response.raise_for_status()

        # Retourne (token, expires_at)
        data = response.json()
        return data["access_token"], time.time() + data["expires_in"] - 60

    # Exemple de méthode pour faire une requête à l'API IGDB
    def request(self, endpoint, body):
        token = self._get_token()
        headers = {
            "Client-ID": self._client_id,
            "Authorization": f"Bearer {token}"
        }
        url = f"https://api.igdb.com/v4/{endpoint}"
        response = requests.post(url, headers=headers, data=body)

        if not response.ok:
            logger.error(f"IGDB error {response.status_code} on {endpoint}: {response.text}")

        response.raise_for_status()
        return response.json()
    
    def get_switch2_games(self):
        all_games = []
        last_id = 0
        limit = 500

        while True:
            query = f"""
                fields id, name, slug, first_release_date;
                where platforms = {PLATFORM_ID}
                    & id > {last_id};
                sort id asc;
                limit {limit};
            """

            batch = self.request("games", query)

            if not batch:
                break

            all_games.extend(batch)

            last_id = batch[-1]["id"]

            if len(batch) < limit:
                break

        return all_games