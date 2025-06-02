'''
# Optimized Streamlit dashboard with spinners, modular layout, and advanced features

import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.io as pio
from plotly.graph_objs import Figure, Scatter, Candlestick
import io
from pathlib import Path
import sys

# ---------------- CONFIG ----------------
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import COMPANY_DATA_DIR

DATA_DIR = Path(COMPANY_DATA_DIR)

st.set_page_config(layout="wide", page_title="📊 Company Insight Dashboard")

# ------------ Load & List Companies ------------
@st.cache_data
def get_company_files():
    if not DATA_DIR.exists() or not DATA_DIR.is_dir():
        return []
    return sorted([f.name for f in DATA_DIR.glob("*.csv")])


@st.cache_data
def load_company_data(filename):
    return pd.read_csv(os.path.join(DATA_DIR, filename), parse_dates=["date"])

# ------------ Sidebar ------------
st.sidebar.title("📁 Company Selection")
companies = get_company_files()
if not companies:
    st.warning(f"⚠️ No .csv files found in {DATA_DIR}")
    st.stop()
else:
    selected_file = st.sidebar.selectbox("Choose a company", companies)

selected_file = st.sidebar.selectbox("Choose a company", companies)
date_range = st.sidebar.radio("Select Date Range", ["All", "YTD", "1 Year", "3 Years"], index=0)
show_zscore = st.sidebar.checkbox("Overlay Sentiment Z-Score", value=True)
show_alerts = st.sidebar.checkbox("Show Alerts", value=True)
show_lag_corr = st.sidebar.checkbox("Show Lagged Correlation", value=False)
show_candlesticks = st.sidebar.checkbox("Show Candlestick Chart", value=False)
alert_threshold = st.sidebar.slider("Alert Threshold (Sentiment Δ)", -1.0, 0.0, step=0.05, value=-0.3)
export_csv = st.sidebar.button("⬇️ Export to CSV")
export_pdf = st.sidebar.button("📄 Export PDF Report")

# ------------ Load Data ------------
with st.spinner("Loading company data..."):
    df = load_company_data(selected_file)
    company_name = selected_file.replace("_", " ").replace(".csv", "")

    # Filter by date range
    if date_range != "All":
        max_date = df["date"].max()
        if date_range == "YTD":
            min_date = pd.to_datetime(f"{max_date.year}-01-01")
        elif date_range == "1 Year":
            min_date = max_date - pd.DateOffset(years=1)
        elif date_range == "3 Years":
            min_date = max_date - pd.DateOffset(years=3)
        df = df[df["date"] >= min_date]

    st.title(f"📈 Insights for {company_name}")

# ------------ Main Price Chart ------------
st.subheader("📈 Stock Price vs. Sentiment (Dual Axis)")
fig_dual = Figure()
fig_dual.add_trace(Scatter(x=df["date"], y=df["Close"], name="Stock Price", yaxis="y1"))
fig_dual.add_trace(Scatter(x=df["date"], y=df["avg_sentiment"], name="Avg Sentiment", yaxis="y2"))
fig_dual.update_layout(
    xaxis=dict(title="Date"),
    yaxis=dict(title="Stock Price", side="left"),
    yaxis2=dict(title="Avg Sentiment", overlaying="y", side="right", range=[-1, 1]),
    height=500
)
st.plotly_chart(fig_dual, use_container_width=True)

# ------------ Candlestick Chart ------------
if show_candlesticks and {"Open", "High", "Low", "Close"}.issubset(df.columns):
    st.subheader("📉 Candlestick Chart")
    fig_candle = Figure(data=[Candlestick(
        x=df["date"],
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"]
    )])
    fig_candle.update_layout(title="Candlestick Price Chart", xaxis_title="Date", yaxis_title="Price")
    st.plotly_chart(fig_candle, use_container_width=True)

# ------------ Z-Score Overlay ------------
if show_zscore and "sentiment_zscore" in df.columns:
    st.plotly_chart(px.line(df, x="date", y="sentiment_zscore", title="Sentiment Z-Score Over Time"), use_container_width=True)

# ------------ Alerts ------------
df["custom_alert"] = df["sentiment_change"] <= alert_threshold
if show_alerts:
    st.subheader(f"🚨 Alerts (Δ ≤ {alert_threshold})")
    st.dataframe(df[df["custom_alert"]][["date", "avg_sentiment", "sentiment_change", "Close", "stock_price_return"]])

# ------------ Z-Score Alerts ------------
if "sentiment_zscore" in df.columns:
    st.sidebar.markdown("### 🔧 Z-Score Alert Settings")
    z_thresh = st.sidebar.slider("Z-Score Alert Threshold", -3.0, 0.0, step=0.1, value=-1.0)
    df["zscore_alert"] = df["sentiment_zscore"] <= z_thresh
    if st.sidebar.checkbox("Show Z-Score Alerts"):
        st.subheader(f"🚨 Z-Score Alerts (Z ≤ {z_thresh})")
        st.dataframe(df[df["zscore_alert"]][["date", "sentiment_zscore", "Close", "stock_price_return"]])

# ------------ Correlation ------------
st.subheader("📊 Correlation Matrix")
cols = ["avg_sentiment", "sentiment_7d", "sentiment_zscore", "Close", "stock_price_return", "return_7d"]
st.dataframe(df[cols].corr().style.background_gradient(cmap='coolwarm').format("{:.2f}"))

# ------------ Lagged Correlation ------------
if show_lag_corr:
    st.subheader("🔁 Lagged Correlation")
    max_lag = 7
    lag_data = [(lag, df["stock_price_return"].corr(df["avg_sentiment"].shift(lag))) for lag in range(-max_lag, max_lag+1)]
    st.plotly_chart(px.bar(pd.DataFrame(lag_data, columns=["Lag", "Correlation"]), x="Lag", y="Correlation", title="Lagged Correlation"), use_container_width=True)

# ------------ Volatility ------------
st.subheader("📉 7d Rolling Volatility")
df["price_volatility"] = df["Close"].pct_change().rolling(7).std()
df["sentiment_volatility"] = df["avg_sentiment"].rolling(7).std()
st.plotly_chart(px.line(df, x="date", y=["price_volatility", "sentiment_volatility"], title="Rolling Volatility"), use_container_width=True)

# ------------ Moving Averages ------------
st.subheader("📊 Moving Averages")
df["MA_7"] = df["Close"].rolling(7).mean()
df["MA_30"] = df["Close"].rolling(30).mean()
st.plotly_chart(px.line(df, x="date", y=["Close", "MA_7", "MA_30"], title="7 & 30-Day MAs"), use_container_width=True)

# ------------ Sentiment Histogram ------------
st.subheader("📊 Sentiment Distribution")
st.plotly_chart(px.histogram(df, x="avg_sentiment", nbins=30, title="Histogram of Sentiment"), use_container_width=True)

# ------------ Strategy Backtest ------------
st.subheader("📈 Strategy Backtest")
df["position"] = df["custom_alert"].replace({True: 1, False: 0}).ffill()
df["strategy_return"] = df["position"].shift() * df["stock_price_return"]
df["cumulative_strategy"] = (1 + df["strategy_return"]).cumprod()
df["cumulative_stock"] = (1 + df["stock_price_return"]).cumprod()
fig_bt = px.line(df, x="date", y=["cumulative_stock", "cumulative_strategy"], title="Cumulative Strategy vs. Stock")
fig_bt.update_layout(yaxis_title="Cumulative Return")
st.plotly_chart(fig_bt, use_container_width=True)

# ------------ Export Section ------------
if export_csv:
    st.download_button("Download CSV", df.to_csv(index=False).encode("utf-8"), selected_file, "text/csv")
if st.sidebar.button("📷 Export Chart as PNG"):
    st.download_button("Download Chart as PNG", pio.to_image(fig_bt, format="png"), f"{company_name}_chart.png", "image/png")

# ------------ Footer ------------
st.markdown("---")
st.caption("Optimized by FIEP Team – Jiayu Han, Zhenyang Zhang, Samuel Vu")
'''






