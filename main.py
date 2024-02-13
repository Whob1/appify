import asyncio
import os
from crawler import crawl_and_score
from data_handler import save_to_csv, save_domain_scores
from aiohttp import ClientSession
from utils import logger

# Configuration settings
START_URLS = os.getenv("START_URLS", "http://example.com").split(",")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
TOP_DOMAINS_THRESHOLD = int(os.getenv("TOP_DOMAINS_THRESHOLD", 3))
SCORE_THRESHOLD = int(os.getenv("SCORE_THRESHOLD", 10))

async def main(start_urls):
    while True:
        domain_scores = {}
        discovered_domains = set()
        all_data = []

        async with ClientSession() as session:
            tasks = []
            for url in start_urls:
                for attempt in range(MAX_RETRIES):
                    try:
                        task = asyncio.create_task(crawl_and_score(url, session, set(), domain_scores, discovered_domains))
                        tasks.append(task)
                        break  # Break the retry loop if successful
                    except Exception as e:
                        logger.error(f"Attempt {attempt+1} failed for {url}: {e}")
                        if attempt == MAX_RETRIES - 1:
                            logger.error(f"Max retries reached for {url}. Skipping.")

            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error in crawling: {result}")
                else:
                    all_data.extend(result if result else [])

        save_to_csv(all_data)
        save_domain_scores(domain_scores)

        top_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)[:TOP_DOMAINS_THRESHOLD]
        start_urls = [f"http://{domain}" for domain, score in top_domains if score >= SCORE_THRESHOLD]

        if not start_urls:
            logger.info("No more domains to crawl based on the scoring threshold. Stopping.")
            break

if __name__ == "__main__":
    asyncio.run(main(START_URLS))
