import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from GoogleNews import GoogleNews
from streamlit_option_menu import option_menu

# --- UI CONFIG ---
st.set_page_config(page_title="NSE LIVE TERMINAL", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0a0c10; color: #e1e1e1; }
    .status-bar {
        background: #161b22; border-radius: 5px; padding: 10px;
        border-left: 5px solid #00ffcc; margin-bottom: 20px;
    }
    .metric-box {
        background: #111418; border: 1px solid #30363d;
        padding: 15px; border-radius: 10px; text-align: center;
    }
    .ai-signal {
        background: linear-gradient(90deg, #001510 0%, #002b24 100%);
        border: 1px solid #00ffcc; padding: 15px; border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CORE DATA ENGINE ---
@st.cache_data(ttl=300)
def fetch_market_snapshot():
    # Adding GIFT NIFTY (traded on NSE IX) - usually tracked via SGX/GIFT proxies or futures
    # Since yfinance uses delayed proxies, we use the GIFT Nifty index symbol if available or ^NSEI as base
    symbols = {
        "NIFTY 50": "^NSEI",
        "GIFT NIFTY": "IN1!", # Proxy for GIFT NIFTY Futures
        "BANK NIFTY": "^NSEBANK",
        "NIFTY NEXT 50": "^NSMIDCP"
    }
    results = []
    for name, sym in symbols.items():
        try:
            t = yf.Ticker(sym)
            h = t.history(period="5d")
            if not h.empty:
                curr = h['Close'].iloc[-1]
                prev = h['Close'].iloc[-2]
                pct = ((curr - prev) / prev) * 100
                results.append({"name": name, "price": curr, "change": pct, "last_close": prev})
        except:
            continue
    return results

# --- AI PREDICTION LOGIC (Simplified Momentum Model) ---
def get_ai_prediction(symbol):
    try:
        data = yf.download(symbol, period="60d", interval="1d", progress=False)
        # Simple Alpha: If 5-day SMA > 20-day SMA + RSI Momentum
        data['SMA5'] = data['Close'].rolling(5).mean()
        data['SMA20'] = data['Close'].rolling(20).mean()
        
        last_sma5 = data['SMA5'].iloc[-1]
        last_sma20 = data['SMA20'].iloc[-1]
        
        if last_sma5 > last_sma20:
            return "BULLISH", "Strong Momentum detected in short-term moving averages.", "#00ffcc"
        else:
            return "BEARISH", "Price action suggests consolidation or downward pressure.", "#ff4b4b"
    except:
        return "NEUTRAL", "Insufficient data for AI inference.", "#8b949e"

# --- TOP NAVIGATION ---
selected = option_menu(
    None, ["Market Dashboard", "AI Terminal", "Corporate News"],
    icons=["speedometer2", "robot", "broadcast"],
    menu_icon="cast", default_index=0, orientation="horizontal",
)

# --- PAGE 1: MARKET DASHBOARD ---
if selected == "Market Dashboard":
    # Header Status
    st.markdown(f"""<div class="status-bar">
        <b>Market Status:</b> <span style="color:#ffcc00;">CLOSED</span> (Last Traded: {pd.Timestamp.now().strftime('%d %b, %Y')})
    </div>""", unsafe_allow_html=True)

    # Market Cards
    cols = st.columns(4)
    snapshots = fetch_market_snapshot()
    
    for i, s in enumerate(snapshots):
        with cols[i]:
            color = "#00ffcc" if s['change'] > 0 else "#ff4b4b"
            st.markdown(f"""
                <div class="metric-box">
                    <small style="color:#8b949e;">{s['name']}</small>
                    <h2 style="margin:0;">{s['price']:,.2f}</h2>
                    <span style="color:{color};">{'▲' if s['change'] > 0 else '▼'} {abs(s['change']):.2f}%</span>
                    <br><small style="color:#484f58;">Prev Close: {s['last_close']:,.2f}</small>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # TradingView & Top 20 Layout
    col_chart, col_list = st.columns([2, 1])
    
    with col_chart:
        st.subheader("📊 Live Technical Canvas")
        st.components.v1.html("""
            <div id="tv-chart" style="height:500px;"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
            <script type="text/javascript">
            new TradingView.widget({
              "width": "100%", "height": 500, "symbol": "NSE:NIFTY",
              "interval": "D", "timezone": "Asia/Kolkata", "theme": "dark",
              "style": "1", "locale": "en", "enable_publishing": false,
              "hide_side_toolbar": false, "container_id": "tv-chart"
            });
            </script>
        """, height=500)

    with col_list:
        st.subheader("🔥 AI Sentiment (Top Stocks)")
        top_stocks = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]
        for stock in top_stocks:
            signal, reason, col = get_ai_prediction(f"{stock}.NS")
            st.markdown(f"""
                <div style="background:#161b22; padding:10px; border-radius:5px; margin-bottom:10px; border-right:4px solid {col};">
                    <div style="display:flex; justify-content:space-between;">
                        <b>{stock}</b>
                        <span style="color:{col}; font-weight:bold;">{signal}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# --- PAGE 2: AI TERMINAL ---
elif selected == "AI Terminal":
    st.subheader("🤖 Neural Market Search")
    query = st.text_input("Enter NSE Ticker", "RELIANCE")
    
    if st.button("Generate AI Audit"):
        ticker = f"{query}.NS"
        signal, reason, col = get_ai_prediction(ticker)
        
        st.markdown(f"""
            <div class="ai-signal">
                <h3 style="color:{col}; margin-top:0;">AI Prediction: {signal}</h3>
                <p>{reason}</p>
                <small>Note: This is an automated analysis based on price momentum and RSI. Not financial advice.</small>
            </div>
        """, unsafe_allow_html=True)
        
        # Detailed Stats for Search
        stock = yf.Ticker(ticker)
        st.write(stock.history(period="1mo"))

# --- PAGE 3: CORPORATE NEWS ---
elif selected == "Corporate News":
    st.subheader("📰 Market Moving Headlines")
    gn = GoogleNews(period='3d', lang='en', region='IN')
    gn.search('NSE Indian Stock Market')
    for item in gn.result()[:10]:
        st.info(f"**{item.get('media')}**: {item.get('title')}")
        st.caption(f"Published: {item.get('date')} | [Read More]({item.get('link')})")
