import csv
import json
from utils import DOMAINS_FILE, DATA_FILE

def save_to_csv(data, filename=DATA_FILE):
    with open(filename, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['url', 'score', 'keywords', 'summarized_text'])
        if f.tell() == 0:
            writer.writeheader()
        writer.writerows(data)

def save_domain_scores(domain_scores):
    with open(DOMAINS_FILE, 'w') as file:
        json.dump(domain_scores, file, indent=4)
