# 📊 FIEP_PROJECT – Sentiment & Stock Price Dashboard

This project analyzes financial sentiment from news sources and compares it with stock performance of DAX companies. It includes a data pipeline for processing sentiment, a news ingestion script, and an interactive dashboard built with Streamlit.

---

## 📦 Project Structure

FIEP_PROJECT/
├── company_data/ # Daily sentiment + price CSVs for each company
├── raw_data/ # Raw input data (stock & article CSVs)
├── sentiment/ # Aggregated sentiment files (daily, weekly, etc.)
├── scripts/ # Python scripts for data processing & collection
├── .env # API keys (not tracked by Git)
├── .gitignore # Prevents .env and other files from being pushed
├── requirements.txt # Python dependencies
├── README.md # This file
├── app.py # Streamlit dashboard


---

## 🚀 Features

- ✅ Collects news for all DAX 40 companies using NewsAPI
- ✅ Cleans & aggregates sentiment scores
- ✅ Fetches historical stock prices
- ✅ Calculates rolling volatility, moving averages, and z-scores
- ✅ Backtests simple alert-based trading strategy
- ✅ Interactive dashboard with:
  - Dual-axis chart for sentiment vs. price
  - Lagged correlation visualizations
  - Sentiment distributions & custom alerts
  - Export options for CSV, PNG, and PDF

---

## 📊 Dashboard Preview

> Launch via:
```bash
streamlit run app.py
Or open in browser: http://localhost:8501

🔐 Setup Instructions

Clone the repo:
git clone https://github.com/YOUR_USERNAME/FIEP_PROJECT.git
cd FIEP_PROJECT
Create .env file (add your NewsAPI key):
echo "NEWS_API_KEY=your_key_here" > .env
Install dependencies:
pip install -r requirements.txt
Run the dashboard:
streamlit run app.py
📡 Data Sources

📈 Stock Prices: Yahoo Finance via yfinance
📰 News Articles: NewsAPI.org
🧠 Sentiment: VADER Sentiment Analysis (NLTK)
🔧 Scripts

Script	Purpose
get_news_data_daily.py	Fetch daily news for all companies
get_daily_stock_price.py	Pull stock price data
sentiment_pipeline.py	Clean & score news sentiment
aggregate_sentiment.py	Create weekly/monthly aggregates
company_csvs.py	Combine data per company
📄 License

This project is for educational purposes. Please don't share API keys or confidential data publicly.

👨‍💻 Author

Samuel Vu, Zhenyang Zhang, Jiayu Han
📍 Goethe University Frankfurt
