import csv
import os
import json
from utils import DOMAINS_FILE, DATA_FILE, OUTPUT_DIR, update_callback, logger

class DataHandler:
    def __init__(self):
        self.chunk_index = 0
        self.csv_files_saved = 0

    def save_data_chunk(self, data):
        if not data:
            return

        try:
            chunk_path = os.path.join(OUTPUT_DIR, f'chunk_{self.chunk_index}.csv')
            with open(chunk_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=['url', 'text'])
                writer.writeheader()
                writer.writerows(data)
            self.chunk_index += 1
        except Exception as e:
            logger.error(f'Error saving data chunk: {e}')

    def consolidate_data(self):
        try:
            consolidated_path = os.path.join(OUTPUT_DIR, 'consolidated_data.csv')
            with open(consolidated_path, 'w', newline='', encoding='utf-8') as outfile:
                writer = csv.writer(outfile)
                writer.writerow(['url', 'text'])

                for i in range(self.chunk_index):
                    chunk_path = os.path.join(OUTPUT_DIR, f'chunk_{i}.csv')
                    with open(chunk_path, 'r', newline='', encoding='utf-8') as infile:
                        reader = csv.reader(infile)
                        next(reader)  # Skip header
                        writer.writerows(reader)
                    os.remove(chunk_path)  # Remove chunk file after its content has been written

            self.csv_files_saved += 1
            update_callback(json.dumps({"csvSaved": self.csv_files_saved}))
        except Exception as e:
            logger.error(f'Error consolidating data: {e}')

    def save_domain_scores(self, domain_scores):
        try:
            scores_path = os.path.join(OUTPUT_DIR, DOMAINS_FILE)
            with open(scores_path, 'w') as file:
                json.dump(domain_scores, file, indent=4)
        except Exception as e:
            logger.error(f'Error saving domain scores: {e}')

