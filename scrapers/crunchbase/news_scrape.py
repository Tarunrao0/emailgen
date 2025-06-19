import json
from newspaper import Article
from groq import Groq
from scrapers.website.website_scraper import load_api_key

def extract_article_text(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        print(f"[Error] Failed to extract from {url}: {e}")
        return ""

def summarize_articles(news_entries, max_article_length=3000):
    all_articles = []

    for entry in news_entries:
        url = entry.get('url') or entry.get('link', '')
        article_text = extract_article_text(url)
        if article_text:
            trimmed = article_text.strip()[:max_article_length]
            all_articles.append(f"Article Title: {entry.get('title', '')}\n\n{trimmed}")

    if not all_articles:
        return "No article content could be extracted for summarization."

    combined_input = "\n\n---\n\n".join(all_articles)

    prompt = f"""
You are a business research assistant. Read the following **full articles** related to a company's recent news.

Write a rich, detailed paragraph that summarizes all major events across the articles. Capture:
- All key partnerships or announcements
- Product/platform launches or expansions
- Strategic directions and industry movements

⚠️ Do not begin with phrases like "Here is a summary" or "This article is about".

Include multiple points if necessary, but stay within one paragraph.

News Articles:
{combined_input}
"""

    api_key = load_api_key()
    client = Groq(api_key=api_key)

    completion = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_completion_tokens=1500
    )

    return completion.choices[0].message.content.strip()

def update_json_with_summaries(data: dict) -> dict:
    news_entries = data.get('news', [])
    if not news_entries:
        print('[Info] No news entries found.')
        return data

    summary = summarize_articles(news_entries)
    data['news_summary'] = summary
    print('[✅ Success] Company news summary added.')
    return data

if __name__ == "__main__":
    json_path = "company_data.json"

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        data = update_json_with_summaries(data)

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print("✅ Updated company_data.json with news_summary.")

    except Exception as e:
        print(f"❌ Failed to process company_data.json: {e}")
