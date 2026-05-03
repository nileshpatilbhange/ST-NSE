import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

# --- UI CONFIGURATION ---
st.set_page_config(page_title="QUANTUM NSE | AI Terminal", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS (PROFESSIONAL GRAPHITE) ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0e11; color: #e1e1e1; }
    .brand-header { 
        text-align: center; 
        padding: 20px 0; 
        border-bottom: 1px solid #1e222d;
        margin-bottom: 20px;
    }
    .logo-main { font-size: 36px; font-weight: 800; color: #ffffff; letter-spacing: -1px; }
    .logo-accent { color: #2962ff; }
    .tagline { font-size: 13px; color: #787b86; text-transform: uppercase; letter-spacing: 2px; margin-top: 5px;}
    
    /* Metric Cards */
    .metric-card { 
        background: #131722; border: 1px solid #1e222d; 
        padding: 15px; border-radius: 4px; text-align: center; 
    }
    .metric-label { color: #787b86; font-size: 11px; font-weight: 600; text-transform: uppercase; }
    .metric-value { font-size: 20px; font-weight: 700; color: #ffffff; }

    /* Tables */
    div[data-testid="stTable"] td, div[data-testid="stTable"] th {
        color: #e1e1e1 !important; background-color: #131722 !important;
        border-bottom: 1px solid #1e222d !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINES ---
@st.cache_data(ttl=600)
def get_index_data():
    indices = {
        "NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "SENSEX": "^BSESN",
        "NIFTY IT": "^CNXIT", "NIFTY AUTO": "^CNXAUTO", "NIFTY PHARMA": "^CNXPHARMA"
    }
    data = {}
    for name, sym in indices.items():
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="2d")
            if len(hist) >= 2:
                price = hist['Close'].iloc[-1]
                change = ((price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
                data[name] = (price, change, sym)
        except: continue
    return data

# --- BRANDING ---
st.markdown("""
    <div class="brand-header">
        <div class="logo-main">QUANTUM<span class="logo-accent">NSE</span></div>
        <div class="tagline">Institutional Grade Market Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

# --- INDICES SECTION (REINSTATED) ---
idx_data = get_index_data()
if idx_data:
    cols = st.columns(len(idx_data))
    for i, (name, val) in enumerate(idx_data.items()):
        # Styling buttons based on performance
        btn_label = f"{name}\n{val[0]:,.0f} ({val[1]:+.2f}%)"
        if cols[i].button(btn_label, key=name):
            st.session_state.selected_index = val[2]
            st.session_state.idx_display_name = name

# --- INDEX CHART DISPLAY (REINSTATED) ---
if 'selected_index' in st.session_state:
    st.markdown(f"### 📊 {st.session_state.idx_display_name} Technical View")
    idx_hist = yf.Ticker(st.session_state.selected_index).history(period="1y")
    fig_idx = go.Figure(data=[go.Candlestick(
        x=idx_hist.index, open=idx_hist['Open'], high=idx_hist['High'], 
        low=idx_hist['Low'], close=idx_hist['Close'],
        increasing_line_color='#089981', decreasing_line_color='#f23645'
    )])
    fig_idx.update_layout(template="plotly_dark", height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_idx, use_container_width=True)
    if st.button("Close Index Chart"): 
        del st.session_state.selected_index
        st.rerun()

# --- NAVIGATION ---
selected = option_menu(None, ["Analysis", "Top 10 Picks", "Market News"], 
    icons=["search", "trophy", "newspaper"], orientation="horizontal",
    styles={
        "container": {"background-color": "#131722", "border": "1px solid #1e222d", "border-radius": "4px"},
        "nav-link-selected": {"background-color": "#2962ff", "color": "#ffffff"}
    })

# --- ANALYSIS PAGE ---
if selected == "Analysis":
    search = st.text_input("", placeholder="Enter Ticker (e.g. RELIANCE)...").upper()
    if search:
        t_sym = f"{search}.NS"
        stock = yf.Ticker(t_sym)
        info, hist = stock.info, stock.history(period="3y")
        
        if not hist.empty:
            curr = hist['Close'].iloc[-1]
            pe = info.get('trailingPE', 0)
            roe = info.get('returnOnEquity', 0) * 100
            debt = info.get('debtToEquity', 0) / 100
            
            score = 0
            if pe < 25: score += 25
            if roe > 15: score += 25
            if debt < 1: score += 25
            if curr > hist['Close'].rolling(200).mean().iloc[-1]: score += 25
            
            st.subheader(f"Equity Report: {info.get('longName', search)}")
            c1, c2, c3 = st.columns(3)
            c1.markdown(f'<div class="metric-card"><div class="metric-label">LTP</div><div class="metric-value">₹{curr:,.2f}</div></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="metric-card"><div class="metric-label">Quantum Score</div><div class="metric-value">{score}/100</div></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="metric-card"><div class="metric-label">Verdict</div><div class="metric-value" style="color:#2962ff">{"BUY" if score >= 75 else "WATCH"}</div></div>', unsafe_allow_html=True)

            # Growth Table
            try:
                fin = stock.financials.T
                fin_df = pd.DataFrame({
                    "Year": fin.index.year,
                    "Net Profit (Cr)": (fin['Net Income'] / 1e7).round(2),
                    "Growth %": fin['Net Income'].pct_change().fillna(0).apply(lambda x: f"{x*100:+.2f}%")
                }).reset_index(drop=True)
                st.table(fin_df)
            except: st.caption("Financial table unavailable for this ticker.")

            fig = go.Figure(data=[go.Scatter(x=hist.index, y=hist['Close'], line=dict(color='#2962ff'))])
            fig.update_layout(template="plotly_dark", height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

# --- TOP 10 PICKS ---
elif selected == "Top 10 Picks":
    b, s = st.columns(2)
    with b:
        st.subheader("Core Compounders")
        for sym in ["RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "L&T", "AXISBANK", "ITC", "KOTAKBANK", "SBIN"]:
            st.markdown(f'<div style="background:#131722; border-left:3px solid #089981; padding:10px; margin-bottom:5px;"><b>{sym}</b></div>', unsafe_allow_html=True)
    with s:
        st.subheader("High Volatility")
        for sym in ["IDEA", "PAYTM", "YESBANK", "RPOWER", "SUZLON", "ZOMATO", "NYKAA", "PEL", "AWL", "DELHIVERY"]:
            st.markdown(f'<div style="background:#131722; border-left:3px solid #f23645; padding:10px; margin-bottom:5px;"><b>{sym}</b></div>', unsafe_allow_html=True)

# --- MARKET NEWS ---
elif selected == "Market News":
    st.subheader("Business Standard Intelligence")
    news_stock = yf.Ticker("^NSEI")
    try:
        news_data = news_stock.news
        for n in news_data[:10]:
            title = n.get('title')
            pub = n.get('publisher')
            link = n.get('link')
            icon = "⭐" if "Business Standard" in pub else "•"
            st.markdown(f"{icon} **{title}**")
            st.caption(f"{pub} | [Source Link]({link})")
            st.divider()
    except: st.info("Intelligence stream currently offline.")
