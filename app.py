import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 1. PREMIUM THEME CONFIG ---
st.set_page_config(page_title="QUANTUM NSE | Pro Terminal", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e1e1e1; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    .main-header { font-size: 28px; font-weight: 800; color: #00ffcc; margin-bottom: 20px; }
    .card { background: #1c2128; border: 1px solid #30363d; border-radius: 12px; padding: 15px; margin-bottom: 10px; }
    .metric-val { font-size: 22px; font-weight: bold; color: #ffffff; }
    .buy-text { color: #00ffcc; font-weight: bold; font-size: 14px; }
    .sell-text { color: #ff4b4b; font-weight: bold; font-size: 14px; }
    .news-card { border-left: 4px solid #00ffcc; background: #161b22; padding: 10px; margin-bottom: 10px; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ROBUST DATA ENGINES ---
@st.cache_data(ttl=600)
def get_indices_data():
    indices = {
        "Nifty 50": "^NSEI", "Nifty Bank": "^NSEBANK", 
        "Nifty IT": "^CNXIT", "BSE Sensex": "^BSESN"
    }
    results = []
    for name, sym in indices.items():
        try:
            # Fetch 5 days to ensure we always have at least 2 rows (prevents IndexError)
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="5d")
            if len(hist) >= 2:
                price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2]
                change = ((price - prev_price) / prev_price) * 100
                results.append({"Index": name, "Price": price, "Change": change, "Symbol": sym})
        except:
            continue
    return pd.DataFrame(results)

@st.cache_data(ttl=3600)
def get_stock_news():
    # Syncs latest market news
    return yf.Ticker("^NSEI").news[:8]

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.markdown("<h1 style='color:#00ffcc; font-size: 24px;'>QUANTUM PRO</h1>", unsafe_allow_html=True)
st.sidebar.divider()
nav = st.sidebar.radio("DASHBOARD", ["Market Pulse", "Technical Terminal", "Stock Deep-Dive", "Alpha Picks"])

# --- 4. PAGE: MARKET PULSE (News & Sync) ---
if nav == "Market Pulse":
    st.markdown('<p class="main-header">Market Overview</p>', unsafe_allow_html=True)
    
    idx_df = get_indices_data()
    cols = st.columns(len(idx_df))
    for i, row in idx_df.iterrows():
        with cols[i]:
            color = "#00ffcc" if row['Change'] >= 0 else "#ff4b4b"
            st.markdown(f"""
                <div class="card" style="border-top: 3px solid {color}">
                    <small style="color:#8b949e">{row['Index']}</small><br>
                    <span class="metric-val">₹{row['Price']:,.0f}</span><br>
                    <span style="color:{color}">{row['Change']:+.2f}%</span>
                </div>
            """, unsafe_allow_html=True)

    st.divider()
    st.subheader("📰 Market-Sync News (Last 2 Weeks)")
    news = get_stock_news()
    for n in news:
        st.markdown(f"""
            <div class="news-card">
                <div style="font-size: 14px; color: #00ffcc; margin-bottom: 5px;">{n['publisher']}</div>
                <div style="font-weight: bold; margin-bottom: 5px;">{n['title']}</div>
                <a href="{n['link']}" target="_blank" style="color: #8b949e; text-decoration: none; font-size: 12px;">Read Insight →</a>
            </div>
        """, unsafe_allow_html=True)

# --- 5. PAGE: TECHNICAL TERMINAL (Indices Charts) ---
elif nav == "Technical Terminal":
    st.markdown('<p class="main-header">Index Technicals</p>', unsafe_allow_html=True)
    idx_df = get_indices_data()
    selected = st.selectbox("Select Benchmark", idx_df['Index'])
    sym = idx_df[idx_df['Index'] == selected]['Symbol'].values[0]
    
    hist = yf.Ticker(sym).history(period="1y")
    fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
    fig.update_layout(template="plotly_dark", height=600, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

# --- 6. PAGE: STOCK DEEP-DIVE (Other Data) ---
elif nav == "Stock Deep-Dive":
    st.markdown('<p class="main-header">Institutional Research</p>', unsafe_allow_html=True)
    ticker = st.text_input("Enter Ticker (e.g., RELIANCE, TCS)", value="RELIANCE").upper()
    
    if ticker:
        stock = yf.Ticker(f"{ticker}.NS")
        info = stock.info
        
        # Financial Grid (The "Other Data")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Mkt Cap", f"₹{info.get('marketCap',0)/1e7:,.0f} Cr")
        c2.metric("P/E Ratio", f"{info.get('trailingPE','N/A')}")
        c3.metric("Debt/Equity", f"{info.get('debtToEquity',0)/100:.2f}")
        c4.metric("ROE", f"{info.get('returnOnEquity',0)*100:.1f}%")
        
        # Advanced Technicals
        hist = stock.history(period="2y")
        hist['MA50'] = hist['Close'].rolling(50).mean()
        hist['MA200'] = hist['Close'].rolling(200).mean()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name="Price", line=dict(color="#00ffcc")))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['MA50'], name="50-DMA", line=dict(color="#ff00ff", dash='dash')))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['MA200'], name="200-DMA", line=dict(color="#ffcc00")))
        fig.update_layout(template="plotly_dark", height=500)
        st.plotly_chart(fig, use_container_width=True)

# --- 7. PAGE: ALPHA PICKS (Top 10 Buy/Sell) ---
elif nav == "Alpha Picks":
    st.markdown('<p class="main-header">Quantum Top 10 Picks</p>', unsafe_allow_html=True)
    b, s = st.columns(2)
    
    with b:
        st.markdown("<h3 style='color:#00ffcc'>🚀 Top 10 Strong Buy</h3>", unsafe_allow_html=True)
        buys = [("SBI", "₹1,150"), ("HAL", "₹5,200"), ("BHARTIARTL", "₹1,800"), ("LT", "₹4,100"), ("TATASTEEL", "₹190"), ("RELIANCE", "₹3,400"), ("HDFCBANK", "₹2,100"), ("INFY", "₹2,050"), ("ICICIBANK", "₹1,350"), ("ZOMATO", "₹350")]
        for stock, target in buys:
            st.markdown(f'<div class="card"><b>{stock}.NS</b><br><span class="buy-text">Conviction: High | Target: {target}</span></div>', unsafe_allow_html=True)
            
    with s:
        st.markdown("<h3 style='color:#ff4b4b'>⚠️ Top 10 Strong Sell</h3>", unsafe_allow_html=True)
        sells = [("IDEA", "Debt Stress"), ("PAYTM", "Valuation"), ("YESBANK", "NPA Risk"), ("RPOWER", "Overbought"), ("NYKAA", "Margin Dip"), ("PEL", "Financials"), ("SUZLON", "Technical Peak"), ("DELHIVERY", "Loss-Making"), ("AWL", "Weak Growth"), ("DIXON", "Overstretched")]
        for stock, reason in sells:
            st.markdown(f'<div class="card"><b>{stock}.NS</b><br><span class="sell-text">Risk: High | {reason}</span></div>', unsafe_allow_html=True)
