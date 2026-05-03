import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from GoogleNews import GoogleNews
from streamlit_option_menu import option_menu

# --- UI CONFIGURATION ---
st.set_page_config(page_title="QUANTUM NSE | Pro Terminal", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS FOR BRANDING & UI ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .brand-title { color: #00ffcc; font-size: 32px; font-weight: 800; margin-bottom: 0px; }
    .brand-tagline { color: #8b949e; font-size: 14px; margin-bottom: 25px; }
    .index-card {
        background: #161b22; border: 1px solid #30363d; border-radius: 8px;
        padding: 15px; text-align: center; cursor: pointer; transition: 0.2s;
    }
    .index-card:hover { border-color: #00ffcc; background: #1c2128; }
    .stat-label { color: #8b949e; font-size: 12px; text-transform: uppercase; }
    .price-val { font-size: 20px; font-weight: bold; margin: 5px 0; }
    /* Detailed Result Box */
    .result-container {
        background: #0d1117; border: 1px solid #00ffcc; border-radius: 12px;
        padding: 25px; margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- BRANDING HEADER ---
st.markdown('<p class="brand-title">⚡ QUANTUM NSE</p>', unsafe_allow_html=True)
st.markdown('<p class="brand-tagline">Advanced AI-Powered Analytics for the Indian Capital Markets</p>', unsafe_allow_html=True)

# --- NAVIGATION ---
selected = option_menu(
    menu_title=None,
    options=["Market Overview", "News-Based Stocks"],
    icons=["graph-up", "newspaper"],
    orientation="horizontal",
    styles={
        "container": {"background-color": "#161b22", "padding": "0"},
        "nav-link": {"font-size": "14px", "color": "#8b949e"},
        "nav-link-selected": {"background-color": "#00ffcc", "color": "#0d1117", "font-weight": "bold"},
    }
)

# --- DATA HELPERS ---
@st.cache_data(ttl=300)
def get_market_indices():
    indices = {
        "Nifty 50": "^NSEI", "Nifty Next 50": "^NSMIDCP", 
        "Bank Nifty": "^NSEBANK", "Nifty Midcap": "NIFTY_MIDCAP_100.NS",
        "GIFT Nifty": "IN1!" 
    }
    data = {}
    for name, sym in indices.items():
        try:
            t = yf.Ticker(sym)
            h = t.history(period="2d")
            if not h.empty:
                curr, prev = h['Close'].iloc[-1], h['Close'].iloc[-2]
                change = ((curr - prev) / prev) * 100
                data[name] = {"price": curr, "change": change, "sym": sym}
        except: continue
    return data

# --- PAGE 1: MARKET OVERVIEW ---
if selected == "Market Overview":
    # 1. SEARCH BAR (Detailed Result on same page)
    col_search, col_news_link = st.columns([4, 1])
    with col_search:
        search_query = st.text_input("", placeholder="🔍 Search Stock (e.g. RELIANCE, TCS, SBIN)...").upper()
    with col_news_link:
        st.write(" ") # alignment
        if st.button("🔥 News Stocks"):
            st.info("Check the 'News-Based Stocks' tab for high-momentum picks!")

    # DETAILED SEARCH RESULT SECTION
    if search_query:
        ticker_sym = f"{search_query}.NS"
        try:
            stock = yf.Ticker(ticker_sym)
            info = stock.info
            
            st.markdown(f'<div class="result-container">', unsafe_allow_html=True)
            res_col1, res_col2 = st.columns([2, 1])
            
            with res_col1:
                st.subheader(f"{info.get('longName', search_query)}")
                st.markdown(f"### ₹{info.get('currentPrice', 'N/A')} <span style='color:#00ffcc; font-size:18px;'>Live Quote</span>", unsafe_allow_html=True)
                
                # Tech Chart for Searched Stock
                hist = stock.history(period="1mo")
                fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
                fig.update_layout(template="plotly_dark", height=300, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)

            with res_col2:
                st.markdown("#### 💎 Fundamental Health")
                st.write(f"**Sector:** {info.get('sector', 'N/A')}")
                st.write(f"**PE Ratio:** {info.get('trailingPE', 'N/A')}")
                st.write(f"**Market Cap:** ₹{info.get('marketCap', 0)/10**11:.2f} L Cr")
                
                # AI Logic Score
                score = 7.5 # Placeholder for AI logic
                st.metric("AI Confidence Score", f"{score}/10", delta="Strong Buy")
            
            st.markdown('</div>', unsafe_allow_html=True)
        except:
            st.error("Stock not found. Please use valid NSE Ticker.")

    st.write("---")

    # 2. ALL INDEXES CARDS
    st.markdown("#### 📊 Current Market Indices")
    indices_data = get_market_indices()
    idx_cols = st.columns(len(indices_data))
    
    selected_index_sym = "NSE:NIFTY" # Default

    for i, (name, val) in enumerate(indices_data.items()):
        with idx_cols[i]:
            color = "#00ffcc" if val['change'] > 0 else "#ff4b4b"
            if st.button(f"{name}\n{val['price']:,.0f}", key=name):
                # Map Yahoo Symbol to TradingView Symbol
                tv_map = {"^NSEI": "NSE:NIFTY", "^NSEBANK": "NSE:BANKNIFTY", "^NSMIDCP": "NSE:NIFTY_MID_SELECT"}
                selected_index_sym = tv_map.get(val['sym'], "NSE:NIFTY")

            st.markdown(f"""
                <div style="text-align:center; color:{color}; font-size:12px; margin-top:-10px;">
                    {'▲' if val['change'] > 0 else '▼'} {abs(val['change']):.2f}%
                </div>
            """, unsafe_allow_html=True)

    # 3. TRADINGVIEW INTEGRATION (Updates based on click)
    st.components.v1.html(f"""
        <div style="height:500px; margin-top:20px;">
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({{
            "autosize": true, "symbol": "{selected_index_sym}", "interval": "D",
            "timezone": "Asia/Kolkata", "theme": "dark", "style": "1",
            "locale": "en", "enable_publishing": false, "hide_side_toolbar": false,
            "container_id": "tv_chart_{selected_index_sym}"
          }});
          </script>
          <div id="tv_chart_{selected_index_sym}" style="height:100%;"></div>
        </div>
    """, height=500)

    # 4. TOP 20 STOCKS
    st.markdown("#### 🏆 Top 20 Market Heavyweights")
    top_20 = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "BHARTIARTL.NS", "SBIN.NS", "INFY.NS", "LICI.NS", "ITC.NS", "HINDUNILVR.NS", "LT.NS", "BAJFINANCE.NS", "HCLTECH.NS", "MARUTI.NS", "SUNPHARMA.NS", "ADANIENT.NS", "KOTAKBANK.NS", "TITAN.NS", "ONGC.NS", "TATAMOTORS.NS"]
    df_top = yf.download(top_20, period="1d")['Close'].iloc[-1].reset_index()
    df_top.columns = ['Ticker', 'Price (INR)']
    st.dataframe(df_top.T, use_container_width=True) # Transposed for a sleek look

# --- PAGE 2: NEWS-BASED STOCKS ---
elif selected == "News-Based Stocks":
    st.subheader("📰 Sentiment-Driven Stock Analysis")
    # Content for news logic goes here
