# scraper/run_pipeline.py
import time
import json
from crunchbase_scrape import fetch_crunchbase_data
from founder_scrape import get_founders_info_and_save
from news_scrape import update_json_with_summaries

def scrape_company_info(company_name: str) -> dict:
    start = time.time()
    print(f"🔍 Starting scrape for: {company_name}")

    crunchbase_url = f"https://www.crunchbase.com/organization/{company_name.lower().replace(' ', '-')}"
    json_path = "company_data.json"

    try:
        # Step 1: Fetch base data
        data = fetch_crunchbase_data(crunchbase_url)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Step 2: Enrich founders
        get_founders_info_and_save(json_path)

        # Step 3: Enrich news (with error handling)
        try:
            update_json_with_summaries(json_path)
        except Exception as e:
            print(f"⚠️ News scraping failed (some data may be missing): {str(e)}")

        # Properly read back the JSON
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception as e:
        print(f"❌ Scraping failed: {str(e)}")
        return {"error": str(e)}
    finally:
        print(f"✅ Completed in {time.time() - start:.2f}s")

if __name__ == "__main__":
    data = scrape_company_info("american armed forces mutual aid association")
    print(json.dumps(data, indent=2, ensure_ascii=False))