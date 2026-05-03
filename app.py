import streamlit as st
import pandas as pd

# --- UPDATED AI-DRIVEN RECO LOGIC (2026 DATA) ---
def get_recommendations(risk):
    if risk == "Aggressive":
        # Focus: AI Software, Data Centers, and Semiconductors
        indices = ["Nifty Midcap 150 Momentum 50 (35%)", "Nifty Smallcap 250 (25%)", "Nifty IT Index (20%)", "Data Center/Infra ETF (10%)", "Nifty Next 50 (10%)"]
        stocks = ["Persistent Systems (AI Services)", "Saksoft (AI/Analytics)", "Netweb Tech (Supercomputing)", "KPIT Tech (Automotive AI)", "Kaynes Tech (Semiconductors)"]
        ret = 0.18  # 18% Expected CAGR
    elif risk == "Moderate":
        # Focus: Core AI Adoption + Strong Financials
        indices = ["Nifty 50 Index (40%)", "Nifty Next 50 (20%)", "Nifty Midcap 100 (15%)", "Nifty IT (15%)", "Gold ETF (10%)"]
        stocks = ["Reliance (Jio AI)", "ICICI Bank (Digital Ops)", "Oracle Financial (Banking AI)", "L&T (Infra/Digital)", "Tata Elxsi (Design AI)"]
        ret = 0.14  # 14% Expected CAGR
    else: # Conservative
        # Focus: High Cash Flow & Stability
        indices = ["Nifty 50 Index (60%)", "Gold ETF (15%)", "Nifty Low Volatility 30 (10%)", "Liquid Fund (10%)", "Nifty Pharma (5%)"]
        stocks = ["TCS (Large Cap AI)", "HDFC Bank (Institutional)", "Bosch (Industrial AI)", "HUL (Defensive)", "Asian Paints (Stability)"]
        ret = 0.11  # 11% Expected CAGR
    return indices, stocks, ret

# --- INTERFACE ---
st.subheader("🤖 AI Capital Allocation Engine")

col_a, col_b = st.columns([1, 1.5])

with col_a:
    total_cap = st.number_input("Total Capital to Deploy (₹)", min_value=10000, value=100000, step=10000)
    horizon = st.select_slider("Time Horizon", options=[1, 3, 5], format_func=lambda x: f"{x} Year{'s' if x > 1 else ''}")
    risk = st.select_slider("Risk Appetite", options=["Conservative", "Moderate", "Aggressive"])

    # Allocation Logic
    ratio_sip = 0.8 if risk == "Conservative" else (0.6 if risk == "Moderate" else 0.4)
    ratio_lump = 1 - ratio_sip
    
    indices, stocks, exp_return = get_recommendations(risk)
    
    sip_total = total_cap * ratio_sip
    lump_total = total_cap * ratio_lump
    monthly_sip = sip_total / (horizon * 12)

with col_b:
    st.markdown(f"### Strategy: {risk} AI Allocation")
    
    # SIP Equation & Diversification
    st.markdown(f"**Monthly SIP = ₹{monthly_sip:,.0f}**")
    st.caption(f"Top 5 Index/Fund Recommendations for {risk} Profile:")
    for i in indices:
        st.write(f"🔹 {i}")
    
    st.divider()
    
    # Lumpsum Equation & Diversification
    st.markdown(f"**Stock Lumpsum = ₹{lump_total:,.0f}**")
    st.caption(f"Top 5 AI & Value Chain Stocks for {risk} Profile:")
    st.success(", ".join(stocks))

    # PROJECTION CALCULATION
    n = horizon * 12
    r_m = exp_return / 12
    # FV of SIP + FV of Lumpsum
    fv_sip = monthly_sip * (((1 + r_m)**n - 1) / r_m) * (1 + r_m)
    fv_lump = lump_total * (1 + exp_return)**horizon
    total_fv = fv_sip + fv_lump
    
    st.divider()
    st.markdown(f"""
        <div style="background:#0d1117; border:1px solid #c8a45e33; padding:20px; border-radius:12px">
            <small style="color:#888">APPROXIMATE MATURITY VALUE ({horizon}Y)</small><br>
            <span style="font-size:32px; color:#c8a45e; font-weight:bold">₹{total_fv:,.0f}</span><br>
            <small style="color:#00ff00">Est. Growth: +₹{total_fv - total_cap:,.0f} ({((total_fv/total_cap)-1)*100:.1f}%)</small>
        </div>
    """, unsafe_allow_html=True)
