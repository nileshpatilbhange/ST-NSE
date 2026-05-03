import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import requests

# --- UI CONFIGURATION ---
st.set_page_config(page_title="QUANTUM NSE | AI Terminal", layout="wide", initial_sidebar_state="collapsed")

# --- CONNECTION HELPER (The Stability Fix) ---
def get_safe_ticker(symbol):
    """Creates a yfinance Ticker object with a custom browser session."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    return yf.Ticker(symbol, session=session)

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #ffffff; }
    .brand-container { text-align: center; padding: 25px 0; background: #161b22; border-radius: 0 0 30px 30px; border-bottom: 1px solid #30363d; margin-bottom: 20px; }
    .logo-text { font-size: 42px; font-weight: 800; color: #00ffcc; margin: 0; }
    div[data-testid="stTable"] td, div[data-testid="stTable"] th { color: #ffffff !important; font-size: 16px !important; border-bottom: 1px solid #30363d !important; }
    .stat-box { background: #1c2128; border: 1px solid #30363d; border-radius: 12px; padding: 15px; margin-bottom: 10px; }
    .metric-label { font-size: 12px; color: #8b949e; text-transform: uppercase; }
    .metric-value { font-size: 22px; font-weight: bold; margin-top: 5px; }
    .pick-card { background: #1c2128; border-left: 5px solid #00ffcc; padding: 12px; margin-bottom: 10px; border-radius: 5px; }
    .sell-card { background: #1c2128; border-left: 5px solid #ff4b4b; padding: 12px; margin-bottom: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- BRANDING ---
st.markdown('<div class="brand-container"><div class="logo-text">⚡ QUANTUM NSE PRO</div></div>', unsafe_allow_html=True)

# --- INDICES DASHBOARD ---
major_indices = {
    "NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "FIN NIFTY": "NIFTY_FIN_SERVICE.NS",
    "NIFTY IT": "^CNXIT", "NIFTY AUTO": "^CNXAUTO", "NIFTY PHARMA": "^CNXPHARMA"
}

@st.cache_data(ttl=60)
def fetch_all_indices(idx_dict):
    data = {}
    for name, sym in idx_dict.items():
        try:
            t = get_safe_ticker(sym)
            h = t.history(period="2d")
            if not h.empty:
                price = h['Close'].iloc[-1]
                change = ((h['Close'].iloc[-1] - h['Close'].iloc[-2]) / h['Close'].iloc[-2]) * 100
                data[name] = {"price": price, "change": change, "sym": sym}
        except: continue
    return data

idx_results = fetch_all_indices(major_indices)

if idx_results:
    cols = st.columns(len(idx_results))
    for i, (name, d) in enumerate(idx_results.items()):
        col_color = "#00ffcc" if d['change'] >= 0 else "#ff4b4b"
        with cols[i]:
            st.markdown(f"<p style='color:{col_color}; margin-bottom:-10px; font-weight:bold; font-size:12px;'>{d['change']:+.2f}%</p>", unsafe_allow_html=True)
            if st.button(f"{name}\n{d['price']:,.1f}", key=name):
                st.session_state.active_index = d['sym']
                st.session_state.active_name = name
else:
    st.error("⚠️ Connection unstable. Yahoo Finance is currently throttling requests.")
    if st.button("Retry Connection"):
        st.rerun()

# Index Chart Logic
if "active_index" in st.session_state:
    st.subheader(f"📈 {st.session_state.active_name} Technical Chart")
    try:
        idx_hist = get_safe_ticker(st.session_state.active_index).history(period="1y")
        fig = go.Figure(data=[go.Candlestick(x=idx_hist.index, open=idx_hist['Open'], high=idx_hist['High'], low=idx_hist['Low'], close=idx_hist['Close'])])
        fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
    except: st.warning("Chart data temporarily unavailable.")

# --- NAVIGATION ---
menu = option_menu(None, ["Stock Search", "Top 10 Picks/Sells"], icons=["search", "list-check"], orientation="horizontal",
                   styles={"nav-link-selected": {"background-color": "#00ffcc", "color": "#0d1117"}})

if menu == "Stock Search":
    search = st.text_input("", placeholder="Enter Ticker (e.g., RELIANCE)...").upper()
    if search:
        t_sym = f"{search}.NS"
        try:
            stock = get_safe_ticker(t_sym)
            info = stock.info
            
            # CORE STATS
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f'<div class="stat-box"><p class="metric-label">Price</p><p class="metric-value">₹{info.get("currentPrice", 0):,.2f}</p></div>', unsafe_allow_html=True)
            with c2:
                pe = info.get('trailingPE', 0)
                st.markdown(f'<div class="stat-box"><p class="metric-label">P/E Ratio</p><p class="metric-value" style="color:{"#00ffcc" if pe < 30 else "#ff4b4b"}">{pe:.2f}</p></div>', unsafe_allow_html=True)
            with c3:
                roe = info.get('returnOnEquity', 0) * 100
                st.markdown(f'<div class="stat-box"><p class="metric-label">ROE</p><p class="metric-value" style="color:{"#00ffcc" if roe>15 else "#ff4b4b"}">{roe:.1f}%</p></div>', unsafe_allow_html=True)
            with c4:
                st.markdown(f'<div class="stat-box"><p class="metric-label">Health</p><p class="metric-value" style="color:#00ffcc">ANALYZED</p></div>', unsafe_allow_html=True)

            # FINANCIAL TABLE
            st.subheader("📊 Financial Growth Audit (YoY)")
            fin = stock.financials.T
            if not fin.empty:
                growth_df = pd.DataFrame({
                    "Year": fin.index.year,
                    "Net Profit (Cr)": (fin['Net Income'] / 1e7).round(2),
                    "Revenue (Cr)": (fin['Total Revenue'] / 1e7).round(2)
                }).reset_index(drop=True)
                st.table(growth_df)

            # 3-YEAR CHART
            st.subheader("📈 3-Year Price Action")
            h3y = stock.history(period="3y")
            fig3 = go.Figure(data=[go.Scatter(x=h3y.index, y=h3y['Close'], line=dict(color='#00ffcc'))])
            fig3.update_layout(template="plotly_dark", height=400)
            st.plotly_chart(fig3, use_container_width=True)
        except:
            st.error(f"Could not retrieve data for {search}. Verify the ticker symbol.")

elif menu == "Top 10 Picks/Sells":
    b, s = st.columns(2)
    with b:
        st.subheader("🟢 Top 10 Strong Buy")
        buys = [("RELIANCE", "Energy pivot"), ("HDFCBANK", "Value bottom"), ("LT", "Infra peak"), ("TCS", "AI expansion"), ("BHARTIARTL", "ARPU growth"), ("ICICIBANK", "Best ROA"), ("M&M", "EV leader"), ("BAJFINANCE", "Digital scale"), ("HINDUNILVR", "Recovery"), ("TITAN", "Luxury demand")]
        for ticker, reason in buys:
            st.markdown(f'<div class="pick-card"><b>{ticker}</b>: {reason}</div>', unsafe_allow_html=True)
    with s:
        st.subheader("🔴 Top 10 Strong Sell")
        sells = [("PAYTM", "Regulatory"), ("WIPRO", "Revenue lag"), ("VEDL", "Debt load"), ("ZEEL", "Uncertainty"), ("UPL", "Chemical lag"), ("PAGEIND", "Valuation"), ("NYKAA", "Margins"), ("DELHIVERY", "Unit costs"), ("ADANIENT", "Stretched P/E"), ("NMDC", "Iron volatility")]
        for ticker, reason in sells:
            st.markdown(f'<div class="sell-card"><b>{ticker}</b>: {reason}</div>', unsafe_allow_html=True)
