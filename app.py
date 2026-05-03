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
    .stApp { background-color: #05070a; color: #ffffff; }
    .brand-container { text-align: center; padding: 20px 0; background: #0d1117; border-radius: 0 0 30px 30px; margin-bottom: 20px; border-bottom: 1px solid #c8a45e44; }
    .logo-text { font-size: 38px; font-weight: 800; color: #c8a45e; margin: 0; }
    .metric-card { background: #0d1117; border: 1px solid #c8a45e33; padding: 15px; border-radius: 12px; margin-bottom: 10px; }
    .equation-text { font-family: 'Courier New', monospace; color: #c8a45e; font-size: 16px; font-weight: bold; }
    .stButton>button { border-color: #c8a45e33 !important; color: #c8a45e !important; background-color: #0d1117 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- NAVIGATION ---
st.markdown('<div class="brand-container"><div class="logo-text">⚡ QUANTUM NSE</div></div>', unsafe_allow_html=True)
selected = option_menu(None, ["Analysis", "Top 10 Picks", "AI Capital Planner", "Market News"], 
    icons=["search", "trophy", "calculator", "newspaper"], orientation="horizontal",
    styles={"nav-link-selected": {"background-color": "#c8a45e", "color": "#05070a"}})

# --- 1. AI CAPITAL PLANNER ---
if selected == "AI Capital Planner":
    st.subheader("🤖 AI Capital Allocation Engine")
    col_input, col_output = st.columns([1, 1.5])
    
    with col_input:
        total_cap = st.number_input("Total Capital (₹)", min_value=10000, value=100000, step=10000)
        horizon = st.select_slider("Time Horizon", options=[1, 3, 5], format_func=lambda x: f"{x} Yr")
        risk = st.select_slider("Risk Appetite", options=["Conservative", "Moderate", "Aggressive"])
        
        config = {
            "Conservative": {"sip": 0.8, "lump": 0.2, "return": 0.11},
            "Moderate": {"sip": 0.6, "lump": 0.4, "return": 0.14},
            "Aggressive": {"sip": 0.4, "lump": 0.6, "return": 0.18}
        }
        
        sip_val = total_cap * config[risk]["sip"]
        lump_val = total_cap * config[risk]["lump"]
        monthly_sip = sip_val / (horizon * 12)

    with col_output:
        st.markdown(f"### {risk} Strategy Allocation")
        st.markdown(f'<p class="equation-text">Monthly SIP = ₹{monthly_sip:,.0f}</p>', unsafe_allow_html=True)
        
        # Exact Indices and Stocks based on your logic
        if risk == "Aggressive":
            indices = ["Nifty Smallcap 250 (30%)", "Nifty Midcap 150 (25%)", "Nifty IT Index (20%)", "Nifty Bank (15%)", "Microcap Index (10%)"]
            stocks = ["Zomato", "Jio Financial", "Suzlon", "Trent", "Mazagon Dock"]
        elif risk == "Moderate":
            indices = ["Nifty 50 Index (40%)", "Nifty Next 50 (20%)", "Nifty Midcap 100 (20%)", "Bank Nifty (10%)", "Nifty Auto (10%)"]
            stocks = ["Reliance", "ICICI Bank", "L&T", "M&M", "Titan"]
        else: # Conservative
            indices = ["Nifty 50 Index (50%)", "Gold ETF (20%)", "Nifty Low Volatility 30 (15%)", "Liquid Fund (10%)", "Nifty Pharma (5%)"]
            stocks = ["TCS", "HUL", "HDFC Bank", "ITC", "Asian Paints"]

        st.info("**Index Diversification:**\n" + "\n".join([f"- {i}" for i in indices]))
        st.divider()
        st.markdown(f'<p class="equation-text">Stock Lumpsum = ₹{lump_val:,.0f}</p>', unsafe_allow_html=True)
        st.success(f"**Stock Picks:** {', '.join(stocks)}")

        # Projection
        n, r_m = horizon * 12, config[risk]["return"] / 12
        fv = (monthly_sip * (((1 + r_m)**n - 1) / r_m) * (1 + r_m)) + (lump_val * (1 + config[risk]["return"])**horizon)
        st.markdown(f'<div class="metric-card"><small>ESTIMATED TOTAL VALUE</small><br><span style="font-size:24px; color:#c8a45e">₹{fv:,.0f}</span></div>', unsafe_allow_html=True)

# --- 2. ANALYSIS (STOCK SEARCH) ---
elif selected == "Analysis":
    ticker = st.text_input("", placeholder="Enter NSE Ticker (e.g. RELIANCE)...").upper()
    if ticker:
        symbol = f"{ticker}.NS"
        try:
            data = yf.Ticker(symbol)
            hist = data.history(period="1y")
            if hist.empty: st.warning("Ticker not found on NSE.")
            else:
                st.subheader(f"📊 {data.info.get('longName', ticker)}")
                fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], 
                                                    increasing_line_color='#c8a45e', decreasing_line_color='#888')])
                fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
                
                c1, c2, c3 = st.columns(3)
                c1.markdown(f'<div class="metric-card"><small>LTP</small><br>₹{hist["Close"].iloc[-1]:,.2f}</div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="metric-card"><small>52W High</small><br>₹{hist["High"].max():,.2f}</div>', unsafe_allow_html=True)
                c3.markdown(f'<div class="metric-card"><small>Market Cap</small><br>₹{data.info.get("marketCap", 0)/10**7:,.0f} Cr</div>', unsafe_allow_html=True)
        except Exception as e: st.error("Error fetching data. Check ticker.")

# --- 3. TOP 10 & 4. NEWS (STUBS) ---
elif selected == "Top 10 Picks":
    st.write("Displaying institutional high-conviction picks...")
    st.table(pd.DataFrame({"Buy": ["RELIANCE", "TCS", "HDFC", "ICICI", "L&T"], "Avoid": ["IDEA", "PAYTM", "YESBANK", "RPOWER", "VI"]}))
elif selected == "Market News":
    st.write("Live feed from Business Standard/MoneyControl...")
