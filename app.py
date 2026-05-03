import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

# --- UI CONFIGURATION ---
st.set_page_config(page_title="QUANTUM NSE | AI Terminal", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #05070a; color: #ffffff; }
    .brand-container { text-align: center; padding: 30px 0; background: #0d1117; border-radius: 0 0 30px 30px; margin-bottom: 20px; border-bottom: 1px solid #c8a45e44; }
    .logo-text { font-size: 42px; font-weight: 800; color: #c8a45e; margin: 0; }
    .branding-tagline { font-size: 16px; color: #888; font-style: italic; margin-top: 5px; }
    div[data-testid="stTable"] td, div[data-testid="stTable"] th { color: #ffffff !important; font-size: 14px !important; border-bottom: 1px solid #30363d !important; background-color: #0d1117 !important; }
    .metric-card { background: #0d1117; border: 1px solid #c8a45e33; padding: 15px; border-radius: 12px; text-align: center; }
    .status-box { padding: 15px; border-radius: 8px; font-weight: bold; text-align: center; font-size: 18px; margin-top: 10px; border: 1px solid #ffffff22; }
    .pick-card { background: #0d1117; border-left: 5px solid #c8a45e; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
    .sell-card { background: #0d1117; border-left: 5px solid #ff4b4b; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- TECHNICAL ANALYSIS ENGINE ---
def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

@st.cache_data(ttl=600)
def get_index_data():
    indices = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "SENSEX": "^BSESN", "NIFTY IT": "^CNXIT"}
    data = {}
    for name, sym in indices.items():
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="5d")
            price = hist['Close'].iloc[-1]
            change = ((price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
            data[name] = (price, change, sym)
        except: continue
    return data

# --- BRANDING ---
st.markdown('<div class="brand-container"><div class="logo-text">⚡ QUANTUM NSE</div><div class="branding-tagline">"Precision Intelligence for the Modern Indian Investor."</div></div>', unsafe_allow_html=True)

# --- NAVIGATION ---
selected = option_menu(None, ["Analysis", "Top 10 Picks", "AI Capital Planner", "Market News"], 
    icons=["search", "trophy", "calculator", "newspaper"], orientation="horizontal",
    styles={"container": {"background-color": "#0d1117", "border": "1px solid #c8a45e22"}, "nav-link-selected": {"background-color": "#c8a45e", "color": "#05070a"}})

# --- ANALYSIS PAGE ---
if selected == "Analysis":
    search = st.text_input("", placeholder="Search Stock Ticker (e.g., RELIANCE)...").upper()
    if search:
        t_sym = f"{search}.NS"
        stock = yf.Ticker(t_sym)
        info = stock.info
        hist = stock.history(period="5y") # Fetch 5Y for average PE and 200 DMA
        
        if not hist.empty:
            # 1. DATA INPUT
            curr_price = hist['Close'].iloc[-1]
            roe = info.get('returnOnEquity', 0) * 100
            debt_equity = info.get('debtToEquity', 0) / 100
            curr_pe = info.get('trailingPE', 0)
            peg = info.get('pegRatio', 0)
            avg_pe_5y = hist['Close'].mean() / (info.get('trailingEps', 1) or 1) # Approximation of 5Y PE logic
            
            dma200 = hist['Close'].rolling(window=200).mean().iloc[-1]
            rsi_series = calculate_rsi(hist['Close'])
            curr_rsi = rsi_series.iloc[-1]

            # 2. SCORING LOGIC
            score = 0
            # Financial Health (+3)
            if roe > 15: score += 2
            if debt_equity < 1: score += 1
            elif debt_equity > 2: score -= 2
            
            # Valuation (+3)
            if peg < 1 and peg > 0: score += 2
            if curr_pe < avg_pe_5y: score += 1
            
            # Momentum (+2)
            if curr_price > dma200: score += 1
            if 30 < curr_rsi < 60: score += 1
            elif curr_rsi > 75: score -= 2

            # 3. DECISION ENGINE
            if score >= 6:
                verdict, v_color, v_msg = "BUY", "#c8a45e", "High Quality + Fair Valuation + Stable Momentum"
            elif 3 <= score <= 5:
                verdict, v_color, v_msg = "WAIT / HOLD", "#ffcc00", "Good business but expensive or declining fundamentals"
            else:
                verdict, v_color, v_msg = "SELL / AVOID", "#ff4b4b", "High debt, overvalued, or failing profitability"

            # DISPLAY
            st.subheader(f"💎 Analysis: {info.get('longName', search)}")
            c1, c2, c3 = st.columns(3)
            c1.markdown(f'<div class="metric-card"><small>Price</small><br><span style="font-size:24px; color:#c8a45e">₹{curr_price:,.2f}</span></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="metric-card"><small>AI Score</small><br><span style="font-size:24px; color:#c8a45e">{score}/8</span></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="metric-card"><small>RSI (14D)</small><br><span style="font-size:24px; color:#c8a45e">{curr_rsi:.1f}</span></div>', unsafe_allow_html=True)
            
            st.markdown(f'<div class="status-box" style="color:{v_color}; border-color:{v_color}44">VERDICT: {verdict}<br><small style="color:#888">{v_msg}</small></div>', unsafe_allow_html=True)

            st.subheader("🔍 Logic Audit")
            a1, a2, a3 = st.columns(3)
            a1.write(f"**ROE:** {roe:.1f}%")
            a1.write(f"**Debt/Equity:** {debt_equity:.2f}")
            a2.write(f"**PEG Ratio:** {peg:.2f}")
            a2.write(f"**P/E vs 5Y Avg:** {curr_pe:.1f} / {avg_pe_5y:.1f}")
            a3.write(f"**Price > 200DMA:** {'✅' if curr_price > dma200 else '❌'}")
            a3.write(f"**RSI Status:** {'Neutral' if 30<curr_rsi<60 else 'Extreme'}")

# --- AI CAPITAL PLANNER (PRESERVED) ---
elif selected == "AI Capital Planner":
    st.subheader("🤖 AI Capital Allocation Engine")
    col_input, col_output = st.columns([1, 1.5])
    with col_input:
        total_cap = st.number_input("Total Capital (₹)", min_value=10000, value=100000)
        risk = st.select_slider("Risk Appetite", options=["Conservative", "Moderate", "Aggressive"])
        config = {"Conservative": {"sip": 0.8, "lump": 0.2, "return": 0.11}, "Moderate": {"sip": 0.6, "lump": 0.4, "return": 0.14}, "Aggressive": {"sip": 0.4, "lump": 0.6, "return": 0.18}}
        sip_total, lump_total = total_cap * config[risk]["sip"], total_cap * config[risk]["lump"]
    with col_output:
        st.info(f"**Allocation Strategy:** {config[risk]['sip']*100}% SIP | {config[risk]['lump']*100}% Lumpsum")
        if risk == "Aggressive":
            indices = ["Nifty Smallcap 250 (30%)", "Nifty Midcap 150 (25%)", "Nifty IT (20%)"]
            stocks = ["Zomato", "Suzlon", "Trent"]
        elif risk == "Moderate":
            indices = ["Nifty 50 (40%)", "Nifty Next 50 (20%)", "Nifty Midcap (20%)"]
            stocks = ["Reliance", "ICICI Bank", "L&T"]
        else:
            indices = ["Nifty 50 (50%)", "Gold ETF (20%)", "Liquid Fund (10%)"]
            stocks = ["TCS", "HDFC Bank", "ITC"]
        st.markdown(f"**Recommended Indices:**\n" + "\n".join([f"- {i}" for i in indices]))
        st.success(f"**Stock Picks:** {', '.join(stocks)}")

# --- TOP 10 & NEWS (PRESERVED) ---
elif selected == "Top 10 Picks":
    b, s = st.columns(2)
    with b:
        st.subheader("🏆 Top Buy")
        for sym in ["RELIANCE", "HDFCBANK", "L&T", "TCS", "ICICIBANK"]: st.markdown(f'<div class="pick-card"><b>{sym}</b></div>', unsafe_allow_html=True)
    with s:
        st.subheader("⚠️ Top Sell")
        for sym in ["IDEA", "PAYTM", "YESBANK", "RPOWER", "NYKAA"]: st.markdown(f'<div class="sell-card"><b>{sym}</b></div>', unsafe_allow_html=True)

elif selected == "Market News":
    st.subheader("📰 Market Intelligence")
    try:
        news = yf.Ticker("^NSEI").news
        for n in news[:8]:
            st.markdown(f"**{n['title']}**")
            st.caption(f"{n['publisher']} | [Link]({n['link']})")
            st.divider()
    except: st.error("News unavailable.")
