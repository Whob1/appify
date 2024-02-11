import re
from urllib.parse import urlparse
import tldextract

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

def match_keywords(text, keywords):
    text_words = set(clean_text(text).lower().split())
    keyword_set = set(map(str.lower, keywords))
    return len(text_words & keyword_set)
