import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- STABILITY LAYER (The 2026 Fix) ---
def get_secure_session():
    session = Session()
    # Mimics a modern browser to bypass throttling
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    })
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session

# --- UI CONFIGURATION ---
st.set_page_config(page_title="QUANTUM NSE | AI Terminal", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #ffffff; }
    .brand-container { text-align: center; padding: 25px 0; background: #161b22; border-radius: 0 0 30px 30px; border-bottom: 2px solid #00ffcc; margin-bottom: 20px; }
    .logo-text { font-size: 38px; font-weight: 800; color: #00ffcc; margin: 0; }
    .stat-box { background: #1c2128; border: 1px solid #30363d; border-radius: 12px; padding: 15px; text-align: center; }
    .metric-label { font-size: 11px; color: #8b949e; text-transform: uppercase; }
    .metric-value { font-size: 22px; font-weight: bold; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- BRANDING ---
st.markdown('<div class="brand-container"><div class="logo-text">⚡ QUANTUM NSE PRO</div><div style="color:#8b949e">Institutional AI Analysis for Indian Markets</div></div>', unsafe_allow_html=True)

# --- DATA FETCHING ---
@st.cache_data(ttl=600)
def fetch_analysis(ticker):
    session = get_secure_session()
    sym = f"{ticker}.NS" # Automatically appends National Stock Exchange suffix
    try:
        stock = yf.Ticker(sym, session=session)
        # Fetch 5 years of data for a 3-year context
        hist = stock.history(period="5y")
        if hist.empty:
            return None, None, "No data found. Check ticker spelling."
        
        info = stock.info
        return hist, info, None
    except Exception as e:
        return None, None, str(e)

# --- MAIN INTERFACE ---
ticker_input = st.text_input("Enter NSE Ticker", value="RELIANCE").upper()

if ticker_input:
    with st.spinner(f"Running 3-Year Projection for {ticker_input}..."):
        df, info, error = fetch_analysis(ticker_input)
        
        if error:
            st.error(f"Connection Alert: {error}")
            st.info("Tip: If connection fails, wait 30 seconds and refresh. Yahoo Finance is sensitive to request frequency.")
        else:
            # 1. CORE METRICS GRID
            c1, c2, c3, c4 = st.columns(4)
            current_price = df['Close'].iloc[-1]
            
            with c1:
                st.markdown(f'<div class="stat-box"><p class="metric-label">Current Price</p><p class="metric-value">₹{current_price:,.2f}</p></div>', unsafe_allow_html=True)
            with c2:
                pe = info.get('trailingPE', 0)
                st.markdown(f'<div class="stat-box"><p class="metric-label">P/E Ratio</p><p class="metric-value" style="color:{"#00ffcc" if pe < 30 else "#ff4b4b"}">{pe:.2f}</p></div>', unsafe_allow_html=True)
            with c3:
                roe = info.get('returnOnEquity', 0) * 100
                st.markdown(f'<div class="stat-box"><p class="metric-label">ROE (Efficiency)</p><p class="metric-value">{roe:.1f}%</p></div>', unsafe_allow_html=True)
            with c4:
                debt = info.get('debtToEquity', 0)
                st.markdown(f'<div class="stat-box"><p class="metric-label">Debt/Equity</p><p class="metric-value" style="color:{"#00ffcc" if debt < 100 else "#ff4b4b"}">{debt/100:.2f}</p></div>', unsafe_allow_html=True)

            # 2. THE 3-YEAR INVESTMENT CHART
            st.subheader("📈 3-Year Growth & Support Analysis")
            
            # Calculate Technicals for Long-Term Entry
            df['MA200'] = df['Close'].rolling(window=200).mean()
            df_3y = df.last('1095D') # Exactly 3 years
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_3y.index, y=df_3y['Close'], name="Share Price", line=dict(color='#00ffcc', width=2.5)))
            fig.add_trace(go.Scatter(x=df_3y.index, y=df_3y['MA200'], name="200-Day Support", line=dict(color='#ffcc00', width=1.5, dash='dot')))
            
            fig.update_layout(template="plotly_dark", height=500, hovermode="x unified", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

            # 3. AI INVESTMENT VERDICT
            st.divider()
            st.subheader("🎯 3-Year Outlook")
            
            v1, v2 = st.columns(2)
            with v1:
                # Logic: Price > 200 DMA is the standard long-term health check
                is_above_ma = current_price > df['MA200'].iloc[-1]
                if is_above_ma:
                    st.success("✅ **STRENGTH:** Stock is in a major long-term uptrend.")
                else:
                    st.warning("⚠️ **WEAKNESS:** Stock is currently trading below its long-term average.")
            
            with v2:
                # Check Profitability for 3Y holding
                if roe > 15:
                    st.success("✅ **EFFICIENCY:** High ROE suggests strong management of capital.")
                else:
                    st.info("ℹ️ **MARGINS:** Capital efficiency is moderate; check industry peers.")

            # 4. FUNDAMENTAL TABLE
            st.subheader("📊 Financial Snapshot")
            fin_data = {
                "Metric": ["Dividend Yield", "Market Cap (Cr)", "Book Value", "52-Week High", "52-Week Low"],
                "Value": [
                    f"{info.get('dividendYield', 0)*100:.2f}%",
                    f"₹{info.get('marketCap', 0)/1e7:,.0f}",
                    f"₹{info.get('bookValue', 0)}",
                    f"₹{info.get('fiftyTwoWeekHigh', 0)}",
                    f"₹{info.get('fiftyTwoWeekLow', 0)}"
                ]
            }
            st.table(pd.DataFrame(fin_data))
