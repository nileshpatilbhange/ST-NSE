import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from GoogleNews import GoogleNews
from streamlit_option_menu import option_menu

# --- THEME & TERMINAL STYLING ---
st.set_page_config(page_title="PRO-TERMINAL | NSE", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .stApp { background-color: #05070a; color: #e1e1e1; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    .market-card {
        background: #111418; border: 1px solid #1f2228; border-radius: 8px;
        padding: 15px; text-align: center; transition: 0.3s;
    }
    .market-card:hover { border-color: #00ffcc; background: #161a1f; }
    .price-up { color: #00ffcc; font-family: 'Courier New', monospace; font-weight: bold; }
    .price-down { color: #ff3333; font-family: 'Courier New', monospace; font-weight: bold; }
    div.stButton > button {
        background: #00ffcc; color: #000; border: none; border-radius: 4px; font-weight: bold; width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- APP NAVIGATION ---
selected = option_menu(
    menu_title=None,
    options=["Market Home", "Stock Terminal", "Stocks In-News"],
    icons=["house", "graph-up-arrow", "newspaper"],
    orientation="horizontal",
    styles={
        "container": {"padding": "0", "background-color": "#111418", "border-radius": "0"},
        "icon": {"color": "#00ffcc", "font-size": "18px"}, 
        "nav-link": {"font-size": "16px", "text-align": "center", "margin":"0px", "color": "#fff"},
        "nav-link-selected": {"background-color": "#1f2228", "border-bottom": "3px solid #00ffcc"},
    }
)

# --- LOGIC: MARKET DATA ---
@st.cache_data(ttl=300)
def get_indices():
    indices = {
        "Nifty 50": "^NSEI",
        "Nifty Next 50": "^NSMIDCP",
        "Bank Nifty": "^NSEBANK",
        "Nifty IT": "^CNXIT"
    }
    data = []
    for name, t in indices.items():
        ticker = yf.Ticker(t)
        h = ticker.history(period="2d")
        if not h.empty:
            curr, prev = h['Close'].iloc[-1], h['Close'].iloc[-2]
            change = ((curr - prev) / prev) * 100
            data.append({"name": name, "price": curr, "change": change, "symbol": t})
    return data

# --- PAGE 1: MARKET HOME ---
if selected == "Market Home":
    st.subheader("🌐 Global & Domestic Benchmarks")
    m_cols = st.columns(4)
    market_data = get_indices()
    
    for i, item in enumerate(market_data):
        with m_cols[i]:
            color_class = "price-up" if item['change'] > 0 else "price-down"
            st.markdown(f"""
                <div class="market-card">
                    <small style="color: #8b949e;">{item['name']}</small>
                    <h3 style="margin: 5px 0;">₹{item['price']:,.2f}</h3>
                    <span class="{color_class}">{'▲' if item['change'] > 0 else '▼'} {abs(item['change']):.2f}%</span>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    
    # TRADINGVIEW INTEGRATION (WIDGET)
    st.subheader("📈 Technical Overview (Nifty 50)")
    st.components.v1.html("""
        <div class="tradingview-widget-container" style="height:500px;">
          <div id="tradingview_chart"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({
            "autosize": true, "symbol": "NSE:NIFTY", "interval": "D", "timezone": "Asia/Kolkata",
            "theme": "dark", "style": "1", "locale": "en", "toolbar_bg": "#f1f3f6",
            "enable_publishing": false, "hide_side_toolbar": false, "allow_symbol_change": true,
            "container_id": "tradingview_chart"
          });
          </script>
        </div>
    """, height=500)

    # TOP 20 TABLE
    st.markdown("### 🏆 Top 20 NSE High-Volume Stocks")
    top_20_list = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "BHARTIARTL.NS", "SBIN.NS", "INFY.NS", "LICI.NS", "ITC.NS", "HINDUNILVR.NS", "LT.NS", "BAJFINANCE.NS", "HCLTECH.NS", "MARUTI.NS", "SUNPHARMA.NS", "ADANIENT.NS", "KOTAKBANK.NS", "TITAN.NS", "ONGC.NS", "TATAMOTORS.NS"]
    
    @st.cache_data(ttl=600)
    def fetch_top_20():
        df = yf.download(top_20_list, period="1d")['Close'].iloc[-1]
        return pd.DataFrame({"Ticker": [t.replace(".NS","") for t in top_20_list], "Price": df.values}).sort_values(by="Price", ascending=False)
    
    st.dataframe(fetch_top_20(), use_container_width=True)

# --- PAGE 2: STOCK TERMINAL ---
elif selected == "Stock Terminal":
    col_s, col_l = st.columns([4, 1])
    with col_s:
        search_ticker = st.text_input("ENTER TICKER (e.g., RELIANCE, INFOSYS)", "RELIANCE").upper()
    with col_l:
        st.write("") # Spacer
        if st.button("OPEN TERMINAL"):
            pass # Button triggers refresh

    ticker_ns = f"{search_ticker}.NS" if not search_ticker.endswith(".NS") else search_ticker
    
    try:
        s = yf.Ticker(ticker_ns)
        info = s.info
        
        # TERMINAL UI
        t_col1, t_col2 = st.columns([2, 1])
        
        with t_col1:
            st.markdown(f"## {info.get('longName', ticker_ns)}")
            st.markdown(f"<h1 style='margin:0;'>₹{info.get('currentPrice', 'N/A')}</h1>", unsafe_allow_html=True)
            
            # Interactive Chart
            hist = s.history(period="1y")
            fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
            fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig, use_container_width=True)

        with t_col2:
            st.markdown("### 🕵️ Expert Audit")
            de = info.get('debtToEquity', 0) / 100
            roe = info.get('returnOnEquity', 0) * 100
            score = 0
            if de < 1.5: score += 4
            if roe > 15: score += 4
            if info.get('pegRatio', 1) < 1.2: score += 2
            
            st.markdown(f"""
                <div class="market-card" style="border-left: 5px solid #00ffcc;">
                    <p>Financial Health Score</p>
                    <h2 style="color:#00ffcc;">{score}/10</h2>
                    <p style="font-size: 14px;">Rec: <b>{'BUY' if score > 7 else 'HOLD' if score > 5 else 'AVOID'}</b></p>
                </div>
            """, unsafe_allow_html=True)
            
            st.write("**Key Ratios**")
            st.json({
                "Debt/Equity": f"{de:.2f}",
                "ROE": f"{roe:.2f}%",
                "Sector": info.get('sector'),
                "P/E": info.get('trailingPE')
            })

    except Exception as e:
        st.error(f"Ticker {search_ticker} not found on NSE.")

# --- PAGE 3: STOCKS IN-NEWS ---
elif selected == "Stocks In-News":
    st.subheader("🗞️ High-Impact Market News")
    gn = GoogleNews(period='7d', lang='en', region='IN')
    gn.search('NSE India Stock News')
    news = gn.result()
    
    for n in news[:10]:
        title = n.get('title', 'News Update')
        if title:
            with st.container():
                st.markdown(f"""
                <div class="market-card" style="text-align: left; margin-bottom: 10px;">
                    <small style="color:#8b949e;">{n.get('media')} • {n.get('date')}</small>
                    <h5 style="margin: 5px 0;"><a href="{n.get('link')}" target="_blank" style="color:#00ffcc; text-decoration:none;">{title}</a></h5>
                </div>
                """, unsafe_allow_html=True)
