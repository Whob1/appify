import asyncio
from crawler import crawl_and_score
from data_handler import save_to_csv, save_domain_scores
from aiohttp import ClientSession
from utils import logging

async def main(start_urls):
    domain_scores = {}
    discovered_domains = set()
    async with ClientSession() as session:
        for url in start_urls:
            visited = set()
            data = await crawl_and_score(url, session, visited, domain_scores, discovered_domains)
            save_to_csv([data])

    save_domain_scores(domain_scores)

if __name__ == "__main__":
    start_urls = ['http://example.com']
    asyncio.run(main(start_urls))
