
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import DAX_ARTICLES_FILE

import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote
import re
import os

# CONFIG
COMPANIES = ['Adidas', 'Airbus', 'Allianz', 'BASF', 'Bayer', 'Beiersdorf', 'BMW', 'Brenntag',
    'Commerzbank', 'Continental', 'Covestro', 'Daimler Truck', 'Delivery Hero', 'Deutsche Bank',
    'Deutsche Börse', 'Deutsche Post', 'Deutsche Telekom', 'Deutsche Wohnen', 'E.ON', 'Fresenius',
    'Fresenius Medical Care', 'Hannover Rück', 'Heidelberg Materials', 'Hellofresh', 'Henkel',
    'Infineon', 'Mercedes-Benz', 'Merck', 'MTU Aero Engines', 'Münchener Rück', 'Porsche AG',
    'Porsche SE', 'Qiagen', 'Rheinmetall', 'RWE', 'SAP', 'Sartorius', 'Siemens', 'Siemens Energy',
    'Siemens Healthineers', 'Volkswagen', 'Vonovia', 'Zalando'
]

USER_AGENT = {"User-Agent": "Mozilla/5.0"}

# Load existing data
if DAX_ARTICLES_FILE.exists():
    df_existing = pd.read_csv(DAX_ARTICLES_FILE, parse_dates=["publishedAt"])
else:
    df_existing = pd.DataFrame(columns=["company_name", "title", "description", "url", "publishedAt", "source"])

def clean_html(raw_html):
    return re.sub('<[^<]+?>', '', raw_html)

def fetch_google_news(company):
    query = f"{company} after:2025-01-01"
    encoded_query = quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}"

    try:
        response = requests.get(rss_url, headers=USER_AGENT, timeout=10)
        soup = BeautifulSoup(response.content, features="xml")
        items = soup.find_all("item")
        news_data = []

        for item in items:
            title = clean_html(item.title.text)
            link = item.link.text
            pubDate = pd.to_datetime(item.pubDate.text).date() if item.pubDate else None
            source = re.sub(r'^https?://(www\.)?', '', re.search(r'https?://[^/]+', link).group()).split('.')[0].capitalize()

            news_data.append({
                "company_name": company,
                "title": title,
                "description": "",  # Not available via RSS
                "url": link,
                "publishedAt": pubDate,
                "source": source
            })

        return news_data
    except Exception as e:
        print(f"Failed to fetch RSS for {company}: {e}")
        return []

# Collect articles from all companies
all_articles = []
for company in COMPANIES:
    print(f"Fetching Google News for {company}...")
    articles = fetch_google_news(company)
    all_articles.extend(articles)

# Merge and sort
df_new = pd.DataFrame(all_articles)
df_combined = pd.concat([df_existing, df_new], ignore_index=True)
df_combined.drop_duplicates(subset=["url"], inplace=True)

# ✅ Fix: Ensure sorting doesn't fail on mixed types
df_combined["company_name"] = df_combined["company_name"].astype(str)
df_combined["publishedAt"] = pd.to_datetime(df_combined["publishedAt"], errors="coerce", utc=True)
df_combined.sort_values(by=["company_name", "publishedAt"], ascending=[True, True], inplace=True)


df_combined.to_csv(DAX_ARTICLES_FILE, index=False)
print(f"✅ Saved {len(df_combined)} articles to {DAX_ARTICLES_FILE}")
