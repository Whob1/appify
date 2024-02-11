import asyncio
from crawler import crawl_and_score
from data_handler import save_to_csv, save_domain_scores
from aiohttp import ClientSession
from utils import logging

async def main(start_urls):
    while True:
        domain_scores = {}
        discovered_domains = set()
        all_data = []
        async with ClientSession() as session:
            tasks = [crawl_and_score(url, session, set(), domain_scores, discovered_domains) for url in start_urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logging.error(f"Error in crawling: {result}")
                else:
                    all_data.extend(result if result else [])
        save_to_csv(all_data)
        save_domain_scores(domain_scores)
        top_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        start_urls = [f"http://{domain}" for domain, score in top_domains if score >= 10]
        if not start_urls:
            break

if __name__ == "__main__":
    asyncio.run(main(['http://example.com']))
