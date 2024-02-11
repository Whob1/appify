import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from utils import clean_text, is_valid_url, extract_root_domain, match_keywords

async def fetch_content(url, session):
    try:
        async with session.get(url, timeout=10) as response:
            response.raise_for_status()
            return await response.text()
    except Exception as e:
        print(f"Error fetching URL: {url} - {e}")
        return None

async def crawl_and_score(url, session, visited, depth=0, max_depth=3):
    if depth > max_depth or url in visited:
        return 0, []

    visited.add(url)
    html_content = await fetch_content(url, session)
    if not html_content:
        return 0, []

    soup = BeautifulSoup(html_content, 'html.parser')
    text = clean_text(' '.join(soup.stripped_strings))
    score = match_keywords(text, KEYWORDS)  # Assume KEYWORDS is defined globally or passed as an argument

    data = [{'url': url, 'score': score, 'text': text}]
    for link in soup.find_all('a', href=True):
        href = link['href']
        next_url = urljoin(url, href)
        if is_valid_url(next_url) and next_url not in visited:
            next_score, next_data = await crawl_and_score(next_url, session, visited, depth + 1, max_depth)
            data.extend(next_data)

    return score, data
