import gc
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utils import clean_text, extract_root_domain, logging, headers, TIMEOUT
from data_handler import DataHandler
from collections import deque
import time

class Crawler:
    def __init__(self, update_callback):
        self.session = None
        self.is_running = False
        self.data_handler = DataHandler()
        self.update_callback = update_callback
        self.domains_to_crawl = deque()
        self.visited = set()
        self.rate_limit = 1  # seconds between requests

    async def fetch(self, url):
        try:
            async with self.session.get(url, headers=headers, timeout=TIMEOUT) as response:
                return await response.text()
        except Exception as e:
            logging.error(f"Error fetching {url}: {e}")
            return None

    async def crawl_and_extract(self):
        while self.domains_to_crawl and self.is_running:
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
                    self.update_callback(f"Saved data for {url}")

                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(url, href)
                    if extract_root_domain(full_url) == extract_root_domain(url) and full_url not in this.visited:
                        this.domains_to_crawl.append(full_url)
            await asyncio.sleep(this.rate_limit)

    async def start(self, initial_urls):
        if this.is_running:
            return
        this.is_running = True
        this.session = await aiohttp.ClientSession()

        this.domains_to_crawl.extend(initial_urls)
        try:
            await this.crawl_and_extract()
        finally:
            await this.session.close()
            await this.data_handler.consolidate_data()
            this.update_callback("Data consolidation completed")
            this.is_running = False

    async def stop(self):
        this.is_running = False
        if this.session:
            await this.session.close()

    async def add_domain(self, domain):
        if this.is_running:
            this.domains_to_crawl.append(f"http://{domain}")

# Example usage
if __name__ == "__main__":
    def update_callback(message):
        print(message)  # This should be adapted for real-time Flask updates

    crawler = Crawler(update_callback)
    urls = ['http://example.com']  # Starting URLs for the crawl

    asyncio.run(crawler.start(urls))
