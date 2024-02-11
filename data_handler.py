
import csv
import os
import json
from tempfile import NamedTemporaryFile
import shutil
from utils import DOMAINS_FILE, DATA_FILE, OUTPUT_DIR

class DataHandler:
    def __init__(self):
        self.temp_files = []

    def save_data_chunk(self, data):
        temp_file = NamedTemporaryFile(delete=False, dir=OUTPUT_DIR, mode='w', newline='', encoding='utf-8')
        writer = csv.DictWriter(temp_file, fieldnames=['url', 'text'])
        writer.writeheader()
        writer.writerows(data)
        self.temp_files.append(temp_file.name)
        temp_file.close()

    def consolidate_data(self):
        with open(DATA_FILE, 'w', newline='', encoding='utf-8') as f_out:
            writer = csv.writer(f_out)
            writer.writerow(['url', 'text'])  # Write final CSV header
            for temp_file in self.temp_files:
                with open(temp_file, 'r', newline='', encoding='utf-8') as f_in:
                    reader = csv.reader(f_in)
                    next(reader)  # Skip header
                    writer.writerows(reader)
                os.unlink(temp_file)  # Delete temporary file
        self.temp_files.clear()  # Clear the list of temporary files

    def save_domain_scores(self, domain_scores):
        with open(DOMAINS_FILE, 'w') as file:
            json.dump(domain_scores, file, indent=4)
