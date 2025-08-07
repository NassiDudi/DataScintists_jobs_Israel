from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from hashlib import md5
from datetime import datetime
import pandas as pd
import time


def start_driver(headless=False):
    options = Options()
    options.add_argument("--window-size=1920,1080")
    if headless:
        options.add_argument("--headless")
    return webdriver.Chrome(options=options)

# LinkedIn Scraper          
def scrape_linkedin(date):
    driver = start_driver(headless=True)
    url = (
        "https://www.linkedin.com/jobs/search/?"
        "keywords=%22Data%20Scientist%22&location=Israel&geoId=101620260&f_TPR=r86400&position=1&pageNum=0"
    )

    def click_button(driver, xpath, limit=0): #########for removing popup window by click
        if limit <= 3:
            try:
                button = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                button.click()
            except:
                time.sleep(4)
                click_button(driver, xpath, limit + 1)

    def scroll_until_stable_html(driver, pause_time=4, max_attempts=20): ###for scrolling down the page
        last_html_hash = ""
        attempt = 0
        while attempt < max_attempts:
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(1)
            try:
                load_more_btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="main-content"]/section[2]/button'))
                )
                load_more_btn.click()
            except:
                pass
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(pause_time)
            current_html = driver.page_source
            current_hash = md5(current_html.encode("utf-8")).hexdigest()
            if current_hash == last_html_hash:
                break
            last_html_hash = current_hash
            attempt += 1

    driver.get(url)
    time.sleep(5)
    try:
        click_button(driver, '//*[@id="base-contextual-sign-in-modal"]/div/section/button')
    except:
        pass

    scroll_until_stable_html(driver)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    job_list = []
    ul = soup.select_one('#main-content > section:nth-of-type(2) > ul')
    if ul:
        for li in ul.find_all('li'):
            try:
                title = li.find("h3", class_="base-search-card__title").get_text(strip=True)
                company = li.find("h4", class_="base-search-card__subtitle").get_text(strip=True)
                location = li.find("span", class_="job-search-card__location").get_text(strip=True)
                link = li.find("a", class_="base-card__full-link")["href"]
                job_list.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "link": link,
                    "source": "LinkedIn",
                    "scraped_at": date#datetime.now().strftime("%Y-%m-%d %H:%M")
                })
            except:
                continue
    return job_list

# Monday.com Scraper
def scrape_monday(date):
    driver = start_driver(headless=True)
    driver.get("https://monday.com/careers?location=telaviv&search=data+scientist")
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    jobs = []
    job_divs = soup.select("div.mobile-results div.result")
    for div in job_divs:
        try:
            a_tag = div.find("a", href=True)
            title = a_tag.find("div", class_="position-name").text.strip()
            link = "https://monday.com" + a_tag["href"]
            location = a_tag.select_one("div.location-pill").text.strip()
            jobs.append({
                "title": title,
                "company": "Monday.com",
                "location": location,
                "link": link,
                "source": "Monday.com",
                "scraped_at": date#datetime.now().strftime("%Y-%m-%d %H:%M")
            })
        except:
            continue
    return jobs

# Amazon Scraper
def scrape_amazon(date):
    driver = start_driver(headless=True)
    driver.get("https://www.amazon.jobs/en/search?base_query=data+scientist&loc_query=Israel&country=ISR")
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    job_list = []
    tiles = soup.select("div.job-tile")
    for tile in tiles:
        try:
            title_tag = tile.select_one("h3.job-title a.job-link")
            title = title_tag.get_text(strip=True)
            link = "https://www.amazon.jobs" + title_tag["href"]
            location_tag = tile.select_one("ul li")
            location = location_tag.get_text(strip=True) if location_tag else "N/A"
            job_list.append({
                "title": title,
                "company": "Amazon",
                "location": location,
                "link": link,
                "source": "Amazon",
                "scraped_at": date#datetime.now().strftime("%Y-%m-%d %H:%M")
            })
        except:
            continue
    return job_list

# Run All
if __name__ == "__main__":
    print("Scrapping from Linkedin")
    linkedin_jobs = scrape_linkedin()
    print("Scrapping from monday")
    monday_jobs = scrape_monday()
    print("Scrapping from amazon")
    amazon_jobs = scrape_amazon()

    all_jobs = linkedin_jobs + monday_jobs + amazon_jobs
    df = pd.DataFrame(all_jobs)
    df.to_csv("data_scientist_jobs_israel1.csv", index=False)

    print(f"\n✅ Total scraped: {len(df)} job postings")
    print(df.head())
