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
        total_cap = st.number_input("Total Capital to Deploy (₹)", min_value=10000, value=100000, step=10000)
        horizon = st.select_slider("Time Horizon", options=[1, 3, 5], format_func=lambda x: f"{x} Year{'s' if x > 1 else ''}")
        risk = st.select_slider("Risk Appetite", options=["Conservative", "Moderate", "Aggressive"])
        
        # Internal Logic for Ratios & Expected Returns
        config = {
            "Conservative": {"sip": 0.8, "lump": 0.2, "return": 0.11},
            "Moderate": {"sip": 0.6, "lump": 0.4, "return": 0.14},
            "Aggressive": {"sip": 0.4, "lump": 0.6, "return": 0.18}
        }
        
        s_ratio = config[risk]["sip"]
        l_ratio = config[risk]["lump"]
        exp_return = config[risk]["return"]
        
        sip_total = total_cap * s_ratio
        lump_total = total_cap * l_ratio
        monthly_sip = sip_total / (horizon * 12)

    with col_output:
        st.markdown(f"### Strategy: {risk} Allocation")
        
        # Monthly SIP Equation
        st.markdown(f'<p class="equation-text">Monthly SIP = ₹{monthly_sip:,.0f} Index Recommendation ({risk})</p>', unsafe_allow_html=True)
        
        # Recommendations
        if risk == "Aggressive":
            indices = ["Nifty Smallcap 250 (30%)", "Nifty Midcap 150 (25%)", "Nifty IT Index (20%)", "Nifty Bank (15%)", "Microcap Index (10%)"]
            stocks = ["Zomato", "Jio Financial", "Suzlon", "Trent", "Mazagon Dock"]
        elif risk == "Moderate":
            indices = ["Nifty 50 Index (40%)", "Nifty Next 50 (20%)", "Nifty Midcap 100 (20%)", "Bank Nifty (10%)", "Nifty Auto (10%)"]
            stocks = ["Reliance", "ICICI Bank", "L&T", "M&M", "Titan"]
        else: # Conservative
            indices = ["Nifty 50 Index (50%)", "Gold ETF (20%)", "Nifty Low Volatility 30 (15%)", "Liquid Fund (10%)", "Nifty Pharma (5%)"]
            stocks = ["TCS", "HUL", "HDFC Bank", "ITC", "Asian Paints"]

        st.info("**Index Diversification (Top 5):**\n" + "\n".join([f"- {i}" for i in indices]))
        st.divider()
        
        # Lumpsum Equation
        st.markdown(f'<p class="equation-text">Stock Lumpsum = ₹{lump_total:,.0f} Stock Recommendation ({risk})</p>', unsafe_allow_html=True)
        st.success("**Stock Diversification (Top 5):**\n" + ", ".join(stocks))

        # APPROXIMATE RETURNS CALCULATION
        n = horizon * 12
        r_m = exp_return / 12
        fv_sip = monthly_sip * (((1 + r_m)**n - 1) / r_m) * (1 + r_m)
        fv_lump = lump_total * (1 + exp_return)**horizon
        total_fv = fv_sip + fv_lump
        
        st.divider()
        st.markdown(f"""
            <div class="metric-card">
                <small>ESTIMATED TOTAL VALUE AFTER {horizon} YEAR(S)</small><br>
                <span style="font-size:28px; color:#c8a45e">₹{total_fv:,.0f}</span><br>
                <small style="color:#888">Approx. Net Gain: ₹{total_fv - total_cap:,.0f} ({((total_fv/total_cap)-1)*100:.1f}%)</small>
            </div>
        """, unsafe_allow_html=True)

# --- 2. ANALYSIS PAGE ---
elif selected == "Analysis":
    search = st.text_input("", placeholder="Enter Ticker (e.g. RELIANCE)...").upper()
    if search:
        t_sym = f"{search}.NS"
        stock = yf.Ticker(t_sym)
        try:
            hist = stock.history(period="3y")
            info = stock.info
            if not hist.empty:
                st.subheader(f"💎 Analysis: {info.get('longName', search)}")
                # Price Chart
                fig = go.Figure(data=[go.Scatter(x=hist.index, y=hist['Close'], line=dict(color='#c8a45e'))])
                fig.update_layout(template="plotly_dark", height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
                
                # Metrics
                m1, m2, m3 = st.columns(3)
                m1.markdown(f'<div class="metric-card"><small>Price</small><br>₹{hist["Close"].iloc[-1]:,.2f}</div>', unsafe_allow_html=True)
                m2.markdown(f'<div class="metric-card"><small>P/E Ratio</small><br>{info.get("trailingPE", "N/A")}</div>', unsafe_allow_html=True)
                m3.markdown(f'<div class="metric-card"><small>ROE</small><br>{(info.get("returnOnEquity", 0)*100):.2f}%</div>', unsafe_allow_html=True)
        except:
            st.error("Ticker not found. Please use NSE symbols.")

# --- 3. TOP 10 PICKS ---
elif selected == "Top 10 Picks":
    st.subheader("🏆 Institutional Recommendations")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Top 10 Buy**")
        for s in ["RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "L&T", "BHARTIARTL", "ITC", "SBI", "KOTAKBANK"]:
            st.code(s)
    with col2:
        st.write("**Top 10 Avoid**")
        for s in ["IDEA", "PAYTM", "YESBANK", "RPOWER", "SUZLON", "ZOMATO", "NYKAA", "ADANIPOWER", "JPASSOCIAT", "VI"]:
            st.code(s)

# --- 4. MARKET NEWS ---
elif selected == "Market News":
    st.subheader("📰 Market Intelligence")
    try:
        news_data = yf.Ticker("^NSEI").news
        for n in news_data[:8]:
            st.markdown(f"**{n.get('title')}**")
            st.caption(f"Source: {n.get('publisher')} | [Read Story]({n.get('link')})")
            st.divider()
    except:
        st.info("News feed currently unavailable.")
