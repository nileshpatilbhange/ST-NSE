import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

# --- UI CONFIGURATION ---
st.set_page_config(page_title="QUANTUM NSE | AI Terminal", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #ffffff; }
    .brand-container { text-align: center; padding: 25px 0; background: #161b22; border-radius: 0 0 30px 30px; margin-bottom: 20px; border-bottom: 1px solid #30363d; }
    .logo-text { font-size: 42px; font-weight: 800; color: #00ffcc; margin: 0; }
    div[data-testid="stTable"] td, div[data-testid="stTable"] th {
        color: #ffffff !important; font-size: 14px !important; border-bottom: 1px solid #30363d !important;
    }
    .pick-card { background: #1c2128; border-left: 5px solid #00ffcc; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
    .sell-card { background: #1c2128; border-left: 5px solid #ff4b4b; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
    .metric-card { background: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINES ---
def get_index_data():
    # Expanded list of all major indices
    indices = {
        "NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "SENSEX": "^BSESN",
        "NIFTY IT": "^CNXIT", "NIFTY AUTO": "^CNXAUTO", "NIFTY PHARMA": "^CNXPHARMA"
    }
    data = {}
    for name, sym in indices.items():
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="2d")
            price = hist['Close'].iloc[-1]
            change = ((price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
            data[name] = (price, change, sym)
        except: data[name] = (0, 0, sym)
    return data

# --- BRANDING & TOP BAR ---
st.markdown('<div class="brand-container"><div class="logo-text">⚡ QUANTUM NSE</div></div>', unsafe_allow_html=True)

idx_data = get_index_data()
cols = st.columns(len(idx_data))
for i, (name, val) in enumerate(idx_data.items()):
    color = "#00ffcc" if val[1] >= 0 else "#ff4b4b"
    if cols[i].button(f"{name}\n{val[0]:,.0f} ({val[1]:.2f}%)"):
        st.session_state.selected_index = val[2]
        st.session_state.idx_display_name = name

# --- NAVIGATION ---
selected = option_menu(None, ["Analysis", "Top 10 Picks", "Market News"], 
    icons=["search", "trophy", "newspaper"], orientation="horizontal",
    styles={"nav-link-selected": {"background-color": "#00ffcc", "color": "#0d1117"}})

# --- 1. TECHNICAL CHART FOR INDICES (Triggered by clicking top bar) ---
if 'selected_index' in st.session_state:
    st.subheader(f"📈 {st.session_state.idx_display_name} Technical Chart")
    idx_hist = yf.Ticker(st.session_state.selected_index).history(period="1y")
    fig_idx = go.Figure(data=[go.Candlestick(x=idx_hist.index, open=idx_hist['Open'], high=idx_hist['High'], low=idx_hist['Low'], close=idx_hist['Close'])])
    fig_idx.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig_idx, use_container_width=True)
    if st.button("Close Index Chart"): 
        del st.session_state.selected_index
        st.rerun()

# --- 2. ANALYSIS PAGE (With Full "Other Data") ---
if selected == "Analysis":
    search = st.text_input("", placeholder="Search Stock Ticker (e.g., RELIANCE, TCS)...").upper()
    if search:
        t_sym = f"{search}.NS"
        stock = yf.Ticker(t_sym)
        info = stock.info
        
        # OTHER DATA: Institutional & Fundamental Grid
        st.subheader(f"💎 {info.get('longName', search)} - Core Fundamentals")
        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(f'<div class="metric-card"><small>Market Cap</small><br><span style="font-size:18px; color:#00ffcc">₹{info.get("marketCap", 0)/1e7:,.0f} Cr</span></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric-card"><small>Trailing P/E</small><br><span style="font-size:18px; color:#00ffcc">{info.get("trailingPE", "N/A")}</span></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric-card"><small>Debt to Equity</small><br><span style="font-size:18px; color:#ff4b4b">{info.get("debtToEquity", 0)/100:.2f}</span></div>', unsafe_allow_html=True)
        m4.markdown(f'<div class="metric-card"><small>ROE</small><br><span style="font-size:18px; color:#00ffcc">{info.get("returnOnEquity", 0)*100:.2f}%</span></div>', unsafe_allow_html=True)

        # Year-on-Year Financial Growth Table
        st.subheader("📊 Financial Audit (PnL & Balance Sheet)")
        try:
            fin = stock.financials.T
            growth_df = pd.DataFrame({
                "Year": fin.index.year,
                "Revenue (Cr)": (fin['Total Revenue'] / 1e7).round(2),
                "Net Profit (Cr)": (fin['Net Income'] / 1e7).round(2),
                "Operating Margin %": ((fin['Operating Income'] / fin['Total Revenue'])*100).round(2)
            }).reset_index(drop=True)
            st.table(growth_df)
        except: st.warning("Detailed financial data unavailable.")

        # Price Action
        st.subheader("📈 3-Year Technical Trend")
        hist = stock.history(period="3y")
        fig = go.Figure(data=[go.Scatter(x=hist.index, y=hist['Close'], line=dict(color='#00ffcc', width=2))])
        fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True)

# --- 3. TOP 10 PICKS (Buy & Sell) ---
elif selected == "Top 10 Picks":
    buy_col, sell_col = st.columns(2)
    
    with buy_col:
        st.subheader("🏆 Strong Buy Ratings")
        buys = [
            ("RELIANCE", "Green energy pivot and Retail expansion."),
            ("HDFCBANK", "Stabilizing NIMs and massive branch network."),
            ("L&T", "Record order book; Infra pipeline leader."),
            ("BHARTIARTL", "Consistently rising ARPU and 5G leadership."),
            ("TCS", "Deep AI integration and robust deal pipeline."),
            ("ICICIBANK", "Superior asset quality and strong digital focus."),
            ("BAJFINANCE", "Market leader in consumer lending (100M+ customers)."),
            ("M&M", "Dominant in SUV and EV segments."),
            ("HINDUNILVR", "Defensive play; high dividend and zero debt."),
            ("INFY", "High free cash flow and BFSI sector recovery.")
        ]
        for s, r in buys:
            st.markdown(f'<div class="pick-card"><b>{s}</b><br><small>{r}</small></div>', unsafe_allow_html=True)

    with sell_col:
        st.subheader("⚠️ Strong Sell / Avoid")
        sells = [
            ("IDEA", "Extreme debt stress and losing subscriber market share."),
            ("PAYTM", "Persistent regulatory hurdles and path to profitability concerns."),
            ("YESBANK", "Slow asset quality recovery and high cost-to-income ratio."),
            ("RPOWER", "Historical debt issues and inconsistent cash flows."),
            ("NYKAA", "Intense competition in beauty/fashion hitting margins."),
            ("PEL", "Stressed real estate exposure in the wholesale book."),
            ("SUZLON", "Technical overextension; high volatility for long term."),
            ("DELHIVERY", "Structural losses in highly competitive logistics sector."),
            ("AWL", "Weak growth in consumer essentials and high valuations."),
            ("DIXON", "Overstretched valuations relative to hardware margins.")
        ]
        for s, r in sells:
            st.markdown(f'<div class="sell-card"><b>{s}</b><br><small>{r}</small></div>', unsafe_allow_html=True)

# --- 4. NEWS PAGE ---
elif selected == "News":
    st.subheader("📰 Market-Sync News (Last 2 Weeks)")
    news_stock = yf.Ticker("^NSEI")
    for n in news_stock.news[:10]:
        with st.container():
            st.markdown(f"**{n['title']}**")
            st.caption(f"Source: {n['publisher']} | [Read Story]({n['link']})")
            st.divider()
