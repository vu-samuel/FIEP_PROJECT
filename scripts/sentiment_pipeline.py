import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import FULL_SENTIMENT_FILE
import pandas as pd
import os
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from config import DAX_ARTICLES_FILE, FULL_SENTIMENT_FILE  # ✅ use from config.py

import sys
from pathlib import Path


# Download the VADER lexicon (if not already present)
nltk.download('vader_lexicon', quiet=True)

# ---------- Step 1: Load article data ----------
df_new = pd.read_csv(DAX_ARTICLES_FILE)
df_new['publishedAt'] = pd.to_datetime(df_new['publishedAt'], errors='coerce')
df_new.dropna(subset=['publishedAt'], inplace=True)
df_new['date'] = df_new['publishedAt'].dt.date
df_new['text'] = df_new['title'].fillna('') + '. ' + df_new['description'].fillna('')

# ---------- Step 2: Load previous sentiment data ----------
if FULL_SENTIMENT_FILE.exists():
    df_old = pd.read_csv(FULL_SENTIMENT_FILE, parse_dates=['publishedAt'])
    df_old['date'] = pd.to_datetime(df_old['publishedAt'], errors='coerce').dt.date
    known_dates = set(df_old['publishedAt'].astype(str))
    df_new = df_new[~df_new['publishedAt'].astype(str).isin(known_dates)]
else:
    df_old = pd.DataFrame()

# ---------- Step 3: Run sentiment analysis ----------
if not df_new.empty:
    print("⚙️ Running VADER sentiment analysis...")
    sia = SentimentIntensityAnalyzer()

    def get_sentiment(text):
        scores = sia.polarity_scores(text)
        compound = scores["compound"]
        if compound > 0.1:
            label = "positive"
        elif compound < -0.1:
            label = "negative"
        else:
            label = "neutral"
        return pd.Series([compound, label])

    df_new[['sentiment_score', 'sentiment_label']] = df_new['text'].apply(lambda x: get_sentiment(str(x)))

    # ---------- Step 4: Combine and save ----------
    df_combined = pd.concat([df_old, df_new], ignore_index=True)
    FULL_SENTIMENT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df_combined.to_csv(FULL_SENTIMENT_FILE, index=False)

    print(f"✅ {len(df_new)} new articles analyzed and saved to '{FULL_SENTIMENT_FILE.name}'")
else:
    print("🔁 No new articles to analyze.")
