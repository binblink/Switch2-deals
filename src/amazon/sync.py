import logging
from amazon import scraper
from playwright.sync_api import sync_playwright
from db.connection import get_connection, release_connection
from db.queries import update_product_price_and_image
from amazon.scraper import get_price_and_image

logger = logging.getLogger(__name__)

def get_games_without_asin(conn):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT g.id, g.title 
                FROM games g
                LEFT JOIN products p ON p.game_id = g.id
                WHERE p.asin IS NULL
                    OR (p.is_manual = FALSE AND p.is_available = TRUE)
                    AND g.is_excluded = FALSE
            """)
            return cur.fetchall()
    except Exception as e:
        logger.error(f"Error fetching games without asin: {e}")
        conn.rollback()
        raise

def get_games_with_outdated_prices(conn):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.id, p.asin
                FROM products p
                LEFT JOIN prices pr ON pr.product_id = p.id 
                    AND pr.scraped_at::date = CURRENT_DATE
                WHERE p.is_available = true
                AND pr.id IS NULL
            """)
            return cur.fetchall()
    except Exception as e:
        logger.error(f"Error fetching games with outdated prices from DB: {e}")
        conn.rollback()
        raise

def set_asin_and_price(conn, game_id, asin, price, image_url):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO products (game_id, asin, image_url, product_type)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (asin) DO UPDATE SET
                        is_available = TRUE,
                        image_url = EXCLUDED.image_url
                    RETURNING id;
            """, (game_id, asin, image_url, "game"))
            # Récupérer l'ID du produit inséré
            product_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO prices (product_id, price, currency, source)
                VALUES (%s, %s, 'EUR', 'amazon')
                ON CONFLICT (product_id, DATE(scraped_at)) DO NOTHING;
            """, (product_id, price))
            conn.commit()
    except Exception as e:
        logger.error(f"Error setting ASIN and price in DB: {e}")
        conn.rollback()
        raise

def update_price(conn, product_id, price):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO prices (product_id, price, currency, source)
                VALUES (%s, %s, 'EUR', 'amazon')
                ON CONFLICT (product_id, DATE(scraped_at)) DO NOTHING;
            """, (product_id, price))
            conn.commit()
    except Exception as e:
        logger.error(f"Error updating price for product {product_id}: {e}")
        conn.rollback()
        raise

def sync_prices():
    conn = get_connection()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            games_without_asin = get_games_without_asin(conn)
            games_with_outdated_prices = get_games_with_outdated_prices(conn)

            for g in games_without_asin:
                logger.info(f"Recherche ASIN pour le jeu : {g[1]}")
                result = scraper.search_asin_and_price(page, g[1])
                if result:
                    asin = result[0]
                    price = result[1]
                    img = result[2]
                    logger.info(f"ASIN trouvé : {asin} pour le jeu {g[1]} avec un prix de {price} EUR")
                    set_asin_and_price(conn, g[0], asin, price, img)
            
            for g in games_with_outdated_prices:
                logger.info(f"Recherche de prix pour ASIN : {g[1]}")
                price = scraper.search_price(page, g[1])
                if price:
                    logger.info(f"Prix trouvé pour ASIN {g[1]}: {price} EUR")
                    update_price(conn, g[0], price)
    finally:
        release_connection(conn)

def refresh_product(conn, asin: str) -> bool:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        result = get_price_and_image(page, asin)

    if result:
        price, image_url = result
        update_product_price_and_image(conn, asin, price, image_url)
        return True
    else:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE products SET is_available = FALSE 
                WHERE asin = %s
            """, (asin,))
        conn.commit()
        return False