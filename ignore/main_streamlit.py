
import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import plotly.express as px
import io
import plotly.io as pio
from plotly.graph_objs import Figure, Scatter

# ---------------- CONFIG ----------------
DATA_DIR = "/Users/samivu/python_files/FIEP_PROJECT/company_data"
st.set_page_config(layout="wide", page_title="📊 Company Insight Dashboard")

# ------------ Load & List Companies ------------
@st.cache_data
def get_company_files():
    files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]
    return sorted(files)

# ------------ Load Data ------------
@st.cache_data
def load_company_data(filename):
    df = pd.read_csv(os.path.join(DATA_DIR, filename), parse_dates=["date"])
    return df

# ------------ UI: Sidebar ------------
st.sidebar.title("📁 Company Selection")
companies = get_company_files()
selected_file = st.sidebar.selectbox("Choose a company", companies)

show_zscore = st.sidebar.checkbox("Overlay Sentiment Z-Score", value=True)
show_alerts = st.sidebar.checkbox("Show Alerts", value=True)
show_lag_corr = st.sidebar.checkbox("Show Lagged Correlation", value=False)
alert_threshold = st.sidebar.slider("Alert Threshold (Sentiment Δ)", min_value=-1.0, max_value=0.0, step=0.05, value=-0.3)
export_csv = st.sidebar.button("⬇️ Export to CSV")
export_pdf = st.sidebar.button("📄 Export PDF Report")

# ------------ Load Selected Company ------------
df = load_company_data(selected_file)
company_name = selected_file.replace("_", " ").replace(".csv", "")

st.title(f"📈 Insights for {company_name}")

# ------------ Time Series Plot with Dual Y-Axis ------------
st.subheader("📈 Stock Price vs. Sentiment (Dual Axis)")
fig_dual = Figure()

# Primäre Y-Achse: Aktienkurs
fig_dual.add_trace(Scatter(
    x=df["date"], y=df["Close"],
    name="Stock Price", yaxis="y1"
))

# Sekundäre Y-Achse: Sentiment
fig_dual.add_trace(Scatter(
    x=df["date"], y=df["avg_sentiment"],
    name="Avg Sentiment", yaxis="y2"
))

# Layout mit 2 Achsen
fig_dual.update_layout(
    title="Stock Price and Avg Sentiment Over Time",
    xaxis=dict(title="Date"),
    yaxis=dict(title="Stock Price", side="left"),
    yaxis2=dict(title="Avg Sentiment", overlaying="y", side="right", range=[-1, 1]),
    legend=dict(x=0, y=1),
    height=500
)

st.plotly_chart(fig_dual, use_container_width=True)

# ------------ Optional: Z-Score Overlay ------------
if show_zscore and "sentiment_zscore" in df.columns:
    fig_z = px.line(df, x="date", y="sentiment_zscore", title="Sentiment Z-Score Over Time")
    st.plotly_chart(fig_z, use_container_width=True)

# ------------ Alerts Visualization ------------
df["custom_alert"] = df["sentiment_change"] <= alert_threshold
if show_alerts:
    alert_df = df[df["custom_alert"] == True]
    st.subheader(f"🚨 Custom Alerts (Sentiment Change ≤ {alert_threshold})")
    st.dataframe(alert_df[["date", "avg_sentiment", "sentiment_change", "Close", "stock_price_return"]])

# ------------ Interactive Z-Score Alert Option ------------
if "sentiment_zscore" in df.columns:
    st.sidebar.markdown("### 🔧 Z-Score Alert Settings")
    z_thresh = st.sidebar.slider("Z-Score Threshold for Alert", min_value=-3.0, max_value=0.0, step=0.1, value=-1.0)
    df["zscore_alert"] = df["sentiment_zscore"] <= z_thresh

    if st.sidebar.checkbox("Show Z-Score Alerts"):
        z_alerts = df[df["zscore_alert"] == True]
        st.subheader(f"🚨 Z-Score Alerts (Z ≤ {z_thresh})")
        st.dataframe(z_alerts[["date", "sentiment_zscore", "Close", "stock_price_return"]])

# ------------ Correlation Analysis ------------
st.subheader("📊 Correlation Analysis")
cols_to_corr = ["avg_sentiment", "sentiment_7d", "sentiment_zscore", "Close", "stock_price_return", "return_7d"]
corr_df = df[cols_to_corr].corr()
st.dataframe(corr_df.style.background_gradient(cmap='coolwarm').format("{:.2f}"))

