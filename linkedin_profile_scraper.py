# linkedin_profile_scraper.py
import os
from dotenv import load_dotenv
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()
EMAIL = os.getenv("LINKEDIN_EMAIL")
PASSWORD = os.getenv("LINKEDIN_PASSWORD")

def fetch_linkedin_bio(profile_url: str) -> str:
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

        driver.get(profile_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Wait and find summary section
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "pv-shared-text-with-see-more")))
        bio_el = driver.find_element(By.CLASS_NAME, "pv-shared-text-with-see-more")
        bio_text = bio_el.text.strip()

        driver.quit()
        return bio_text

    except Exception as e:
        print(f"❌ Failed to fetch bio from LinkedIn: {e}")
        if driver:
            driver.quit()
        return ""
