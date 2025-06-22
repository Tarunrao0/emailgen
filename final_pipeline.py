import time
import csv
import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Your combined pipeline
from scrapers.scraper_pipeline import scrape_company_info
from email_gen.emailgen_pipeline import generate_email

# ========== CONFIG ==========

CSV_FILE = "email_log.csv"
JSON_FILE = "data/company_data.json"
EMBEDDINGS_PATH = "data/email_embeddings.json"

# ========== FASTAPI APP ==========

app = FastAPI()
latest_email = {"company": "", "subject": "", "email": ""}

# ========== CSV LOGGER ==========

def append_to_csv(entry: dict):
    fieldnames = ["company", "subject", "email"]
    try:
        with open(CSV_FILE, "a", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if f.tell() == 0:
                writer.writeheader()
            writer.writerow(entry)
    except Exception as e:
        print(f"❌ Failed to write to CSV: {e}")

# ========== FASTAPI ENDPOINTS ==========

class CompanyRequest(BaseModel):
    company_name: str
    homepage_url: str

@app.post("/scrape")
def scrape_and_generate(request: CompanyRequest):
    global latest_email
    start = time.time()

    # 1. Run full data scraping pipeline (Crunchbase + founders + news + website summary)
    scrape_company_info(request.company_name, request.homepage_url)

    # 2. Generate email using updated company_data.json
    email = generate_email(JSON_FILE, EMBEDDINGS_PATH)
    append_to_csv(email)
    latest_email = email

    print(f"✅ API request completed in {time.time() - start:.2f}s")
    return JSONResponse(content=email)

@app.get("/email")
def get_latest_email():
    return latest_email

# ========== MAIN RUNNER ==========

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
