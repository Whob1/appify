import logging
import os
import re
from summarizer import Summarizer
from rake_nltk import Rake
import tldextract
from urllib.parse import urlparse

# Set up logging
if not logging.getLogger().hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
OUTPUT_DIR = 'output'
os.makedirs(OUTPUT_DIR, exist_ok=True)
DOMAINS_FILE = os.path.join(OUTPUT_DIR, 'relevant_domains.json')
DATA_FILE = os.path.join(OUTPUT_DIR, 'crawled_data.csv')

# User agent for requests
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
}

# Timeout for requests
TIMEOUT = 10

# AppConfig class for storing application configuration
class AppConfig:
    KEYWORDS = [
        'safer use', 'harm reduction', 'risk reduction',
        'overdose', 'tolerance', 'roa', 'dose', 'duration', 'onset', 'peak',
        'interactions', 'Central', 'Nervous', 'System', 'Depressant', 'Stimulant', 'Hallucinogen',
        'Dissociative', 'Anesthetic', 'Narcotic', 'Analgesic', 'Inhalant', 'Cannabis',
        'Opioid', 'Amphetamine', 'Methamphetamine', 'Cocaine', 'Crack'
    ]

# Function to clean text
def clean_text(text):
    return re.sub(r'\\s+', ' ', re.sub(r'\\W', ' ', text)).strip()

# Function to validate URLs
def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
    except ValueError:
        return False

# Function to check if a link is relevant
def is_relevant_link(url):
    irrelevant_paths = ['/contact', '/about', '/privacy']
    return not any(irrelevant_path in url for irrelevant_path in irrelevant_paths)

# Function to extract the root domain from a URL
def extract_root_domain(url):
    extracted = tldextract.extract(url)
    return f"{extracted.domain}.{extracted.suffix}"

# Function to match keywords in text
def match_keywords(text, keywords=AppConfig.KEYWORDS):
    text_words = set(clean_text(text).lower().split())
    keyword_set = set(map(str.lower, keywords))
    return len(text_words & keyword_set)

# Initialize Summarizer and Rake instances
summarizer = Summarizer()
rake = Rake()

# Function to summarize text
def summarize_text(text):
    return summarizer(text, min_length=60)

# Function to extract keywords from text
def extract_keywords(text):
    rake.extract_keywords_from_text(text)
    return rake.get_ranked_phrases()[:5]
