import logging
import os
import re
from summarizer import Summarizer
from rake_nltk import Rake
import tldextract
from urllib.parse import urlparse

# Logging Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Output directory configuration
OUTPUT_DIR = 'output'
os.makedirs(OUTPUT_DIR, exist_ok=True)
DOMAINS_FILE = os.path.join(OUTPUT_DIR, 'relevant_domains.json')
DATA_FILE = os.path.join(OUTPUT_DIR, 'crawled_data.csv')

# Headers Configuration for aiohttp requests
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
}

# Global Variables
TIMEOUT = 10
KEYWORDS = [
    # List your keywords here
]

def clean_text(text):
    return re.sub(r'\s+', ' ', re.sub(r'\W', ' ', text)).strip()

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
    except ValueError:
        return False

def is_relevant_link(url):
    irrelevant_paths = ['/contact', '/about', '/privacy']
    return not any(irrelevant_path in url for irrelevant_path in irrelevant_paths)

def extract_root_domain(url):
    extracted = tldextract.extract(url)
    return f"{extracted.domain}.{extracted.suffix}"

def match_keywords(text):
    text_words = set(clean_text(text).lower().split())
    keyword_set = set(map(str.lower, KEYWORDS))
    return len(text_words & keyword_set)

def summarize_text(text):
    model = Summarizer()
    return model(text, min_length=60)

def extract_keywords(text):
    rake = Rake()
    rake.extract_keywords_from_text(text)
    return rake.get_ranked_phrases()[:5]

KEYWORDS = [
    'safer use', 'harm reduction', 'risk reduction',
    'overdose', 'tolerance', 'roa', 'dose', 'duration', 'onset', 'peak',
    'interactions', 'Central', 'Nervous', 'System', 'Depressant', 'Stimulant', 'Hallucinogen',
    'Dissociative', 'Anesthetic', 'Narcotic', 'Analgesic', 'Inhalant', 'Cannabis',
    'Opioid', 'Amphetamine', 'Methamphetamine', 'Cocaine', 'Crack',
    # Add more keywords as needed
]
