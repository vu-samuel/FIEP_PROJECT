'''from pathlib import Path
from dotenv import load_dotenv
import os

# Project base directory
BASE_DIR = Path(__file__).resolve().parent

# Common folders
SENTIMENT_DIR = BASE_DIR / "sentiment"
RAW_DATA_DIR = BASE_DIR / "raw_data"
COMPANY_DATA_DIR = BASE_DIR / "company_data"
LOG_FILE = BASE_DIR / "cron.log"

# Specific files
DAILY_SENTIMENT_FILE = SENTIMENT_DIR / "daily_sentiment.csv"
WEEKLY_SENTIMENT_FILE = SENTIMENT_DIR / "weekly_sentiment.csv"
MONTHLY_SENTIMENT_FILE = SENTIMENT_DIR / "monthly_sentiment.csv"
FULL_SENTIMENT_FILE = SENTIMENT_DIR / "full_sentiment.csv"

DAX_ARTICLES_FILE = RAW_DATA_DIR / "dax_articles.csv"
DAX_PRICES_FILE = RAW_DATA_DIR / "dax_stock_prices.csv"

# Load .env variables
load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
'''



from pathlib import Path
from dotenv import load_dotenv
import os

# Project base directory (root of FIEP_PROJECT)
BASE_DIR = Path(__file__).resolve().parent

# Common folders
SENTIMENT_DIR = BASE_DIR / "sentiment"
RAW_DATA_DIR = BASE_DIR / "raw_data"
COMPANY_DATA_DIR = BASE_DIR / "company_data"
LOG_FILE = BASE_DIR / "cron.log"

# Specific files
DAILY_SENTIMENT_FILE = SENTIMENT_DIR / "daily_sentiment.csv"
WEEKLY_SENTIMENT_FILE = SENTIMENT_DIR / "weekly_sentiment.csv"
MONTHLY_SENTIMENT_FILE = SENTIMENT_DIR / "monthly_sentiment.csv"
FULL_SENTIMENT_FILE = SENTIMENT_DIR / "full_sentiment.csv"

DAX_ARTICLES_FILE = RAW_DATA_DIR / "dax_articles.csv"
DAX_PRICES_FILE = RAW_DATA_DIR / "dax_stock_prices.csv"

# Load .env variables (optional)
load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

