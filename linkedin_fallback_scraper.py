# linkedin_fallback_scraper.py
import os
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from dotenv import load_dotenv

load_dotenv()
EMAIL = os.getenv("LINKEDIN_EMAIL")
PASSWORD = os.getenv("LINKEDIN_PASSWORD")

HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Accept-Language': 'en-US,en;q=0.9'
}

COMMON_PATHS = ['/news', '/press', '/blog', '/insights', '/about', '/team', '/leadership']

def fetch_page(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.text
    except requests.RequestException:
        pass
    return None

def extract_text_from_soup(soup):
    paragraphs = soup.find_all(['p', 'h2', 'h3'])
    return "\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30)

def extract_about_content(soup):
    candidates = soup.select('section, div')
    for tag in candidates:
        if 'about' in tag.get('class', []) or 'mission' in tag.get('class', []):
            text = tag.get_text(strip=True)
            if len(text.split()) > 30:
                return text
    return None

def fallback_website_scraper(website_url):
    data_blocks = []

    homepage_html = fetch_page(website_url)
    if homepage_html:
        soup = BeautifulSoup(homepage_html, 'html.parser')
        content = extract_about_content(soup) or extract_text_from_soup(soup)
        if content:
            data_blocks.append({
                "source": "website",
                "category": "homepage",
                "content": content,
                "url": website_url,
                "scraped_at": datetime.now().isoformat(),
                "quality_score": 6
            })

    for path in COMMON_PATHS:
        full_url = urljoin(website_url, path)
        html = fetch_page(full_url)
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            content = extract_text_from_soup(soup)
            if content:
                data_blocks.append({
                    "source": "website",
                    "category": path.strip("/"),
                    "content": content,
                    "url": full_url,
                    "scraped_at": datetime.now().isoformat(),
                    "quality_score": 5
                })
    return data_blocks

def fetch_linkedin_articles(linkedin_articles_url, max_articles=30):
    driver = None
    try:
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--start-maximized")
        driver = uc.Chrome(options=options)

        driver.get("https://www.linkedin.com/login")
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(EMAIL)
        driver.find_element(By.ID, "password").send_keys(PASSWORD + Keys.RETURN)
        WebDriverWait(driver, 15).until(EC.url_contains("feed"))

        driver.get(linkedin_articles_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(4)

        articles = []
        seen = set()
        last_height = driver.execute_script("return document.body.scrollHeight")

        while len(articles) < max_articles:
            elements = driver.find_elements(By.CSS_SELECTOR, "div.update-components-text")
            for el in elements:
                text = el.text.strip()
                if text and text not in seen:
                    seen.add(text)
                    articles.append(text)
                    if len(articles) >= max_articles:
                        break
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        driver.quit()

        if articles:
            return [{
                "source": "linkedin",
                "category": "articles",
                "content": "\n\n".join(articles),
                "url": linkedin_articles_url,
                "scraped_at": datetime.now().isoformat(),
                "quality_score": 8
            }]
    except Exception as e:
        print(f"❌ Failed LinkedIn scrape: {e}")
        if driver:
            driver.quit()
    return []

def fetch_linkedin_about(linkedin_about_url):
    driver = None
    try:
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--start-maximized")
        driver = uc.Chrome(options=options)

        driver.get("https://www.linkedin.com/login")
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(EMAIL)
        driver.find_element(By.ID, "password").send_keys(PASSWORD + Keys.RETURN)
        WebDriverWait(driver, 15).until(EC.url_contains("feed"))

        driver.get(linkedin_about_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)

        about_el = driver.find_element(By.CSS_SELECTOR, "section.artdeco-card p")
        about_text = about_el.text.strip()
        driver.quit()

        if about_text:
            return [{
                "source": "linkedin",
                "category": "about",
                "content": about_text,
                "url": linkedin_about_url,
                "scraped_at": datetime.now().isoformat(),
                "quality_score": 6
            }]
    except Exception as e:
        print(f"❌ LinkedIn about scrape failed: {e}")
        if driver:
            driver.quit()
    return []

def normalize_source_data(data):
    return {
        "source_type": f"{data.get('source', 'unknown')}_{data.get('category', 'uncategorized')}",
        "text": data.get("content", ""),
        "source_url": data.get("url", ""),
        "quality_score": data.get("quality_score", 0),
    }

def scrape_all_company_data(linkedin_url, website_url):
    sources = []
    if linkedin_url:
        sources.extend(fetch_linkedin_articles(linkedin_url))
        about_url = linkedin_url.replace("/posts", "/about")
        sources.extend(fetch_linkedin_about(about_url))

    if website_url:
        sources.extend(fallback_website_scraper(website_url))

    return [normalize_source_data(s) for s in sources if s]
