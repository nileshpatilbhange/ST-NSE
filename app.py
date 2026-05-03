import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

# --- UI CONFIGURATION ---
st.set_page_config(page_title="QUANTUM NSE | AI Terminal", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS (NEW MIDNIGHT & GOLD THEME) ---
st.markdown("""
    <style>
    .stApp { background-color: #05070a; color: #e0e0e0; }
    .brand-container { 
        text-align: center; 
        padding: 40px 0; 
        background: linear-gradient(180deg, #111418 0%, #05070a 100%); 
        border-bottom: 1px solid #c8a45e33;
        margin-bottom: 30px;
    }
    .logo-text { font-size: 52px; font-weight: 900; color: #c8a45e; letter-spacing: -1px; margin: 0; }
    .branding-tagline { font-size: 16px; color: #888; font-style: italic; margin-top: 5px; }
    
    /* Metric Cards */
    .metric-card { 
        background: #111418; 
        border: 1px solid #30363d; 
        padding: 20px; 
        border-radius: 16px; 
        text-align: center;
        transition: transform 0.3s ease;
    }
    .metric-card:hover { transform: translateY(-5px); border-color: #c8a45e; }
    
    div[data-testid="stTable"] td, div[data-testid="stTable"] th {
        color: #e0e0e0 !important; border-bottom: 1px solid #30363d !important;
        background-color: #111418 !important;
    }
    .status-box { padding: 12px; border-radius: 10px; font-weight: 800; text-align: center; margin-bottom: 15px; }
    .pick-card { background: #111418; border-left: 4px solid #c8a45e; padding: 15px; margin-bottom: 12px; border-radius: 8px; }
    .sell-card { background: #111418; border-left: 4px solid #ff4b4b; padding: 15px; margin-bottom: 12px; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- BRANDING SECTION ---
st.markdown("""
    <div class="brand-container">
        <div class="logo-text">QUANTUM NSE</div>
        <div class="branding-tagline">"Precision Intelligence for the Modern Indian Investor."</div>
    </div>
    """, unsafe_allow_html=True)

# --- DATA ENGINES ---
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
            if len(hist) >= 2:
                price = hist['Close'].iloc[-1]
                change = ((price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
                data[name] = (price, change, sym)
        except: continue
    return data

idx_data = get_index_data()
if idx_data:
    cols = st.columns(len(idx_data))
    for i, (name, val) in enumerate(idx_data.items()):
        color = "#c8a45e" if val[1] >= 0 else "#ff4b4b"
        if cols[i].button(f"{name}\n{val[0]:,.0f} ({val[1]:.2f}%)"):
            st.session_state.selected_index = val[2]
            st.session_state.idx_display_name = name

# --- NAVIGATION ---
selected = option_menu(None, ["Analysis", "Top 10 Picks", "Market News"], 
    icons=["graph-up-arrow", "shield-check", "broadcast"], orientation="horizontal",
    styles={
        "container": {"background-color": "#111418", "border-radius": "0px"},
        "nav-link": {"color": "#888", "font-size": "14px"},
        "nav-link-selected": {"background-color": "#c8a45e", "color": "#05070a", "font-weight": "700"}
    })

# --- ANALYSIS PAGE ---
if selected == "Analysis":
    search = st.text_input("", placeholder="Enter Ticker Symbol (e.g. TATASTEEL)...").upper()
    if search:
        t_sym = f"{search}.NS"
        stock = yf.Ticker(t_sym)
        info = stock.info
        hist = stock.history(period="3y")
        
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            pe = info.get('trailingPE', 0)
            peg = info.get('pegRatio', 0)
            debt_to_equity = info.get('debtToEquity', 0)
            roe = info.get('returnOnEquity', 0) * 100
            pledged = info.get('pledgedPercent', 0) or 0
            
            score = 0
            if pe < 25: score += 25
            if roe > 15: score += 25
            if (debt_to_equity/100) < 1.5: score += 25
            if 0.8 <= peg <= 1.5: score += 25
            
            st.subheader(f"💎 {info.get('longName', search)}")
            c1, c2, c3 = st.columns(3)
            c1.markdown(f'<div class="metric-card"><small>PRICE</small><br><span style="font-size:28px; color:#c8a45e">₹{current_price:,.2f}</span></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="metric-card"><small>HEALTH SCORE</small><br><span style="font-size:28px; color:#c8a45e">{score}/100</span></div>', unsafe_allow_html=True)
            v_text = "PREMIUM" if pe > 30 else "VALUE"
            c3.markdown(f'<div class="metric-card"><small>TIER</small><br><span style="font-size:28px; color:#c8a45e">{v_text}</span></div>', unsafe_allow_html=True)

            st.subheader("📊 Fundamental Audit")
            r1, r2, r3, r4 = st.columns(4)
            r1.markdown(f'<div class="metric-card"><small>D/E Ratio</small><br><b style="color:#c8a45e">{(debt_to_equity/100):.2f}</b></div>', unsafe_allow_html=True)
            r2.markdown(f'<div class="metric-card"><small>ROE %</small><br><b style="color:#c8a45e">{roe:.1f}%</b></div>', unsafe_allow_html=True)
            r3.markdown(f'<div class="metric-card"><small>P/E</small><br><b style="color:#c8a45e">{pe:.1f}</b></div>', unsafe_allow_html=True)
            r4.markdown(f'<div class="metric-card"><small>Pledged</small><br><b style="color:#ff4b4b">{pledged:.1f}%</b></div>', unsafe_allow_html=True)

            fig = go.Figure(data=[go.Scatter(x=hist.index, y=hist['Close'], line=dict(color='#c8a45e', width=2))])
            fig.update_layout(template="plotly_dark", height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,t=20,b=0))
            st.plotly_chart(fig, use_container_width=True)

elif selected == "Top 10 Picks":
    b, s = st.columns(2)
    with b:
        st.subheader("🏆 Growth Leaders")
        for sym in ["RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "L&T", "AXISBANK", "ITC", "KOTAKBANK", "SBIN"]:
            st.markdown(f'<div class="pick-card"><b>{sym}</b> - Structural Compounder</div>', unsafe_allow_html=True)
    with s:
        st.subheader("⚠️ High Risk Watch")
        for sym in ["IDEA", "PAYTM", "YESBANK", "RPOWER", "SUZLON", "ADANIPOWER", "ZOMATO", "NYKAA", "PEL", "IBULHSGFIN"]:
            st.markdown(f'<div class="sell-card"><b>{sym}</b> - Volatility Alert</div>', unsafe_allow_html=True)

elif selected == "Market News":
    st.subheader("📰 Business Standard Intelligence")
    news_stock = yf.Ticker("^NSEI")
    try:
        for n in news_stock.news[:8]:
            title = n.get('title', 'N/A')
            pub = n.get('publisher', 'Market Desk')
            link = n.get('link', '#')
            st.markdown(f"**{title}**")
            st.caption(f"Ref: {pub} | [Access Full Report]({link})")
            st.divider()
    except: st.info("Intelligence feed currently synchronizing...")