import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
from plotly.graph_objs import Figure, Scatter, Candlestick
from pathlib import Path
import sys

# ---------------- CONFIG ----------------
try:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from config import COMPANY_DATA_DIR
except ImportError:
    st.error("Could not import COMPANY_DATA_DIR from config.py")
    st.stop()

DATA_DIR = Path(COMPANY_DATA_DIR).resolve()  # Convert to absolute path

st.set_page_config(layout="wide", page_title="📊 Company Insight Dashboard")

# ------------ Helper Functions ------------
@st.cache_data
def get_company_files():
    """Get list of available company data files with error handling"""
    try:
        if not DATA_DIR.exists():
            st.error(f"Data directory not found: {DATA_DIR}")
            return []
        
        csv_files = [f.name for f in DATA_DIR.glob("*.csv") if f.is_file()]
        if not csv_files:
            st.error(f"No CSV files found in {DATA_DIR}")
        return sorted(csv_files)
    except Exception as e:
        st.error(f"Error listing company files: {str(e)}")
        return []

@st.cache_data
def load_company_data(filename):
    """Load company data with robust error handling"""
    try:
        file_path = DATA_DIR / filename
        if not file_path.exists():
            st.error(f"File not found: {file_path}")
            return pd.DataFrame()
        
        df = pd.read_csv(file_path, parse_dates=["date"])
        if df.empty:
            st.error(f"Empty dataframe loaded from {filename}")
        return df
    except Exception as e:
        st.error(f"Error loading {filename}: {str(e)}")
        return pd.DataFrame()

