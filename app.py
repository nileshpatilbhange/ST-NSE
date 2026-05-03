import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

# --- UI CONFIGURATION ---
st.set_page_config(page_title="QUANTUM NSE | AI Terminal", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS (GRAPHITE & ELECTRIC BLUE) ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0e11; color: #e1e1e1; font-family: 'Inter', sans-serif; }
    
    /* Branding Header */
    .brand-header { 
        text-align: left; 
        padding: 20px 0; 
        border-bottom: 1px solid #1e222d;
        margin-bottom: 25px;
    }
    .logo-main { font-size: 32px; font-weight: 800; color: #ffffff; letter-spacing: -1px; }
    .logo-accent { color: #2962ff; }
    .tagline { font-size: 13px; color: #787b86; text-transform: uppercase; letter-spacing: 1px; }
    
    /* Data Containers */
    .metric-card { 
        background: #131722; 
        border: 1px solid #1e222d; 
        padding: 20px; 
        border-radius: 4px; 
        text-align: center;
    }
    .metric-label { color: #787b86; font-size: 12px; font-weight: 600; text-transform: uppercase; }
    .metric-value { font-size: 24px; font-weight: 700; color: #ffffff; margin-top: 5px; }
    
    /* Navigation */
    .nav-container { background: #131722; border: 1px solid #1e222d; border-radius: 4px; margin-bottom: 20px; }
    
    /* List Items */
    .pick-item { background: #131722; border-left: 3px solid #2962ff; padding: 12px; margin-bottom: 8px; border-radius: 2px; }
    .sell-item { background: #131722; border-left: 3px solid #f23645; padding: 12px; margin-bottom: 8px; border-radius: 2px; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE ---
@st.cache_data(ttl=600)
def get_index_data():
    indices = {
        "NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "SENSEX": "^BSESN",
        "NIFTY IT": "^CNXIT", "NIFTY AUTO": "^CNXAUTO"
    }
    data = {}
    for name, sym in indices.items():
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="2d")
            price = hist['Close'].iloc[-1]
            change = ((price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
            data[name] = (price, change, sym)
        except: continue
    return data

# --- BRANDING ---
st.markdown("""
    <div class="brand-header">
        <div class="logo-main">QUANTUM<span class="logo-accent">NSE</span></div>
        <div class="tagline">Institutional Grade Analysis for the Retail Frontier.</div>
    </div>
    """, unsafe_allow_html=True)

# --- INDEX TICKER TAPE ---
idx_data = get_index_data()
if idx_data:
    cols = st.columns(len(idx_data))
    for i, (name, val) in enumerate(idx_data.items()):
        color = "#089981" if val[1] >= 0 else "#f23645"
        if cols[i].button(f"{name} : {val[0]:,.0f} ({val[1]:+.2f}%)"):
            st.session_state.selected_index = val[2]
            st.session_state.idx_display_name = name

# --- NAVIGATION ---
selected = option_menu(None, ["Analysis", "Top 10 Picks", "Market News"], 
    icons=["graph-up", "shield-check", "newspaper"], orientation="horizontal",
    styles={
        "container": {"background-color": "#131722", "border": "1px solid #1e222d", "border-radius": "4px"},
        "nav-link": {"color": "#787b86", "font-size": "14px", "font-weight": "600"},
        "nav-link-selected": {"background-color": "#2962ff", "color": "#ffffff"}
    })

# --- PAGE LOGIC (Based on your best result) ---
if selected == "Analysis":
    search = st.text_input("", placeholder="Ticker Symbol (e.g. RELIANCE)...").upper()
    if search:
        stock = yf.Ticker(f"{search}.NS")
        info, hist = stock.info, stock.history(period="3y")
        
        if not hist.empty:
            curr = hist['Close'].iloc[-1]
            pe = info.get('trailingPE', 0)
            roe = info.get('returnOnEquity', 0) * 100
            score = 0
            if pe < 25: score += 40
            if roe > 15: score += 60
            
            st.subheader(f"Equity Insight: {info.get('longName', search)}")
            c1, c2, c3 = st.columns(3)
            c1.markdown(f'<div class="metric-card"><div class="metric-label">Last Price</div><div class="metric-value">₹{curr:,.2f}</div></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="metric-card"><div class="metric-label">Proprietary Score</div><div class="metric-value">{score}/100</div></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="metric-card"><div class="metric-label">Valuation</div><div class="metric-value" style="color:#2962ff">{"Value" if pe < 20 else "Growth"}</div></div>', unsafe_allow_html=True)

            fig = go.Figure(data=[go.Scatter(x=hist.index, y=hist['Close'], line=dict(color='#2962ff', width=2))])
            fig.update_layout(template="plotly_dark", height=450, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,t=20,b=0))
            st.plotly_chart(fig, use_container_width=True)

elif selected == "Top 10 Picks":
    b, s = st.columns(2)
    with b:
        st.subheader("Strong Momentum")
        for sym in ["RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "L&T", "AXISBANK", "ITC", "KOTAKBANK", "SBIN"]:
            st.markdown(f'<div class="pick-item"><b>{sym}</b> - Structural Compounder</div>', unsafe_allow_html=True)
    with s:
        st.subheader("Risk Warning")
        for sym in ["IDEA", "PAYTM", "YESBANK", "RPOWER", "SUZLON", "ZOMATO", "NYKAA", "PEL", "IBULHSGFIN", "AWL"]:
            st.markdown(f'<div class="sell-item"><b>{sym}</b> - Volatility Alert</div>', unsafe_allow_html=True)

elif selected == "Market News":
    st.subheader("Business Standard Intelligence")
    news_stock = yf.Ticker("^NSEI")
    try:
        for n in news_stock.news[:8]:
            st.markdown(f"**{n.get('title')}**")
            st.caption(f"Source: {n.get('publisher')} | [Read Report]({n.get('link')})")
            st.divider()
    except: st.info("Feed syncing...")
