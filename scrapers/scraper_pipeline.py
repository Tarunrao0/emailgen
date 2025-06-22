import time
import json
import argparse
import concurrent.futures

from scrapers.crunchbase.crunchbase_scrape import fetch_crunchbase_data
from scrapers.crunchbase.news_scrape       import update_json_with_summaries

from scrapers.website.website_scraper      import (
    scrape_homepage_sections,
    summarize_full_site_with_groq,
    load_api_key
)
from scrapers.company_profile              import build_full_profile

from groq import Groq

def make_serializable(obj):
    """Recursively convert non-serializable objs into strings."""
    if isinstance(obj, (dict, list, str, int, float, bool, type(None))):
        return obj
    elif isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_serializable(i) for i in obj]
    else:
        return str(obj)

def scrape_crunchbase_info(url: str) -> dict:
    try:
        print("📊 Scraping Crunchbase data...")
        data = fetch_crunchbase_data(url)
        with open("data/company_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # add news summaries
        with open("data/company_data.json", "r", encoding="utf-8") as f:
            updated = json.load(f)
        updated = update_json_with_summaries(updated)
        with open("data/company_data.json", "w", encoding="utf-8") as f:
            json.dump(updated, f, indent=2, ensure_ascii=False)
        return updated

    except Exception as e:
        print(f"⚠️ Crunchbase scrape/news failed: {e}")
        return {"error": str(e)}

def init_groq_client():
    print("🛠️ Initializing Groq client…")
    return Groq(api_key=load_api_key())

def run_website_summary_from_url(url: str, groq_future=None) -> str:
    print(f"🌐 Scraping website: {url}")
    try:
        sections = scrape_homepage_sections(url)
        client   = groq_future.result() if groq_future else Groq(api_key=load_api_key())
        summary  = summarize_full_site_with_groq(sections)
        print("✅ Website summary generated.")
        return summary
    except Exception as e:
        print(f"⚠️ Website summary failed: {e}")
        return None

def scrape_company_info(company_name: str, homepage_url: str) -> dict:
    start = time.time()
    print(f"\n🔍 Starting scrape for: {company_name}\n")

    cb_url    = f"https://www.crunchbase.com/organization/{company_name.lower().replace(' ','-')}"
    json_path = "data/company_data.json"

    with concurrent.futures.ThreadPoolExecutor() as executor:
        fut_cb   = executor.submit(scrape_crunchbase_info, cb_url)
        fut_groq = executor.submit(init_groq_client)
        fut_web  = executor.submit(run_website_summary_from_url, homepage_url, fut_groq)

        crunchbase_data = fut_cb.result()
        web_summary     = fut_web.result()

    if web_summary:
        crunchbase_data["website_summary"] = web_summary

    # ─── NEW: build and merge full profile ────────────────────
    print("🏢 Building full company profile…")
    profile = build_full_profile(company_name, homepage_url, max_news=5)
    crunchbase_data["profile"] = profile
    print("✅ Full profile merged.")

    # write once
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(make_serializable(crunchbase_data), f, indent=2, ensure_ascii=False)

    print(f"\n✅ Completed in {time.time() - start:.2f}s\n")
    return crunchbase_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scrape Crunchbase + website + full profile"
    )
    parser.add_argument("company_name", help="Company name for Crunchbase")
    parser.add_argument(
        "--url", "-u",
        required=False,
        help="Company homepage URL for website scraping"
    )
    args = parser.parse_args()
    homepage = args.url or input("🌐 Enter homepage URL → ").strip()
    data     = scrape_company_info(args.company_name, homepage)
    print(json.dumps(data, indent=2, ensure_ascii=False))
