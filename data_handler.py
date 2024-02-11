import csv
import json

def save_to_csv(data, filename):
    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['url', 'score', 'text'])
        writer.writeheader()
        for item in data:
            writer.writerow(item)

def identify_relevant_domains(crawled_data, score_threshold):
    new_domains = set()
    for item in crawled_data:
        if item['score'] > score_threshold:
            domain = extract_root_domain(item['url'])  # Assuming extract_root_domain is defined in utils.py
            new_domains.add(domain)
    return list(new_domains)
