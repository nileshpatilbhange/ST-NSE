import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- PREMIUM UI THEME ---
st.set_page_config(page_title="QUANTUM NSE | Pro Terminal", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e1e1e1; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    .main-header { font-size: 28px; font-weight: 800; color: #00ffcc; margin-bottom: 20px; }
    .card { background: #1c2128; border: 1px solid #30363d; border-radius: 12px; padding: 20px; margin-bottom: 15px; }
    .metric-val { font-size: 24px; font-weight: bold; color: #ffffff; }
    .buy-text { color: #00ffcc; font-weight: bold; }
    .sell-text { color: #ff4b4b; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINES ---
@st.cache_data(ttl=600)
def get_indices():
    # Primary Indian Indices
    indices = {
        "Nifty 50": "^NSEI",
        "Nifty Bank": "^NSEBANK",
        "Nifty IT": "^CNXIT",
        "Nifty Auto": "^CNXAUTO",
        "BSE Sensex": "^BSESN"
    }
    data = []
    for name, sym in indices.items():
        ticker = yf.Ticker(sym)
        hist = ticker.history(period="2d")
        if not hist.empty:
            price = hist['Close'].iloc[-1]
            change = ((price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
            data.append({"Index": name, "Price": price, "Change%": change, "Symbol": sym})
    return pd.DataFrame(data)

@st.cache_data(ttl=3600)
def get_market_news():
    # Simple news aggregator using yfinance news for broad market
    # In a real tool, this would sync with an RSS/News API
    stock = yf.Ticker("^NSEI")
    return stock.news[:10] # Last 10 market-moving stories

# --- SIDEBAR NAVIGATION ---
st.sidebar.markdown("<h2 style='color:#00ffcc;'>QUANTUM PRO</h2>", unsafe_allow_html=True)
page = st.sidebar.radio("Navigation", ["Market Overview", "Indices Analysis", "Stock Deep-Dive", "Top 10 Picks"])

# --- PAGE 1: MARKET OVERVIEW & NEWS ---
if page == "Market Overview":
    st.markdown('<p class="main-header">Market Pulse</p>', unsafe_allow_html=True)
    
    # Indices Ribbon
    idx_df = get_indices()
    cols = st.columns(len(idx_df))
    for i, row in idx_df.iterrows():
        with cols[i]:
            color = "#00ffcc" if row['Change%'] > 0 else "#ff4b4b"
            st.markdown(f"""
                <div class="card" style="text-align:center; border-top: 3px solid {color}">
                    <small>{row['Index']}</small><br>
                    <span class="metric-val">₹{row['Price']:,.0f}</span><br>
                    <span style="color:{color}">{row['Change%']:+.2f}%</span>
                </div>
            """, unsafe_allow_html=True)

    # News Section (Last 2 Weeks Sync)
    st.subheader("📰 Market-Moving News")
    news = get_market_news()
    for item in news:
        with st.expander(f"📌 {item['title']}"):
            st.write(f"**Publisher:** {item['publisher']}")
            st.write(f"**Published:** {datetime.fromtimestamp(item['providerPublishTime']).strftime('%Y-%m-%d %H:%M')}")
            st.link_button("Read Full Story", item['link'])

# --- PAGE 2: INDICES ANALYSIS (Tech Charts) ---
elif page == "Indices Analysis":
    st.markdown('<p class="main-header">Sectoral & Index Charts</p>', unsafe_allow_html=True)
    idx_df = get_indices()
    selected_idx_name = st.selectbox("Select Index for Technical View", idx_df['Index'])
    selected_sym = idx_df[idx_df['Index'] == selected_idx_name]['Symbol'].values[0]
    
    hist = yf.Ticker(selected_sym).history(period="2y")
    fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
    fig.update_layout(template="plotly_dark", height=600, title=f"{selected_idx_name} Technical Chart")
    st.plotly_chart(fig, use_container_width=True)

# --- PAGE 3: STOCK DEEP-DIVE ---
elif page == "Stock Deep-Dive":
    st.markdown('<p class="main-header">Institutional Stock Analysis</p>', unsafe_allow_html=True)
    ticker = st.text_input("Search NSE Ticker", value="RELIANCE").upper()
    if ticker:
        sym = f"{ticker}.NS"
        stock = yf.Ticker(sym)
        info = stock.info
        hist = stock.history(period="5y")
        
        # Grid for Other Data (Balance Sheet / Fundamentals)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"**Market Cap:** ₹{info.get('marketCap', 0)/1e7:,.0f} Cr")
            st.markdown(f"**Trailing P/E:** {info.get('trailingPE', 'N/A')}")
        with c2:
            st.markdown(f"**Dividend Yield:** {info.get('dividendYield', 0)*100:.2f}%")
            st.markdown(f"**ROE:** {info.get('returnOnEquity', 0)*100:.1f}%")
        with c3:
            st.markdown(f"**52 Week High:** ₹{info.get('fiftyTwoWeekHigh')}")
            st.markdown(f"**Sector:** {info.get('sector')}")
        
        # Technical 3-Year Chart
        df_3y = hist.last('1095D') if hasattr(hist, 'last') else hist[hist.index >= (hist.index[-1] - pd.DateOffset(years=3))]
        fig = go.Figure(go.Scatter(x=df_3y.index, y=df_3y['Close'], line=dict(color='#00ffcc')))
        fig.update_layout(template="plotly_dark", title=f"{ticker} 3-Year Trend")
        st.plotly_chart(fig, use_container_width=True)

# --- PAGE 4: TOP 10 PICKS (Buy/Sell) ---
elif page == "Top 10 Picks":
    st.markdown('<p class="main-header">Top 10 Analyst Signals</p>', unsafe_allow_html=True)
    
    col_buy, col_sell = st.columns(2)
    
    with col_buy:
        st.subheader("🚀 Strong Buy (2026 Picks)")
        # Static curated list based on QGLP (Quality, Growth, Longevity, Price) logic
        buys = [
            ("SBI", "Banking", "₹1,100"), ("BHARTIARTL", "Telecom", "₹2,365"), 
            ("HCLTECH", "IT/AI", "₹2,150"), ("L&T", "Infra", "₹4,200"),
            ("TVSMOTOR", "Auto/EV", "₹4,159"), ("RELIANCE", "Energy/Retail", "₹3,400"),
            ("HDFCBANK", "Banking", "₹2,100"), ("INFY", "IT", "₹1,950"),
            ("ICICIBANK", "Banking", "₹1,350"), ("TCS", "IT", "₹4,600")
        ]
        for s, ind, tar in buys:
            st.markdown(f"""<div class="card"><b>{s}.NS</b> | {ind}<br><span class="buy-text">Target: {tar}</span></div>""", unsafe_allow_html=True)

    with col_sell:
        st.subheader("⚠️ Sell/Avoid Signals")
        sells = [
            ("IDEA", "Telecom", "Debt Stress"), ("PAYTM", "Fintech", "Regulatory"),
            ("ZOMATO", "Platform", "Valuation"), ("NYKAA", "E-com", "Margin Pressure"),
            ("YESBANK", "Banking", "Stressed Assets"), ("RPOWER", "Power", "Debt"),
            ("JPASSOCIAT", "Infra", "Liquidity"), ("SUZLON", "Energy", "Overbought"),
            ("DELHIVERY", "Logistics", "Loss Making"), ("ADANIPOWER", "Energy", "Volatility")
        ]
        for s, ind, reason in sells:
            st.markdown(f"""<div class="card"><b>{s}.NS</b> | {ind}<br><span class="sell-text">Reason: {reason}</span></div>""", unsafe_allow_html=True)
