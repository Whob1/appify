import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utils import clean_text, extract_root_domain, logger, headers, TIMEOUT
from data_handler import DataHandler

class Crawler:
    def __init__(self, update_callback):
        self.session = None
        self.is_running = False
        self.is_paused = False
        self.data_handler = DataHandler(update_callback)
        self.update_callback = update_callback
        self.domains_to_crawl = asyncio.Queue()
        self.visited = set()
        self.rate_limit = 1  # seconds between requests
        self.urls_crawled = 0
        self.concurrency_limit = 5  # Max number of concurrent requests

    async def fetch(self, url):
        try:
            async with self.session.get(url, headers=headers, timeout=TIMEOUT) as response:
                if response.status != 200:
                    logger.error(f'Non-200 response for {url}: {response.status}')
                    return None
                self.urls_crawled += 1
                if self.urls_crawled % 1000 == 0:
                    self.update_callback({'urlsCrawled': self.urls_crawled, 'currentTask': 'Fetching URLs'})
                return await response.text()
        except Exception as e:
            logger.error(f'Error fetching {url}: {e}')
            return None

    async def crawl_and_extract(self):
        self.update_callback({'currentTask': 'Crawling and Extracting'})
        sem = asyncio.Semaphore(self.concurrency_limit)

        async def handle_url(url):
            async with sem:
                if url in self.visited:
                    return
                self.visited.add(url)
                content = await self.fetch(url)
                if content:
                    soup = BeautifulSoup(content, 'html.parser')
                    text = clean_text(' '.join(soup.stripped_strings))
                    if text:
                        await self.data_handler.save_data_chunk({'url': url, 'text': text})
                        self.update_callback({'currentTask': f'Saved data for {url}'})
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(url, href)
                        if extract_root_domain(full_url) == extract_root_domain(url) and full_url not in self.visited:
                            await self.domains_to_crawl.put(full_url)
                await asyncio.sleep(self.rate_limit)

        tasks = []
        while self.is_running and not self.is_paused and not self.domains_to_crawl.empty():
            url = await self.domains_to_crawl.get()
            tasks.append(asyncio.create_task(handle_url(url)))
            if len(tasks) >= self.concurrency_limit:
                await asyncio.gather(*tasks)
                tasks = []

        if tasks:
            await asyncio.gather(*tasks)

    async def start(self, initial_urls):
        if self.is_running:
            return
        self.is_running = True
        self.session = aiohttp.ClientSession()

        for url in initial_urls:
            await self.domains_to_crawl.put(url)

        try:
            await self.crawl_and_extract()
        finally:
            await self.session.close()
            await self.data_handler.consolidate_data()
            self.update_callback({'currentTask': 'Data consolidation completed'})
            self.is_running = False

    async def stop(self):
        self.is_running = False
        if self.session:
            await self.session.close()
            self.update_callback({'currentTask': 'Stopped'})

    async def pause(self):
        self.is_paused = True
        self.update_callback({'currentTask': 'Paused'})

    async def resume(self):
        self.is_paused = False
        self.update_callback({'currentTask': 'Resumed'})
        if not self.is_running:
            await self.start(list(self.visited))
