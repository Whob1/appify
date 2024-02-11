import requests
from bs4 import BeautifulSoup
import logging
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, urljoin
import os
import re
import json
import csv
from summarizer import Summarizer
from rake_nltk import Rake
import tldextract
import asyncio
import aiohttp

# Logging Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Output directory configuration
OUTPUT_DIR = 'output'
os.makedirs(OUTPUT_DIR, exist_ok=True)
DOMAINS_FILE = os.path.join(OUTPUT_DIR, 'relevant_domains.json')
DATA_FILE = os.path.join(OUTPUT_DIR, 'crawled_data.csv')

# Session and Headers Configuration
session = requests.Session()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
}

# Global Variables
TIMEOUT = 10
KEYWORDS = [

KEYWORDS = [
    'safer use', 'harm reduction', 'risk reduction',
    'overdose', 'tolerance', 'roa', 'dose', 'duration', 'onset', 'peak',
    'interactions', 'Central', 'Nervous', 'System', 'Depressant', 'Stimulant', 'Hallucinogen',
    'Dissociative', 'Anesthetic', 'Narcotic', 'Analgesic', 'Inhalant', 'Cannabis',
    'Opioid', 'Amphetamine', 'Methamphetamine', 'Cocaine', 'Crack',
    # Add more keywords as needed
]

async def fetch(url, session):
    async with session.get(url, headers=headers, timeout=TIMEOUT) as response:
        return await response.text()

async def fetch_all(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(url, session) for url in urls]
        return await asyncio.gather(*tasks)

seen_hashes = set()

def get_content_hash(content):
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def is_duplicate_content(content):
    content_hash = get_content_hash(content)
    if content_hash in seen_hashes:
        return True
    seen_hashes.add(content_hash)
    return False


RELEVANCE_THRESHOLD = 5  # Define a minimum relevance score to continue crawling

def should_continue_crawling(depth, score, max_depth=3):
    return depth < max_depth and score > RELEVANCE_THRESHOLD

def is_relevant_link(url):
    irrelevant_paths = ['/contact', '/about', '/privacy']
    return not any(irrelevant_path in url for irrelevant_path in irrelevant_paths)

def extract_root_domain(url):
    parsed_uri = urlparse(url)
    extracted = tldextract.extract(parsed_uri.netloc)
    return f"{extracted.domain}.{extracted.suffix}"

def clean_text(text):
    """Clean text by removing special characters and reducing whitespace."""
    return re.sub(r'\s+', ' ', re.sub(r'\W', ' ', text)).strip()

def match_keywords(text, keywords):
    """Match text against given keywords efficiently."""
    text_words = set(clean_text(text).lower().split())
    keyword_set = set(map(str.lower, keywords))
    return len(text_words & keyword_set)

def is_valid_url(url):
    """Validate the URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
    except ValueError:
        return False

async def fetch_content(url, session):
    """Asynchronously fetch HTML content with error handling."""
    try:
        async with session.get(url, headers=headers, timeout=TIMEOUT) as response:
            response.raise_for_status()
            return await response.text()
    except Exception as e:
        logging.error(f"Error fetching URL: {url} - {e}")
        return None

def analyze_content_for_keywords(text, keywords):
    """Analyze text for relevant keywords and return a score based on their presence."""
    return match_keywords(text, keywords)

def summarize_text(text):
    """Generate a summary for the given text."""
    model = Summarizer()
    return model(text, min_length=60)

def extract_keywords(text):
    """Extract key phrases from the text using Rake."""
    rake = Rake()
    rake.extract_keywords_from_text(text)
    return rake.get_ranked_phrases()[:5]  # Returns top 5 keywords

def update_domain_scores(domain, score, domain_scores):
    """Update the score of a domain based on the relevance of its content."""
    if domain in domain_scores:
        domain_scores[domain] += score
    else:
        domain_scores[domain] = score

def save_domain_scores(domain_scores):
    """Save domain scores to a file."""
    with open(DOMAINS_FILE, 'w') as file:
        json.dump(domain_scores, file, indent=4)

def parse_html(html, url, data, domain_scores, discovered_domains):
    """Parse HTML content, extract relevant information, and discover new links."""
    if not html or not is_valid_url(url):
        return

    soup = BeautifulSoup(html, 'html.parser')
    text = ' '.join(soup.stripped_strings)
    cleaned_text = clean_text(text)
    summarized_text = summarize_text(cleaned_text)
    keywords = extract_keywords(cleaned_text)
    score = analyze_content_for_keywords(cleaned_text, KEYWORDS)

    domain = extract_root_domain(url)
    update_domain_scores(domain, score, domain_scores)
    discovered_domains.add(domain)

    # Append content data to the dataset
    data.append({
        'url': url,
        'full_text': cleaned_text,
        'summarized_text': summarized_text,
        'keywords': ', '.join(keywords)
    })

    # Extract and process links for further crawling
    for link in soup.find_all('a', href=True):
        href = link['href']
        full_url = urljoin(url, href)
        # Filter links based on relevance
        if is_relevant_link(full_url) and full_url not in discovered_domains:
            discovered_domains.add(extract_root_domain(full_url))

RELEVANCE_THRESHOLD = 5  # Adjust based on your requirements

async def crawl_and_score(url, session, visited, depth=0, max_depth=3, pages_crawled=0, max_pages=15):
    # Base cases: stop if max depth reached, max pages crawled, or URL already visited
    if depth > max_depth or pages_crawled >= max_pages or url in visited:
        return 0, pages_crawled

    visited.add(url)  # Mark the current URL as visited
    pages_crawled += 1  # Increment the count of pages crawled

    html_content = await fetch_content(url, session)
    if not html_content:
        return 0, pages_crawled  # Return the current score and count if no content

    # Score the current page based on keyword matches
    text = clean_text(' '.join(BeautifulSoup(html_content, 'html.parser').stripped_strings))
    score = analyze_content_for_keywords(text, KEYWORDS)

    # Prepare to crawl and score linked pages within the same domain
    soup = BeautifulSoup(html_content, 'html.parser')
    tasks = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        next_url = urljoin(url, href)
        if urlparse(next_url).netloc == urlparse(url).netloc and next_url not in visited:
            tasks.append(crawl_and_score(next_url, session, visited, depth + 1, max_depth, pages_crawled, max_pages))

    # Gather scores from linked pages, ensuring not to exceed the max_pages limit
    results = await asyncio.gather(*tasks)
    for link_score, crawled in results:
        score += link_score  # Aggregate the score
        pages_crawled += crawled  # Update the count of pages crawled

    return score, pages_crawled

              

def prioritize_domains_with_deep_crawling(start_urls, max_depth=3):
    """Score and sort domains based on deep crawling, returning a list prioritized by relevance."""
    scored_domains = [(url, crawl_and_score(url, max_depth=max_depth)) for url in start_urls]
    scored_domains.sort(key=lambda x: x[1], reverse=True)  # Sort domains based on their scores
    return scored_domains

def prioritize_domains(start_urls):
    """Score and sort domains, returning a list prioritized by relevance."""
    scored_domains = [(url, initial_crawl_and_score(url)) for url in start_urls]
    # Sort domains based on their scores in descending order
    scored_domains.sort(key=lambda x: x[1], reverse=True)
    return scored_domains

async def export_data(data, filename):
    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['url', 'score'])
        writer.writeheader()
        for item in data:
            writer.writerow(item)

async def main(start_urls, max_depth=3, cycles=3, score_threshold=10):
    async with aiohttp.ClientSession() as session:
        for cycle in range(cycles):
            scored_domains = await asyncio.gather(*(score_domain(url, session) for url in start_urls))
            filtered_domains = [url for url, score in scored_domains if score > score_threshold]
            if not filtered_domains:
                logging.info("No domains exceed the score threshold. Ending process.")
                break
            await asyncio.gather(*(crawl_and_score(url, session, max_depth=max_depth) for url in filtered_domains))
            # Logic for selecting new domains for the next cycle, if applicable
