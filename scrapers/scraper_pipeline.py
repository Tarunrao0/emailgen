import time
import json
import argparse
import os
import concurrent.futures

from scrapers.crunchbase.crunchbase_scrape import fetch_crunchbase_data
from scrapers.crunchbase.news_scrape import update_news_summary_for_company_key
from scrapers.website.website_scraper import (
    scrape_homepage_sections,
    summarize_full_site_with_groq,
    load_api_key
)
from groq import Groq


def make_serializable(obj):
    """ Recursively convert non-serializable objects into strings. """
    if isinstance(obj, (dict, list, str, int, float, bool, type(None))):
        return obj
    elif isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_serializable(item) for item in obj]
    else:
        return str(obj)


def scrape_crunchbase_info(url: str) -> dict:
    try:
        print("📊 Scraping Crunchbase data...")
        data = fetch_crunchbase_data(url)
        return data
    except Exception as e:
        print(f"❌ Crunchbase scraping failed: {str(e)}")
        return {"crunchbase_error": str(e)}


def init_groq_client():
    print("🛠️ Initializing Groq client and setting device...")
    return Groq(api_key=load_api_key())


def run_website_summary_from_url(url: str, groq_future=None) -> str:
    print(f"🌐 Scraping website: {url}")
    try:
        sections = scrape_homepage_sections(url)
        client = groq_future.result() if groq_future else Groq(api_key=load_api_key())
        summary = summarize_full_site_with_groq(sections)
        print("✅ Website summary generated.")
        return summary
    except Exception as e:
        print(f"⚠️ Website scraping failed: {str(e)}")
        return None


def scrape_company_info(company_name: str, homepage_url: str) -> dict:
    start = time.time()
    print(f"\n🔍 Starting scrape for: {company_name}\n")

    company_key = company_name.lower().replace(" ", "-")
    crunchbase_url = f"https://www.crunchbase.com/organization/{company_key}"
    json_path = "data/company_data.json"

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_crunchbase = executor.submit(scrape_crunchbase_info, crunchbase_url)
        future_groq = executor.submit(init_groq_client)
        future_website = executor.submit(run_website_summary_from_url, homepage_url, future_groq)

        crunchbase_data = future_crunchbase.result()
        website_summary = future_website.result()

    if website_summary:
        crunchbase_data["website_summary"] = website_summary

    # Load existing data
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            all_data = json.load(f)
    else:
        all_data = {}

    # Insert or replace entry
    all_data[company_key] = make_serializable(crunchbase_data)

    # ✅ Update news summary for this specific company only
    all_data = update_news_summary_for_company_key(company_key, all_data)

    # Save back
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Completed in {time.time() - start:.2f}s\n")
    return all_data[company_key]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape company info from Crunchbase and website.")
    parser.add_argument("company_name", help="Company name (used for Crunchbase)")
    parser.add_argument("--url", help="Company homepage URL (for website scraper)", required=False)

    args = parser.parse_args()

    company_name = args.company_name
    homepage_url = args.url

    if not homepage_url:
        homepage_url = input("🌐 Enter the company's website URL (e.g. https://nvidia.com): ").strip()

    data = scrape_company_info(company_name, homepage_url)
    print(json.dumps(data, indent=2, ensure_ascii=False))
