import gc
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utils import (
    clean_text, extract_root_domain, match_keywords, AppConfig, logging, headers, TIMEOUT
)
from data_handler import DataHandler

CACHE = {}
CACHE_EXPIRY = 60  # Cache expiry time in seconds

async def fetch(url, session):
    cache_result = CACHE.get(url)
    if cache_result and time.time() - cache_result['timestamp'] < CACHE_EXPIRY:
        return cache_result['data']
    try:
        async with session.get(url, headers=headers, timeout=TIMEOUT) as response:
            text = await response.text()
            CACHE[url] = {'data': text, 'timestamp': time.time()}
            return text
    except Exception as e:
        logging.error(f"Error fetching {url}: {e}")
        return None

async def crawl_and_extract(url, session, data_handler, update_callback):
    visited = set()
    try:
        html_content = await fetch(url, session)
        if html_content:
            soup = BeautifulSoup(html_content, 'html.parser')
            text = clean_text(' '.join(soup.stripped_strings))
            if text:
                data_handler.save_data_chunk({'url': url, 'text': text})
                update_callback(f"Saved data for {url}")
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                if full_url not in visited:
                    visited.add(full_url)
                    await crawl_and_extract(full_url, session, data_handler, update_callback)
    except Exception as e:
        logging.error(f"Error crawling {url}: {e}")
    finally:
        gc.collect()

async def main(urls, update_callback):
    data_handler = DataHandler()
    async with aiohttp.ClientSession() as session:
        tasks = [crawl_and_extract(url, session, data_handler, update_callback) for url in urls]
        await asyncio.gather(*tasks)
    await data_handler.consolidate_data()
    update_callback("Data consolidation completed")

if __name__ == "__main__":
    def update_callback(message):
        print(message)  # Replace with actual GUI callback in Flask app

    urls = ['http://example.com']
    asyncio.run(main(urls, update_callback))
