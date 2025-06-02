import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import FULL_SENTIMENT_FILE
import pandas as pd

from config import (
    FULL_SENTIMENT_FILE,
    DAILY_SENTIMENT_FILE,
    WEEKLY_SENTIMENT_FILE,
    MONTHLY_SENTIMENT_FILE
)




# Load full sentiment data
df = pd.read_csv(FULL_SENTIMENT_FILE, parse_dates=['date'])

# Daily aggregation
daily = df.groupby(['company_name', df['date'].dt.date])['sentiment_score'].mean().reset_index()
daily.rename(columns={'sentiment_score': 'avg_sentiment'}, inplace=True)
daily.to_csv(DAILY_SENTIMENT_FILE, index=False)

# Weekly aggregation
weekly = df.groupby(['company_name', df['date'].dt.to_period('W').apply(lambda r: r.start_time)])['sentiment_score'].mean().reset_index()
weekly.rename(columns={'sentiment_score': 'avg_sentiment'}, inplace=True)
weekly.to_csv(WEEKLY_SENTIMENT_FILE, index=False)

# Monthly aggregation
monthly = df.groupby(['company_name', df['date'].dt.to_period('M').apply(lambda r: r.start_time)])['sentiment_score'].mean().reset_index()
monthly.rename(columns={'sentiment_score': 'avg_sentiment'}, inplace=True)
monthly.to_csv(MONTHLY_SENTIMENT_FILE, index=False)

print("📊 Aggregationen (daily, weekly, monthly) gespeichert.")
