import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os
from config import DAX_PRICES_FILE  # comes from config.py



# ----------- CONFIG -----------
DAX_TICKERS = {
    'Adidas': 'ADS.DE', 'Airbus': 'AIR.DE', 'Allianz': 'ALV.DE', 'BASF': 'BAS.DE',
    'Bayer': 'BAYN.DE', 'Beiersdorf': 'BEI.DE', 'BMW': 'BMW.DE', 'Brenntag': 'BNR.DE',
    'Commerzbank': 'CBK.DE', 'Continental': 'CON.DE', 'Covestro': '1COV.DE',
    'Daimler Truck': 'DTG.DE', 'Delivery Hero': 'DHER.DE', 'Deutsche Bank': 'DBK.DE',
    'Deutsche Börse': 'DB1.DE', 'Deutsche Post': 'DHL.DE', 'Deutsche Telekom': 'DTE.DE',
    'Deutsche Wohnen': 'DWNI.DE', 'E.ON': 'EOAN.DE', 'Fresenius': 'FRE.DE',
    'Fresenius Medical Care': 'FME.DE', 'Hannover Rück': 'HNR1.DE', 'Heidelberg Materials': 'HEI.DE',
    'Hellofresh': 'HFG.DE', 'Henkel': 'HEN3.DE', 'Infineon': 'IFX.DE', 'Mercedes-Benz': 'MBG.DE',
    'Merck': 'MRK.DE', 'MTU Aero Engines': 'MTX.DE', 'Münchener Rück': 'MUV2.DE',
    'Porsche AG': 'P911.DE', 'Porsche SE': 'PAH3.DE', 'Qiagen': 'QIA.DE', 'Rheinmetall': 'RHM.DE',
    'RWE': 'RWE.DE', 'SAP': 'SAP.DE', 'Sartorius': 'SRT3.DE', 'Siemens': 'SIE.DE',
    'Siemens Energy': 'ENR.DE', 'Siemens Healthineers': 'SHL.DE', 'Volkswagen': 'VOW3.DE',
    'Vonovia': 'VNA.DE', 'Zalando': 'ZAL.DE'
}

DEFAULT_START_DATE = datetime(2025, 1, 1)
END_DATE = datetime.today()
# ------------------------------

# Step 1: Determine start date
if os.path.exists(DAX_PRICES_FILE):
    df_existing = pd.read_csv(DAX_PRICES_FILE, parse_dates=["Date"])
    latest_date = df_existing["Date"].max()
    start_date = latest_date + timedelta(days=1)
    print(f"🔁 Updating from {start_date.date()} to {END_DATE.date()}")
else:
    df_existing = pd.DataFrame()
    start_date = DEFAULT_START_DATE
    print(f"🆕 Creating new database from {start_date.date()} to {END_DATE.date()}")

# Step 2: Download new data
new_data = []

for company, ticker in DAX_TICKERS.items():
    print(f"📈 Fetching {company} ({ticker})...")
    try:
        df = yf.download(ticker, start=start_date, end=END_DATE)

        if not df.empty:
            df = df.reset_index()

            # Handle MultiIndex columns (e.g., when using groupby)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join(col).strip() if col[1] else col[0] for col in df.columns]

            close_col = next((col for col in df.columns if col.lower().startswith("close")), None)
            if not close_col:
                print(f"⚠️ Could not find Close column for {ticker}")
                continue

            df = df[["Date", close_col]].rename(columns={close_col: "Close"})
            df["Company"] = company
            df["Ticker"] = ticker

            new_data.append(df)
        else:
            print(f"⚠️ No new data for {company}")
    except Exception as e:
        print(f"❌ Error fetching {company}: {e}")

# Step 3: Combine and save
if new_data:
    df_new = pd.concat(new_data, ignore_index=True)

    if not df_existing.empty:
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined.drop_duplicates(subset=["Date", "Company"], inplace=True)
    else:
        df_combined = df_new

    df_combined.sort_values(by=["Company", "Date"], inplace=True)
    df_combined.reset_index(drop=True, inplace=True)

    os.makedirs(DAX_PRICES_FILE.parent, exist_ok=True)
    df_combined.to_csv(DAX_PRICES_FILE, index=False)

    print(f"\n✅ Saved {len(df_new)} new rows. Updated CSV: {DAX_PRICES_FILE}")
else:
    print("⛔ No new data found — CSV unchanged.")
