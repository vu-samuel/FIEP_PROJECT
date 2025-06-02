
# Optimized Streamlit dashboard with spinners, modular layout, and config-based data path

import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.io as pio
from plotly.graph_objs import Figure, Scatter
import io

# ---------------- CONFIG ----------------
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent))
from config import COMPANY_DATA_DIR as DATA_DIR

st.set_page_config(layout="wide", page_title="📊 Company Insight Dashboard")

# ------------ Load & List Companies ------------
@st.cache_data
def get_company_files():
    return sorted([f for f in os.listdir(DATA_DIR) if f.endswith(".csv")])

@st.cache_data
def load_company_data(filename):
    return pd.read_csv(os.path.join(DATA_DIR, filename), parse_dates=["date"])

# ------------ Sidebar ------------
st.sidebar.title("📁 Company Selection")
companies = get_company_files()
selected_file = st.sidebar.selectbox("Choose a company", companies)
show_zscore = st.sidebar.checkbox("Overlay Sentiment Z-Score", value=True)
show_alerts = st.sidebar.checkbox("Show Alerts", value=True)
show_lag_corr = st.sidebar.checkbox("Show Lagged Correlation", value=False)
alert_threshold = st.sidebar.slider("Alert Threshold (Sentiment Δ)", -1.0, 0.0, step=0.05, value=-0.3)
export_csv = st.sidebar.button("⬇️ Export to CSV")
export_pdf = st.sidebar.button("📄 Export PDF Report")

# ------------ Load Data ------------
with st.spinner("Loading company data..."):
    df = load_company_data(selected_file)
    company_name = selected_file.replace("_", " ").replace(".csv", "")
    st.title(f"📈 Insights for {company_name}")

# ------------ Dual Y-Axis Plot ------------
st.subheader("📈 Stock Price vs. Sentiment (Dual Axis)")
fig_dual = Figure()
fig_dual.add_trace(Scatter(x=df["date"], y=df["Close"], name="Stock Price", yaxis="y1"))
fig_dual.add_trace(Scatter(x=df["date"], y=df["avg_sentiment"], name="Avg Sentiment", yaxis="y2"))
fig_dual.update_layout(
    title="Stock Price and Avg Sentiment Over Time",
    xaxis=dict(title="Date"),
    yaxis=dict(title="Stock Price", side="left"),
    yaxis2=dict(title="Avg Sentiment", overlaying="y", side="right", range=[-1, 1]),
    legend=dict(x=0, y=1),
    height=500
)
st.plotly_chart(fig_dual, use_container_width=True)

# ------------ Optional Z-Score Overlay ------------
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

