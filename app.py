import streamlit as st
import pandas as pd
import numpy as np

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="QUANTUM NSE | AI Terminal", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #05070a; color: #e0e0e0; }
    .stNumberInput, .stSelectbox, .stSlider { background-color: #0d1117 !important; }
    .equation-box { 
        background: #0d1117; 
        border: 1px solid #c8a45e44; 
        padding: 20px; 
        border-radius: 15px; 
        font-family: 'Courier New', monospace;
        margin-bottom: 20px;
    }
    .metric-value { color: #c8a45e; font-size: 2.5rem; font-weight: bold; }
    .reco-card { 
        background: #161b22; 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 5px solid #c8a45e;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE LOGIC & 2026 DATA ---
def get_ai_engine_data(risk):
    """Returns 2026-specific data based on latest market trends."""
    if risk == "Aggressive":
        indices = [
            "Nifty Midcap 150 Momentum 50 (35%)",
            "Nifty Smallcap 250 Index (25%)",
            "Nifty India Manufacturing Index (20%)",
            "Nifty IT Index (10%)",
            "Data Center & Infra ETF (10%)"
        ]
        stocks = [
            "Netweb Technologies (AI Supercomputing)",
            "Kaynes Technology (Semiconductors)",
            "Persistent Systems (AI/Cloud)",
            "Saksoft Ltd (Niche AI Services)",
            "Mazagon Dock (Defense/AI Systems)"
        ]
        annual_return = 0.18 # 18% Target
        sip_weight = 0.4     # 40% SIP, 60% Lumpsum
    
    elif risk == "Moderate":
        indices = [
            "Nifty 50 Index (40%)",
            "Nifty Next 50 (20%)",
            "Nifty Midcap 100 (20%)",
            "Nifty IT Index (10%)",
            "Gold ETF (10%)"
        ]
        stocks = [
            "Reliance Industries (Jio AI Ecosystem)",
            "Tata Elxsi (AI Design Engineering)",
            "Oracle Financial Services (Banking AI)",
            "Larsen & Toubro (Data Center Infra)",
            "ICICI Bank (Digital Transformation)"
        ]
        annual_return = 0.14 # 14% Target
        sip_weight = 0.6     # 60% SIP, 40% Lumpsum
        
    else: # Conservative
        indices = [
            "Nifty 50 Index (60%)",
            "Gold ETF (15%)",
            "Nifty Low Volatility 30 (10%)",
            "Liquid Fund (10%)",
            "Nifty Pharma Index (5%)"
        ]
        stocks = [
            "TCS (AI Services Leader)",
            "Bosch Ltd (Industrial AI)",
            "HDFC Bank (Institutional Strength)",
            "Hindustan Unilever (Consumer Base)",
            "Asian Paints (Stability)"
        ]
        annual_return = 0.11 # 11% Target
        sip_weight = 0.8     # 80% SIP, 20% Lumpsum
        
    return indices, stocks, annual_return, sip_weight

# --- 3. UI LAYOUT ---
st.title("⚡ QUANTUM NSE: AI Capital Planner")
st.write("---")

col_input, col_display = st.columns([1, 2])

with col_input:
    st.subheader("Investment Parameters")
    total_capital = st.number_input("Total Capital to Invest (₹)", min_value=10000, value=100000, step=5000)
    horizon = st.select_slider("Time Horizon", options=[1, 3, 5], format_func=lambda x: f"{x} Year{'s' if x > 1 else ''}")
    risk = st.select_slider("Risk Appetite", options=["Conservative", "Moderate", "Aggressive"])
    
    # Calculate Ratios
    indices, stocks, exp_return, sip_w = get_ai_engine_data(risk)
    lump_w = 1 - sip_w
    
    sip_total_pool = total_capital * sip_w
    lump_total_pool = total_capital * lump_w
    monthly_sip_val = sip_total_pool / (horizon * 12)

with col_display:
    st.subheader(f"Allocation Strategy: {risk}")
    
    # --- SIP EQUATION ---
    st.markdown(f"""
    <div class="equation-box">
        <span style="color:#888"># SIP ALLOCATION ENGINE</span><br>
        Monthly SIP = (₹{monthly_sip_val:,.0f}) Index Recommendation ({risk})
    </div>
    """, unsafe_allow_html=True)
    
    st.write("**Top 5 Diversified Indices:**")
    cols_idx = st.columns(2)
    for idx, name in enumerate(indices):
        cols_idx[idx % 2].markdown(f'<div class="reco-card">🔹 {name}</div>', unsafe_allow_html=True)

    st.write("---")

    # --- LUMPSUM EQUATION ---
    st.markdown(f"""
    <div class="equation-box">
        <span style="color:#888"># LUMPSUM ALLOCATION ENGINE</span><br>
        Stock Lumpsum = (₹{lump_total_pool:,.0f}) Stock Recommendation ({risk})
    </div>
    """, unsafe_allow_html=True)
    
    st.write("**Top 5 AI-Driven Stock Picks:**")
    st.success(" | ".join(stocks))

# --- 4. RETURNS CALCULATION ---
st.write("---")
st.subheader("📈 Approximate Returns Projection")

# Compound Interest Formula for SIP + Lumpsum
n_months = horizon * 12
monthly_rate = exp_return / 12

# FV of SIP = P * [((1 + r)^n - 1) / r] * (1 + r)
fv_sip = monthly_sip_val * (((1 + monthly_rate)**n_months - 1) / monthly_rate) * (1 + monthly_rate)
# FV of Lumpsum = P * (1 + r)^t
fv_lumpsum = lump_total_pool * (1 + exp_return)**horizon

total_final = fv_sip + fv_lumpsum
net_profit = total_final - total_capital

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Expected Maturity Value", f"₹{total_final:,.0f}")
with c2:
    st.metric("Net Gain", f"₹{net_profit:,.0f}", f"{exp_return*100:.1f}% Est. CAGR")
with c3:
    st.metric("Timeframe", f"{horizon} Years")

st.info("💡 **AI Analyst Note:** These recommendations are based on May 2026 market leadership in AI infrastructure and high-growth momentum. Always review with a financial advisor before deploying capital.")
