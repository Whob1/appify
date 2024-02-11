import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utils import (
    clean_text, is_valid_url, is_relevant_link, extract_root_domain,
    match_keywords, summarize_text, extract_keywords, logging, headers, TIMEOUT, AppConfig
)

CACHE = {}
CACHE_EXPIRY = 60
URLS_PER_DOMAIN_LIMIT = 15

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

async def parse_html(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        text = clean_text(' '.join(soup.stripped_strings))
        return soup, text
    except Exception as e:
        logging.error(f"Error parsing HTML: {e}")
        return None, None

async def crawl_and_score(url, session, visited, domain_scores, discovered_domains, depth=0, max_depth=1):
    if depth > max_depth or len(visited) >= URLS_PER_DOMAIN_LIMIT:
        return
    visited.add(url)
    html_content = await fetch(url, session)
    if not html_content:
        return
    soup, text = await parse_html(html_content)
    if not soup:
        return
    score = match_keywords(text, AppConfig.KEYWORDS)
    domain = extract_root_domain(url)
    domain_scores[domain] = domain_scores.get(domain, 0) + score
    discovered_domains.add(domain)
    if depth < max_depth:
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(url, href)
            if is_relevant_link(full_url) and full_url not in visited and extract_root_domain(full_url) == domain:
                await crawl_and_score(full_url, session, visited, domain_scores, discovered_domains, depth + 1, max_depth)
