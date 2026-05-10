import logging
import random
import time

logger = logging.getLogger(__name__)

# Ces fonctions utilisent Playwright pour rechercher les ASIN et les prix sur Amazon
def search_asin_and_price(page, title: str) -> tuple[str, float, str] | None:
    try:
        url = f"https://www.amazon.fr/s?k={title.replace(' ', '+')}+switch+2"
        page.goto(url)
        first_result = page.locator('[data-asin]:not([data-asin=""])').first
        asin = first_result.get_attribute('data-asin', timeout=5000)
        image_url = page.locator(f'[data-asin="{asin}"] img').first.get_attribute('src')
        whole = page.locator('.a-price-whole').first.inner_text()
        fraction = page.locator('.a-price-fraction').first.inner_text()
        price = float(f"{whole.replace(',', '').strip()}.{fraction.strip()}")
        time.sleep(random.uniform(1.5, 3.0))
        return (asin, price, image_url)
    except Exception as e:
        logger.warning(f"ASIN not found for {title}: {e}")
        return None
    
# Cette fonction est utilisée pour rechercher uniquement le prix à partir d'un ASIN donné 
def search_price(page, asin: str) -> float | None:
    try:
        url = f"https://www.amazon.fr/dp/{asin}"
        page.goto(url)
        if page.locator('.a-price-whole').count() == 0:
            logger.warning(f"Product unavailable for ASIN {asin}")
            return None
        whole = page.locator('.a-price-whole').first.inner_text()
        fraction = page.locator('.a-price-fraction').first.inner_text()
        price = float(f"{whole.replace(',', '').strip()}.{fraction.strip()}")
        time.sleep(random.uniform(1.5, 3.0))
        return price
    except Exception as e:
        logger.warning(f"Price not found for ASIN {asin}: {e}")
        return None
    
def get_price_and_image(page, asin: str) -> tuple[float, str] | None:
    try:
        url = f"https://www.amazon.fr/dp/{asin}"
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        })
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(2000) 
        whole = page.locator('.a-price-whole').first.inner_text(timeout=10000)
        fraction = page.locator('.a-price-fraction').first.inner_text(timeout=10000)
        price = float(f"{whole.replace(',', '').strip()}.{fraction.strip()}")
        image_url = page.locator('#imgTagWrapperId img').first.get_attribute('src')
        time.sleep(random.uniform(1.5, 3.0))
        return (price, image_url)
    except Exception as e:
        logger.warning(f"Price/image not found for ASIN {asin}: {e}")
        return None