# ------------ Sidebar ------------
st.sidebar.title("📁 Company Selection")
companies = get_company_files()

if not companies:
    st.error(f"⚠️ No valid company data files found in {DATA_DIR}")
    st.stop()

selected_file = st.sidebar.selectbox("Choose a company", companies)
date_range = st.sidebar.radio("Select Date Range", ["All", "YTD", "1 Year", "3 Years"], index=0)
show_zscore = st.sidebar.checkbox("Overlay Sentiment Z-Score", value=True)
show_alerts = st.sidebar.checkbox("Show Alerts", value=True)
show_lag_corr = st.sidebar.checkbox("Show Lagged Correlation", value=False)
show_candlesticks = st.sidebar.checkbox("Show Candlestick Chart", value=False)
alert_threshold = st.sidebar.slider("Alert Threshold (Sentiment Δ)", -1.0, 0.0, step=0.05, value=-0.3)
export_csv = st.sidebar.button("⬇️ Export to CSV")
export_pdf = st.sidebar.button("📄 Export PDF Report")

# ------------ Load Data ------------
with st.spinner(f"Loading {selected_file}..."):
    df = load_company_data(selected_file)
    
    if df.empty:
        st.error("No data loaded - cannot continue")
        st.stop()
    
    company_name = selected_file.replace("_", " ").replace(".csv", "")

    # Filter by date range
    if date_range != "All":
        max_date = df["date"].max()
        if date_range == "YTD":
            min_date = pd.to_datetime(f"{max_date.year}-01-01")
        elif date_range == "1 Year":
            min_date = max_date - pd.DateOffset(years=1)
        elif date_range == "3 Years":
            min_date = max_date - pd.DateOffset(years=3)
        df = df[df["date"] >= min_date]

    st.title(f"📈 Insights for {company_name}")