# ------------ Lagged Correlation Plot ------------
if show_lag_corr:
    st.subheader("🔁 Lagged Correlation (Sentiment vs. Stock Return)")
    max_lag = 7
    corrs = []
    for lag in range(-max_lag, max_lag + 1):
        shifted = df["avg_sentiment"].shift(lag)
        corr = df["stock_price_return"].corr(shifted)
        corrs.append((lag, corr))
    lag_df = pd.DataFrame(corrs, columns=["Lag", "Correlation"])
    fig_lag = px.bar(lag_df, x="Lag", y="Correlation", title="Lagged Correlation")
    st.plotly_chart(fig_lag, use_container_width=True)

# ------------ Volatility Visualization ------------
st.subheader("📉 Stock & Sentiment Volatility (7d Rolling Std Dev)")
df["price_volatility"] = df["Close"].pct_change().rolling(7).std()
df["sentiment_volatility"] = df["avg_sentiment"].rolling(7).std()
fig_vol = px.line(df, x="date", y=["price_volatility", "sentiment_volatility"], title="7-Day Rolling Volatility")
fig_vol.update_layout(yaxis_title="Volatility", legend_title_text="Type")
st.plotly_chart(fig_vol, use_container_width=True)

# ------------ Moving Averages ------------
st.subheader("📊 Moving Averages on Stock Price")
df["MA_7"] = df["Close"].rolling(window=7).mean()
df["MA_30"] = df["Close"].rolling(window=30).mean()
fig_ma = px.line(df, x="date", y=["Close", "MA_7", "MA_30"], title="Stock Price with 7 & 30-Day Moving Averages")
fig_ma.update_layout(yaxis_title="Price", legend_title_text="Metric")
st.plotly_chart(fig_ma, use_container_width=True)

# ------------ Sentiment Distribution ------------
st.subheader("📊 Sentiment Distribution")
fig_hist = px.histogram(df, x="avg_sentiment", nbins=30, title="Histogram of Average Sentiment")
st.plotly_chart(fig_hist, use_container_width=True)

# ------------ Simple Backtest ------------
st.subheader("📈 Strategy Backtest (Based on Custom Alert)")
df["position"] = df["custom_alert"].replace({True: 1, False: 0}).ffill()
df["strategy_return"] = df["position"].shift() * df["stock_price_return"]
df["cumulative_strategy"] = (1 + df["strategy_return"]).cumprod()
df["cumulative_stock"] = (1 + df["stock_price_return"]).cumprod()
fig_bt = px.line(df, x="date", y=["cumulative_stock", "cumulative_strategy"], title="Cumulative Returns: Strategy vs. Stock")
fig_bt.update_layout(yaxis_title="Cumulative Return", legend_title_text="Strategy")
st.plotly_chart(fig_bt, use_container_width=True)

# ------------ Export Option ------------
if export_csv:
    st.download_button(
        label="Download Clean Data as CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=selected_file,
        mime="text/csv"
    )

# ------------ Export Chart as PNG ------------
if st.sidebar.button("📷 Export Last Chart as PNG"):
    png_bytes = pio.to_image(fig_bt, format="png")
    st.download_button(
        label="Download Chart as PNG",
        data=png_bytes,
        file_name=f"{company_name}_strategy_vs_stock.png",
        mime="image/png"
    )

# ------------ PDF Export (Basic Text Summary) ------------
if export_pdf:
    import matplotlib.backends.backend_pdf as pdf_backend
    from matplotlib.figure import Figure

    buffer = io.BytesIO()
    pdf = pdf_backend.PdfPages(buffer)

    fig1 = Figure()
    ax1 = fig1.subplots()
    df[["date", "Close"]].plot(x="date", y="Close", ax=ax1, title="Stock Price Over Time")
    pdf.savefig(fig1)

    fig2 = Figure()
    ax2 = fig2.subplots()
    df[["date", "avg_sentiment"]].plot(x="date", y="avg_sentiment", ax=ax2, title="Sentiment Over Time")
    pdf.savefig(fig2)

    pdf.close()
    buffer.seek(0)

    st.download_button(
        label="Download PDF Report",
        data=buffer,
        file_name=f"{company_name.replace(' ', '_')}_report.pdf",
        mime="application/pdf"
    )

# ------------ Footer ------------
st.markdown("---")
st.caption("Built by FIEP's BEST – Jiayu Han, Zhenyang Zhang, Samuel Vu - Sentiment & Market Intelligence Dashboard")
