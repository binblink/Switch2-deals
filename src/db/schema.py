import psycopg2
 
 
def create_tables(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id          SERIAL PRIMARY KEY,
                igdb_id     INTEGER UNIQUE NOT NULL,
                title       TEXT NOT NULL,
                igdb_slug   TEXT,
                platform    TEXT DEFAULT 'switch2',
                first_release_date TIMESTAMP
            );
 
            CREATE TABLE IF NOT EXISTS products (
                id            SERIAL PRIMARY KEY,
                game_id       INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
                asin          TEXT UNIQUE,
                title_amazon  TEXT,
                image_url     TEXT,
                product_type  TEXT,
                is_available  BOOLEAN DEFAULT TRUE,
                is_manual     BOOLEAN DEFAULT FALSE,
                created_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW() 
            );  
 
            CREATE TABLE IF NOT EXISTS prices (
                id          SERIAL PRIMARY KEY,
                product_id  INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                price       NUMERIC(10,2) NOT NULL,
                currency    TEXT DEFAULT 'EUR',
                scraped_at  TIMESTAMP DEFAULT NOW(),
                source      TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_games_igdb_id ON games(igdb_id);
            CREATE INDEX IF NOT EXISTS idx_products_asin ON products(asin);
            CREATE INDEX IF NOT EXISTS idx_prices_product_id ON prices(product_id);
            CREATE INDEX IF NOT EXISTS idx_prices_scraped_at ON prices(scraped_at);
            CREATE INDEX IF NOT EXISTS idx_prices_product_date ON prices(product_id, scraped_at DESC);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_prices_unique_per_day ON prices(product_id, (scraped_at::date));
        """)
    conn.commit()