# ------------ Main Price Chart ------------
try:
    st.subheader("📈 Stock Price vs. Sentiment (Dual Axis)")
    fig_dual = Figure()
    fig_dual.add_trace(Scatter(x=df["date"], y=df["Close"], name="Stock Price", yaxis="y1"))
    fig_dual.add_trace(Scatter(x=df["date"], y=df["avg_sentiment"], name="Avg Sentiment", yaxis="y2"))
    fig_dual.update_layout(
        xaxis=dict(title="Date"),
        yaxis=dict(title="Stock Price", side="left"),
        yaxis2=dict(title="Avg Sentiment", overlaying="y", side="right", range=[-1, 1]),
        height=500
    )
    st.plotly_chart(fig_dual, use_container_width=True)
except Exception as e:
    st.error(f"Error creating price chart: {str(e)}")

# ------------ Candlestick Chart ------------
if show_candlesticks:
    try:
        required_columns = {"Open", "High", "Low", "Close"}
        if required_columns.issubset(df.columns):
            st.subheader("📉 Candlestick Chart")
            fig_candle = Figure(data=[Candlestick(
                x=df["date"],
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"]
            )])
            fig_candle.update_layout(title="Candlestick Price Chart", xaxis_title="Date", yaxis_title="Price")
            st.plotly_chart(fig_candle, use_container_width=True)
        else:
            st.warning("Candlestick chart disabled - missing required price columns")
    except Exception as e:
        st.error(f"Error creating candlestick chart: {str(e)}")

# ------------ Z-Score Overlay ------------
if show_zscore:
    try:
        if "sentiment_zscore" in df.columns:
            st.plotly_chart(px.line(df, x="date", y="sentiment_zscore", title="Sentiment Z-Score Over Time"), 
                           use_container_width=True)
        else:
            st.warning("Z-score data not available in this dataset")
    except Exception as e:
        st.error(f"Error creating Z-score chart: {str(e)}")

# ------------ Alerts ------------
try:
    df["custom_alert"] = df["sentiment_change"] <= alert_threshold
    if show_alerts:
        st.subheader(f"🚨 Alerts (Δ ≤ {alert_threshold})")
        alert_cols = ["date", "avg_sentiment", "sentiment_change", "Close", "stock_price_return"]
        available_cols = [col for col in alert_cols if col in df.columns]
        st.dataframe(df[df["custom_alert"]][available_cols])
except Exception as e:
    st.error(f"Error generating alerts: {str(e)}")

# ------------ Z-Score Alerts ------------
if "sentiment_zscore" in df.columns:
    try:
        st.sidebar.markdown("### 🔧 Z-Score Alert Settings")
        z_thresh = st.sidebar.slider("Z-Score Alert Threshold", -3.0, 0.0, step=0.1, value=-1.0)
        df["zscore_alert"] = df["sentiment_zscore"] <= z_thresh
        if st.sidebar.checkbox("Show Z-Score Alerts"):
            st.subheader(f"🚨 Z-Score Alerts (Z ≤ {z_thresh})")
            st.dataframe(df[df["zscore_alert"]][["date", "sentiment_zscore", "Close", "stock_price_return"]])
    except Exception as e:
        st.error(f"Error processing Z-score alerts: {str(e)}")

# ------------ Correlation ------------
try:
    st.subheader("📊 Correlation Matrix")
    possible_cols = ["avg_sentiment", "sentiment_7d", "sentiment_zscore", "Close", "stock_price_return", "return_7d"]
    available_cols = [col for col in possible_cols if col in df.columns]
    
    if len(available_cols) >= 2:  # Need at least 2 columns for correlation
        corr_df = df[available_cols].corr()
        st.dataframe(corr_df.style.background_gradient(cmap='coolwarm').format("{:.2f}"))
    else:
        st.warning("Not enough numeric columns available for correlation matrix")
except Exception as e:
    st.error(f"Error generating correlation matrix: {str(e)}")

