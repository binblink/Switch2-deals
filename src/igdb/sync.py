import logging
from db.connection import get_connection, release_connection
from .client import IGDBClient

logger = logging.getLogger(__name__)

def sync_games():
    client = IGDBClient()
    games = client.get_switch2_games()
    logger.info(f"Nombre de jeux trouvés : {len(games)}")
    conn = get_connection()
    insert_games_to_db(games, conn)


def insert_games_to_db(games, conn):
    try:
        with conn.cursor() as cur:
            for game in games:
                cur.execute("""
                    INSERT INTO games (igdb_id, first_release_date, title, igdb_slug)
                    VALUES (%s, to_timestamp(%s), %s, %s)
                    ON CONFLICT (igdb_id) DO UPDATE SET
                        first_release_date = EXCLUDED.first_release_date,
                        title = EXCLUDED.title,
                        igdb_slug = EXCLUDED.igdb_slug
                """, (game["id"], game.get("first_release_date"), game["name"], game.get("slug")))
        conn.commit()
    except Exception as e:
        logger.error(f"Error inserting games into DB: {e}")
        conn.rollback()
        raise
    finally:
        release_connection(conn)