import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="India Market Analyzer", layout="wide", initial_sidebar_state="collapsed")

# Custom Dark Theme CSS
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    div.stButton > button { width: 100%; border-radius: 5px; height: 3em; background-color: #262730; color: white; border: 1px solid #444; }
    div.stButton > button:hover { border: 1px solid #00ffcc; color: #00ffcc; }
    .metric-card { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA FETCHING ---
@st.cache_data(ttl=300)
def get_index_data():
    indices = {
        "^NSEI": "NIFTY 50",
        "^NSEBANK": "BANK NIFTY",
        "^CNXIT": "NIFTY IT",
        "^CNXAUTO": "NIFTY AUTO",
        "^CNXPHARMA": "NIFTY PHARMA",
        "^CNXMETAL": "NIFTY METAL"
    }
    data = []
    for sym, name in indices.items():
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="2d")
            if len(hist) >= 2:
                price = hist['Close'].iloc[-1]
                change = ((price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
                data.append({'sym': sym, 'name': name, 'price': price, 'change': change})
        except:
            continue
    return data

# --- APP LOGIC ---
if 'active_index' not in st.session_state:
    st.session_state.active_index = "^NSEI"
    st.session_state.active_name = "NIFTY 50"

# 1. TOP BAR (The fix for your error is here)
idx_list = get_index_data()
if idx_list:
    cols = st.columns(len(idx_list))
    for i, item in enumerate(idx_list):
        label = f"{item['name']}\n{item['price']:,.0f} ({item['change']:.2f}%)"
        if cols[i].button(label):
            st.session_state.active_index = item['sym']
            st.session_state.active_name = item['name']
else:
    st.error("Connection Error: Unable to fetch index data. Check internet.")

st.title(f"📊 {st.session_state.active_name} Analysis")

# 2. CHARTS SECTION
col_main, col_side = st.columns([3, 1])

with col_main:
    period = st.select_slider("Select Time Horizon", options=["1M", "6M", "1Y", "3Y", "5Y"], value="3Y")
    d_map = {"1M": "30d", "6M": "180d", "1Y": "365d", "3Y": "1095d", "5Y": "1825d"}
    
    df = yf.Ticker(st.session_state.active_index).history(period=d_map[period])
    
    fig = go.Figure(data=[go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        increasing_line_color='#00ffcc', decreasing_line_color='#ff4b4b'
    )])
    fig.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=20, b=20), height=500,
                      xaxis_rangeslider_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

# 3. LONG-TERM FUNDAMENTALS (Strategic for 3-year horizon)
with col_side:
    st.subheader("Stock Lookup")
    ticker_input = st.text_input("Enter NSE Ticker (e.g., RELIANCE.NS)", "TCS.NS")
    
    if st.button("Analyze Fundamentals"):
        stock = yf.Ticker(ticker_input)
        info = stock.info
        
        st.markdown(f"**{info.get('longName', 'N/A')}**")
        st.write(f"Sector: {info.get('sector', 'N/A')}")
        
        # Displaying key long-term metrics
        metrics = {
            "Trailing P/E": info.get('trailingPE'),
            "Debt to Equity": info.get('debtToEquity'),
            "ROE": info.get('returnOnEquity'),
            "Dividend Yield": info.get('dividendYield')
        }
        
        for k, v in metrics.items():
            val = f"{v:.2f}" if isinstance(v, (int, float)) else "N/A"
            st.metric(k, val)

# 4. FOOTER
st.divider()
st.caption(f"Data updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Strategy: Long-term (3Y+)")
