'''import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DAX_ARTICLES_FILE, FULL_SENTIMENT_FILE, NEWS_API_KEY  # ✅ use from config.py
import pandas as pd
import time
import os
import random
from tqdm import tqdm
from datetime import datetime, timedelta
from newsapi import NewsApiClient


# DAX-Tickerliste
dax_tickers = [
    "GDAXI", "Adidas", "Airbus", "Allianz", "BASF", "Bayer", "Beiersdorf", "BMW", "Brenntag", "Commerzbank",
    "Continental", "Covestro", "Daimler Truck", "Delivery Hero", "Deutsche Bank", "Deutsche Börse", "Deutsche Post (DHL Group)",
    "Deutsche Telekom", "Deutsche Wohnen", "E.ON", "Fresenius", "Fresenius Medical Care", "Hannover Rück",
    "Heidelberg Materials", "Hellofresh", "Infineon", "Mercedes-Benz Group", "Merck", "MTU Aero Engines",
    "Münchener Rück", "Porsche AG", "Porsche SE", "Qiagen", "Rheinmetall", "RWE", "SAP", "Sartorius",
    "Siemens", "Siemens Energy", "Siemens Healthineers", "Symrise", "Volkswagen (VZ)", "Zalando"
]


# Init NewsAPI
newsapi = NewsApiClient(api_key=NEWS_API_KEY)

# Article buffer
article_list = []

# Time window
today = datetime.now()
thirty_days_ago = today - timedelta(days=30)
today_str = today.strftime('%Y-%m-%d')
thirty_days_ago_str = thirty_days_ago.strftime('%Y-%m-%d')

# Counters
total_fetched = 0
total_with_date = 0
total_without_date = 0

# Fetch articles
for company_name in tqdm(dax_tickers, desc="Fetching news"):
    try:
        all_articles = newsapi.get_everything(
            q=company_name,
            sources='handelsblatt,the-economist,business-insider,reuters,forbes,bloomberg,yahoo-finance',
            domains='handelsblatt.de,businessinsider.de,reuters.com,forbes.com,bloomberg.com,finance.yahoo.com',
            from_param=thirty_days_ago_str,
            to=today_str,
            sort_by='relevancy'
        )

        articles = all_articles.get('articles', [])
        total_fetched += len(articles)

        with_date = 0
        without_date = 0

        for article in articles:
            published_at = article.get('publishedAt')
            if not published_at:
                without_date += 1
                continue
            with_date += 1
            article_list.append({
                'company_name': company_name,
                'title': article['title'],
                'description': article['description'],
                'url': article['url'],
                'publishedAt': published_at,
                'source': article['source']['name']
            })

        print(f"🔎 {company_name}: {len(articles)} Artikel gefunden | 🟢 {with_date} mit Datum | 🔴 {without_date} ohne")

        total_with_date += with_date
        total_without_date += without_date

    except Exception as e:
        print(f"❌ Fehler bei {company_name}: {e}")

    time.sleep(random.uniform(2.5, 3.5))  # API courtesy delay

# Summary
print(f"\n📊 Gesamtübersicht:")
print(f"   Artikel gesamt:         {total_fetched}")
print(f"   Mit 'publishedAt':      {total_with_date}")
print(f"   Ohne 'publishedAt':     {total_without_date}")

# Create DataFrame
df_new = pd.DataFrame(article_list)
df_new.drop_duplicates(subset=["company_name", "title", "publishedAt"], inplace=True)
df_new.reset_index(drop=True, inplace=True)

# Combine with existing data
if DAX_ARTICLES_FILE.exists():
    df_existing = pd.read_csv(DAX_ARTICLES_FILE, parse_dates=["publishedAt"])
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
else:
    df_combined = df_new

# Clean & validate
df_combined['company_name'] = df_combined['company_name'].str.strip().str.lower()
df_combined['publishedAt'] = pd.to_datetime(df_combined['publishedAt'], errors='coerce')

missing_dates = df_combined['publishedAt'].isna().sum()
if missing_dates > 0:
    print(f"⚠️ {missing_dates} Zeilen haben ungültiges Datum und werden entfernt.")
    df_combined = df_combined.dropna(subset=["publishedAt"])

# Save final data
df_combined.sort_values(by=["company_name", "publishedAt"], inplace=True)
df_combined.reset_index(drop=True, inplace=True)
os.makedirs(DAX_ARTICLES_FILE.parent, exist_ok=True)
df_combined.to_csv(DAX_ARTICLES_FILE, index=False)

print(f"✅ CSV aktualisiert: {len(df_combined)} Artikel gespeichert in '{DAX_ARTICLES_FILE}'")

'''


