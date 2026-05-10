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
                    WHERE g.is_excluded = FALSE
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

def upsert_product(conn, game_id, asin):
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE products SET is_available = FALSE 
            WHERE game_id = %s AND asin != %s
        """, (game_id, asin))
        cur.execute("""
            INSERT INTO products (game_id, asin, is_manual, is_available)
            VALUES (%s, %s, TRUE, TRUE)
            ON CONFLICT (asin) DO UPDATE SET
                game_id = EXCLUDED.game_id,
                is_manual = TRUE,
                is_available = TRUE
        """, (game_id, asin))
    conn.commit()

def update_product_price_and_image(conn, asin, price, image_url):
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE products SET image_url = %s
            WHERE asin = %s
        """, (image_url, asin))
        cur.execute("SELECT id FROM products WHERE asin = %s", (asin,))
        product_id = cur.fetchone()[0]
        cur.execute("""
            INSERT INTO prices (product_id, price, currency, source)
            VALUES (%s, %s, 'EUR', 'amazon')
            ON CONFLICT (product_id, DATE(scraped_at)) DO NOTHING
        """, (product_id, price))
    conn.commit()