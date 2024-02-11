import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utils import (
    clean_text, is_valid_url, is_relevant_link, extract_root_domain,
    match_keywords, summarize_text, extract_keywords, logging, headers, TIMEOUT
)

async def fetch(url, session):
    async with session.get(url, headers=headers, timeout=TIMEOUT) as response:
        return await response.text()

async def crawl_and_score(url, session, visited, domain_scores, discovered_domains, depth=0, max_depth=3, max_pages=15):
    if depth > max_depth or url in visited or len(visited) >= max_pages:
        return 0

    visited.add(url)
    html_content = await fetch(url, session)
    if not html_content:
        return 0

    soup = BeautifulSoup(html_content, 'html.parser')
    text = clean_text(' '.join(soup.stripped_strings))
    score = match_keywords(text)

    domain = extract_root_domain(url)
    if domain not in domain_scores:
        domain_scores[domain] = score
    else:
        domain_scores[domain] += score
    discovered_domains.add(domain)

    data = {'url': url, 'score': score, 'keywords': ', '.join(extract_keywords(text)), 'summarized_text': summarize_text(text)}

    for link in soup.find_all('a', href=True):
        href = link['href']
        full_url = urljoin(url, href)
        if is_relevant_link(full_url) and extract_root_domain(full_url) not in discovered_domains:
            await crawl_and_score(full_url, session, visited, domain_scores, discovered_domains, depth + 1, max_depth, max_pages)

    return data
