import logging
import os
import re
from summarizer import Summarizer
from rake_nltk import Rake
import tldextract
from urllib.parse import urlparse
import json

# Load configuration from a JSON file or environment variables
config_path = os.getenv('APP_CONFIG_PATH', 'app_config.json')
if os.path.exists(config_path):
    with open(config_path, 'r') as config_file:
        AppConfig = json.load(config_file)
else:
    AppConfig = {
        'OUTPUT_DIR': os.getenv('OUTPUT_DIR', 'output'),
        'DOMAINS_FILE': os.getenv('DOMAINS_FILE', 'relevant_domains.json'),
        'DATA_FILE': os.getenv('DATA_FILE', 'crawled_data.csv'),
        'TIMEOUT': int(os.getenv('TIMEOUT', 10)),
        'HEADERS': {
            'User-Agent': os.getenv('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36')
        }
    }

# Ensure output directory exists
os.makedirs(AppConfig['OUTPUT_DIR'], exist_ok=True)

# Configure logging
logger = logging.getLogger('AppLogger')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(ch)

def clean_text(text):
    return re.sub(r'\s+', ' ', re.sub(r'\W', ' ', text)).strip()

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
    except ValueError:
        return False

def extract_root_domain(url):
    extracted = tldextract.extract(url)
    return f"{extracted.domain}.{extracted.suffix}"

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
