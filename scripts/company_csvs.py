import sys
from pathlib import Path

# Add project root (FIEP_PROJECT) to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import DAX_ARTICLES_FILE, FULL_SENTIMENT_FILE  # oder was du brauchst


import pandas as pd
import os
from config import DAILY_SENTIMENT_FILE, DAX_PRICES_FILE, COMPANY_DATA_DIR



# Create output directory if it doesn't exist
COMPANY_DATA_DIR.mkdir(parents=True, exist_ok=True)

# 1. Load data
sentiment_df = pd.read_csv(DAILY_SENTIMENT_FILE, parse_dates=["date"])
price_df = pd.read_csv(DAX_PRICES_FILE, parse_dates=["Date"])
price_df.rename(columns={"Date": "date"}, inplace=True)

# 2. Normalize company names
sentiment_df["company_name"] = sentiment_df["company_name"].str.strip().str.title()
price_df["Company"] = price_df["Company"].str.strip().str.title()

# 3. Get companies available in both datasets
companies = sorted(set(sentiment_df["company_name"]).intersection(price_df["Company"]))

# 4. Process each company
for company in companies:
    sentiment = sentiment_df[sentiment_df["company_name"] == company][["date", "avg_sentiment"]]
    price = price_df[price_df["Company"] == company][["date", "Close"]]

    df_new = pd.merge(sentiment, price, on="date", how="inner")
    if df_new.empty:
        print(f"⚠️ No data for {company}, skipping.")
        continue

    filename = f"{company.replace(' ', '_')}.csv"
    filepath = COMPANY_DATA_DIR / filename

    if filepath.exists():
        df_existing = pd.read_csv(filepath, parse_dates=["date"])
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined.drop_duplicates(subset=["date"], inplace=True)
    else:
        df_combined = df_new

    df_combined.sort_values("date", inplace=True)

    # Feature Engineering
    df_combined["sentiment_7d"] = df_combined["avg_sentiment"].rolling(7).mean()
    df_combined["sentiment_change"] = df_combined["avg_sentiment"].diff()
    df_combined["sentiment_lag1"] = df_combined["avg_sentiment"].shift(1)
    df_combined["sentiment_lag3"] = df_combined["avg_sentiment"].shift(3)
    df_combined["stock_price_return"] = df_combined["Close"].pct_change()
    df_combined["return_7d"] = df_combined["Close"].pct_change(7)
    df_combined["volatility_7d"] = df_combined["Close"].rolling(7).std()

    sentiment_mean = df_combined["avg_sentiment"].rolling(30).mean()
    sentiment_std = df_combined["avg_sentiment"].rolling(30).std()
    df_combined["sentiment_zscore"] = (df_combined["avg_sentiment"] - sentiment_mean) / sentiment_std

    df_combined["alert"] = df_combined["sentiment_change"] <= -0.3
    df_combined["alert_combined"] = (df_combined["sentiment_change"] <= -0.3) & (df_combined["stock_price_return"] < 0)

    df_combined["weekday"] = df_combined["date"].dt.day_name()
    df_combined["month"] = df_combined["date"].dt.month

    df_combined.to_csv(filepath, index=False)

print("✅ All company CSVs updated with advanced features.")
