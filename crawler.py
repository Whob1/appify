import gc
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utils import clean_text, extract_root_domain, logger, headers, TIMEOUT
from data_handler import DataHandler
from collections import deque
import json

class Crawler:
    def __init__(self, update_callback):
        self.session = None
        self.is_running = False
        self.is_paused = False
        self.data_handler = DataHandler(update_callback)
        self.update_callback = update_callback
        self.domains_to_crawl = deque()
        self.visited = set()
        self.rate_limit = 1  # seconds between requests
        self.urls_crawled = 0

    async def fetch(self, url):
        try:
            async with self.session.get(url, headers=headers, timeout=TIMEOUT) as response:
                self.urls_crawled += 1
                if self.urls_crawled % 1000 == 0:
                    self.update_callback(json.dumps({
                        "urlsCrawled": self.urls_crawled,
                        "currentTask": "Fetching URLs"
                    }))
                return await response.text()
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    async def crawl_and_extract(self):
        self.update_callback(json.dumps({"currentTask": "Crawling and Extracting"}))
        while self.domains_to_crawl and self.is_running and not self.is_paused:
            url = self.domains_to_crawl.popleft()
            if url in self.visited:
                continue
            self.visited.add(url)

            content = await self.fetch(url)
            if content:
                soup = BeautifulSoup(content, 'html.parser')
                text = clean_text(' '.join(soup.stripped_strings))
                if text:
                    await self.data_handler.save_data_chunk({'url': url, 'text': text})
                    self.update_callback(json.dumps({"currentTask": f"Saved data for {url}"}))

                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(url, href)
                    if extract_root_domain(full_url) == extract_root_domain(url) and full_url not in self.visited:
                        self.domains_to_crawl.append(full_url)
            await asyncio.sleep(self.rate_limit)

    async def start(self, initial_urls):
        if self.is_running:
            return
        self.is_running = True
        self.session = await aiohttp.ClientSession()

        self.domains_to_crawl.extend(initial_urls)
        try:
            await self.crawl_and_extract()
        finally:
            await self.session.close()
            await self.data_handler.consolidate_data()
            self.update_callback(json.dumps({"currentTask": "Data consolidation completed"}))
            self.is_running = False

    async def stop(self):
        self.is_running = False
        if self.session:
            await self.session.close()
            self.update_callback(json.dumps({"currentTask": "Stopped"}))

    async def pause(self):
        self.is_paused = True
        self.update_callback(json.dumps({"currentTask": "Paused"}))
        # Save the state here if needed

    async def resume(self):
        self.is_paused = False
        self.update_callback(json.dumps({"currentTask": "Resumed"}))
        # Restore the saved state here if needed
        if not self.is_running:
            await self.start(list(self.domains_to_crawl))

    async def add_domain(self, domain):
        if self.is_running and not self.is_paused:
            self.domains_to_crawl.append(f"http://{domain}")
            self.update_callback(json.dumps({"currentTask": f"Added domain {domain}"}))

# Example usage
if __name__ == "__main__":
    def update_callback(message):
        # This should be adapted to emit SSE or log appropriately
        print(message)

    crawler = Crawler(update_callback)
    asyncio.run(crawler.start(['http://example.com']))