import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import time
import os
import random
import logging
from tqdm import tqdm
from datetime import datetime, timedelta
from newsapi import NewsApiClient
from config import DAX_ARTICLES_FILE, FULL_SENTIMENT_FILE, NEWS_API_KEY

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ---------------- DAX Tickers ----------------
dax_tickers = [
    "GDAXI", "Adidas", "Airbus", "Allianz", "BASF", "Bayer", "Beiersdorf", "BMW", "Brenntag", "Commerzbank",
    "Continental", "Covestro", "Daimler Truck", "Delivery Hero", "Deutsche Bank", "Deutsche Börse", "Deutsche Post (DHL Group)",
    "Deutsche Telekom", "Deutsche Wohnen", "E.ON", "Fresenius", "Fresenius Medical Care", "Hannover Rück",
    "Heidelberg Materials", "Hellofresh", "Infineon", "Mercedes-Benz Group", "Merck", "MTU Aero Engines",
    "Münchener Rück", "Porsche AG", "Porsche SE", "Qiagen", "Rheinmetall", "RWE", "SAP", "Sartorius",
    "Siemens", "Siemens Energy", "Siemens Healthineers", "Symrise", "Volkswagen (VZ)", "Zalando"
]

# ---------------- Setup ----------------
newsapi = NewsApiClient(api_key=NEWS_API_KEY)
article_list = []

today = datetime.now()
thirty_days_ago = today - timedelta(days=30)
today_str = today.strftime('%Y-%m-%d')
thirty_days_ago_str = thirty_days_ago.strftime('%Y-%m-%d')

total_fetched = total_with_date = total_without_date = 0

# ---------------- Fetch Articles ----------------
for company_name in tqdm(dax_tickers, desc="🔍 Fetching news"):
    try:
        all_articles = newsapi.get_everything(
            q=company_name,
            sources='handelsblatt,the-economist,business-insider,reuters,forbes,bloomberg,yahoo-finance',
            domains='handelsblatt.de,businessinsider.de,reuters.com,forbes.com,bloomberg.com,finance.yahoo.com',
            from_param=thirty_days_ago_str,
            to=today_str,
            sort_by='relevancy',
            language='en'  # or 'de' if you prefer
        )

        articles = all_articles.get('articles', [])
        total_fetched += len(articles)

        with_date = 0

        for article in articles:
            published_at = article.get('publishedAt')
            if not published_at:
                total_without_date += 1
                continue

            article_list.append({
                'company_name': company_name,
                'title': article.get('title'),
                'description': article.get('description'),
                'url': article.get('url'),
                'publishedAt': published_at,
                'source': article.get('source', {}).get('name')
            })
            with_date += 1

        total_with_date += with_date
        logger.info(f"{company_name}: {len(articles)} total | 🟢 {with_date} with date | 🔴 {len(articles)-with_date} without date")

    except Exception as e:
        logger.error(f"❌ Error fetching articles for {company_name}: {e}")

    time.sleep(random.uniform(2.5, 3.5))  # API rate limiter

# ---------------- Summary ----------------
logger.info("\n📊 Fetch Summary:")
logger.info(f"   Total articles fetched: {total_fetched}")
logger.info(f"   With 'publishedAt':     {total_with_date}")
logger.info(f"   Without 'publishedAt':  {total_without_date}")

# ---------------- Clean & Combine ----------------
df_new = pd.DataFrame(article_list)
df_new.drop_duplicates(subset=["company_name", "title", "publishedAt"], inplace=True)
df_new.reset_index(drop=True, inplace=True)

# Load previous if exists
if DAX_ARTICLES_FILE.exists():
    df_existing = pd.read_csv(DAX_ARTICLES_FILE, parse_dates=["publishedAt"])
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
else:
    df_combined = df_new

# Final cleanup
df_combined["company_name"] = df_combined["company_name"].str.strip().str.lower()
df_combined["publishedAt"] = pd.to_datetime(df_combined["publishedAt"], errors='coerce')

missing_dates = df_combined["publishedAt"].isna().sum()
if missing_dates > 0:
    logger.warning(f"⚠️ {missing_dates} rows with invalid date removed.")
    df_combined = df_combined.dropna(subset=["publishedAt"])

# Sort & save
df_combined.sort_values(by=["company_name", "publishedAt"], inplace=True)
df_combined.reset_index(drop=True, inplace=True)
os.makedirs(DAX_ARTICLES_FILE.parent, exist_ok=True)
df_combined.to_csv(DAX_ARTICLES_FILE, index=False)

logger.info(f"✅ Final CSV updated: {len(df_combined)} articles saved to {DAX_ARTICLES_FILE}")