# ------------ Lagged Correlation ------------
if show_lag_corr:
    try:
        st.subheader("🔁 Lagged Correlation")
        max_lag = 7
        if "avg_sentiment" in df.columns and "stock_price_return" in df.columns:
            lag_data = [(lag, df["stock_price_return"].corr(df["avg_sentiment"].shift(lag))) 
                       for lag in range(-max_lag, max_lag+1)]
            st.plotly_chart(px.bar(pd.DataFrame(lag_data, columns=["Lag", "Correlation"]), 
                           x="Lag", y="Correlation", title="Lagged Correlation"), 
                           use_container_width=True)
        else:
            st.warning("Required columns missing for lagged correlation")
    except Exception as e:
        st.error(f"Error creating lagged correlation: {str(e)}")

# ------------ Volatility ------------
try:
    st.subheader("📉 7d Rolling Volatility")
    if "Close" in df.columns:
        df["price_volatility"] = df["Close"].pct_change().rolling(7).std()
    if "avg_sentiment" in df.columns:
        df["sentiment_volatility"] = df["avg_sentiment"].rolling(7).std()
    
    plot_cols = []
    if "price_volatility" in df.columns:
        plot_cols.append("price_volatility")
    if "sentiment_volatility" in df.columns:
        plot_cols.append("sentiment_volatility")
    
    if plot_cols:
        st.plotly_chart(px.line(df, x="date", y=plot_cols, title="Rolling Volatility"), 
                       use_container_width=True)
    else:
        st.warning("No volatility data available")
except Exception as e:
    st.error(f"Error calculating volatility: {str(e)}")

# ------------ Moving Averages ------------
try:
    st.subheader("📊 Moving Averages")
    if "Close" in df.columns:
        df["MA_7"] = df["Close"].rolling(7).mean()
        df["MA_30"] = df["Close"].rolling(30).mean()
        st.plotly_chart(px.line(df, x="date", y=["Close", "MA_7", "MA_30"], 
                       title="7 & 30-Day MAs"), use_container_width=True)
    else:
        st.warning("Close price data missing - cannot calculate MAs")
except Exception as e:
    st.error(f"Error calculating moving averages: {str(e)}")

# ------------ Sentiment Histogram ------------
try:
    st.subheader("📊 Sentiment Distribution")
    if "avg_sentiment" in df.columns:
        st.plotly_chart(px.histogram(df, x="avg_sentiment", nbins=30, 
                       title="Histogram of Sentiment"), use_container_width=True)
    else:
        st.warning("Sentiment data not available")
except Exception as e:
    st.error(f"Error creating sentiment histogram: {str(e)}")

# ------------ Strategy Backtest ------------
try:
    st.subheader("📈 Strategy Backtest")
    if all(col in df.columns for col in ["custom_alert", "stock_price_return"]):
        df["position"] = df["custom_alert"].replace({True: 1, False: 0}).ffill()
        df["strategy_return"] = df["position"].shift() * df["stock_price_return"]
        df["cumulative_strategy"] = (1 + df["strategy_return"]).cumprod()
        df["cumulative_stock"] = (1 + df["stock_price_return"]).cumprod()
        fig_bt = px.line(df, x="date", y=["cumulative_stock", "cumulative_strategy"], 
                        title="Cumulative Strategy vs. Stock")
        fig_bt.update_layout(yaxis_title="Cumulative Return")
        st.plotly_chart(fig_bt, use_container_width=True)
    else:
        st.warning("Required columns missing for strategy backtest")
except Exception as e:
    st.error(f"Error running strategy backtest: {str(e)}")

# ------------ Export Section ------------
if export_csv:
    try:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=selected_file,
            mime="text/csv"
        )
    except Exception as e:
        st.error(f"Error exporting CSV: {str(e)}")

if st.sidebar.button("📷 Export Chart as PNG"):
    try:
        img_bytes = pio.to_image(fig_bt, format="png")
        st.download_button(
            label="Download Chart as PNG",
            data=img_bytes,
            file_name=f"{company_name}_chart.png",
            mime="image/png"
        )
    except Exception as e:
        st.error(f"Error exporting chart: {str(e)}")

# ------------ Footer ------------
st.markdown("---")
st.caption("Optimized by FIEP Team – Jiayu Han, Zhenyang Zhang, Samuel Vu")







