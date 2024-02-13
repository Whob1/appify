
import asyncio
import os
from crawler import Crawler
from data_handler import DataHandler
from utils import logger, AppConfig

async def crawl_and_process(start_urls, session):
    crawler = Crawler(session)
    data_handler = DataHandler()
    for url in start_urls:
        try:
            await crawler.crawl(url)
            data = crawler.extract_data()
            await data_handler.save_data_chunk(data)
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")

async def main():
    start_urls = AppConfig['START_URLS'].split(",")
    max_retries = AppConfig['MAX_RETRIES']
    score_threshold = AppConfig['SCORE_THRESHOLD']
    domain_scores = {}

    async with aiohttp.ClientSession() as session:
        for _ in range(max_retries):
            try:
                await crawl_and_process(start_urls, session)
                break
            except Exception as e:
                logger.error(f"Retry due to error: {e}")
        
        # Update domain_scores based on extracted data
        # Code to update domain_scores goes here

    top_domains = {domain: score for domain, score in domain_scores.items() if score >= score_threshold}
    if top_domains:
        logger.info(f"Top domains for next crawl: {top_domains}")
    else:
        logger.info("No domains meet the score threshold. Stopping.")

if __name__ == "__main__":
    asyncio.run(main())
