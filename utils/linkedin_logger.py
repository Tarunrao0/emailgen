import os
import json
import csv
from datetime import datetime

CSV_PATH = "data/linkedin_log.csv"
JSON_PATH = "data/linkedin_log.json"

def save_linkedin_message(company: str, message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    word_count = len(message.split())

    record = {
        "company": company,
        "message": message,
        "word_count": word_count,
        "timestamp": timestamp
    }

    # Save to CSV
    os.makedirs("data", exist_ok=True)
    csv_exists = os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=record.keys())
        if not csv_exists:
            writer.writeheader()
        writer.writerow(record)

    # Save to JSON
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r+", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
            data.append(record)
            f.seek(0)
            json.dump(data, f, indent=2)
    else:
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump([record], f, indent=2)

    return record
