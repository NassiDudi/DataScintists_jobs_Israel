import time
import pandas as pd
from datetime import datetime
from scrapers import scrape_linkedin, scrape_monday, scrape_amazon  # Your scrapers

CSV_PATH = "data_scientist_jobs_israel.csv"

def normalize_link(link): ## normalize the link for removing duplicates
    return link.split("?")[0] if isinstance(link, str) else link

def load_existing_jobs(): ## loading jobs csv file
    try:
        df = pd.read_csv(CSV_PATH)
        df["link"] = df["link"].apply(normalize_link)
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=["title", "company", "location", "link", "source", "scraped_at"])

def remove_duplicates(new_df, existing_df): #removing dulpilcates by links
    new_df["link"] = new_df["link"].apply(normalize_link)
    return new_df[~new_df["link"].isin(existing_df["link"])]

def main_loop(): ## scraping every 2 hours
    while True:
        print(f"\n🔄 Scraping started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        scrape_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Run all scrapers
        linkedin_jobs = scrape_linkedin(scrape_time)
        monday_jobs = scrape_monday(scrape_time)
        amazon_jobs = scrape_amazon(scrape_time)

        all_jobs = linkedin_jobs + monday_jobs + amazon_jobs
        new_jobs_df = pd.DataFrame(all_jobs)

        if new_jobs_df.empty:
            print("⚠️ No new jobs scraped.")
        else:
            existing_jobs_df = load_existing_jobs()
            unique_new_jobs = remove_duplicates(new_jobs_df, existing_jobs_df)

            if not unique_new_jobs.empty:
                updated_df = pd.concat([existing_jobs_df, unique_new_jobs], ignore_index=True)
                updated_df.to_csv(CSV_PATH, index=False)
                print(f"✅ Added {len(unique_new_jobs)} new job(s). Total: {len(updated_df)}")
            else:
                print("📭 No new unique jobs to add.")
                # Add dummy 'None' job to keep track of scrape time with zero new jobs
                dummy_job = {
                    "title": "None",
                    "company": "None",
                    "location": "None",
                    "link": "None",
                    "source": "None",
                    "scraped_at": scrape_time
                }
                updated_df = pd.concat([existing_jobs_df, pd.DataFrame([dummy_job])], ignore_index=True)
                updated_df.to_csv(CSV_PATH, index=False)
                print("📝 Added dummy entry for no new jobs scrape.")

        print("⏳ Waiting for 2 hours ..\n")
        time.sleep(7200)

if __name__ == "__main__":
    main_loop()
