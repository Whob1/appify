import logging
import os
import re
from summarizer import Summarizer
from rake_nltk import Rake
import tldextract
from urllib.parse import urlparse

# Dedicated logger for the application
logger = logging.getLogger('AppLogger')
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)

class AppConfig:
    OUTPUT_DIR = 'output'
    DOMAINS_FILE = 'relevant_domains.json'
    DATA_FILE = 'crawled_data.csv'
    TIMEOUT = 10
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
    }
    KEYWORDS = [
        'safer use', 'harm reduction', 'risk reduction',
        'overdose', 'tolerance', 'roa', 'dose', 'duration', 'onset', 'peak',
        'interactions', 'Central', 'Nervous', 'System', 'Depressant', 'Stimulant', 'Hallucinogen',
        'Dissociative', 'Anesthetic', 'Narcotic', 'Analgesic', 'Inhalant', 'Cannabis',
        'Opioid', 'Amphetamine', 'Methamphetamine', 'Cocaine', 'Crack'
    ]

os.makedirs(AppConfig.OUTPUT_DIR, exist_ok=True)

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

def match_keywords(text, keywords=AppConfig.KEYWORDS):
    text_words = set(clean_text(text).lower().split())
    keyword_set = set(map(str.lower, keywords))
    return len(text_words & keyword_set)

summarizer = Summarizer()
rake = Rake()

def summarize_text(text):
    try:
        return summarizer(text, min_length=60)
    except Exception as e:
        logger.error(f"Error summarizing text: {e}")
        return text

def extract_keywords(text):
    try:
        rake.extract_keywords_from_text(text)
        return rake.get_ranked_phrases()[:5]
    except Exception as e:
        logger.error(f"Error extracting keywords: {e}")
        return []
