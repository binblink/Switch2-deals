import logging
logger = logging.getLogger(__name__)

def get_games_from_db(conn):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                        g.id,
                        g.title,
                        g.igdb_slug,
                        p.asin,
                        p.image_url,
                        pr.price,
                        pr.scraped_at
                    FROM games g
                    LEFT JOIN products p ON p.game_id = g.id
                    LEFT JOIN prices pr ON pr.product_id = p.id
                        AND pr.scraped_at = (
                            SELECT MAX(scraped_at) 
                            FROM prices 
                            WHERE product_id = p.id
                        )
                    ORDER BY g.title ASC
                """)
            rows = cur.fetchall()
            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "igdb_slug": row[2],
                    "asin": row[3],
                    "image_url": row[4],
                    "price": float(row[5]) if row[5] else None,
                    "scraped_at": row[6].isoformat() if row[6] else None,
                    "trend": None
                }
                for row in rows
            ]
    except Exception as e:
        logger.error(f"Error getting games from DB: {e}")
        conn.rollback()
        raise