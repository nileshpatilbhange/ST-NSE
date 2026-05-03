# --- AI CAPITAL PLANNER (MANUAL INPUT VERSION) ---
elif selected == "AI Capital Planner":
    st.subheader("🤖 AI Capital Allocation Engine")
    col_input, col_output = st.columns([1, 1.5])
    
    with col_input:
        # 1. USER ADDS SIP AMOUNT
        monthly_sip = st.number_input("Monthly SIP Amount (₹)", min_value=500, value=5000, step=500)
        
        # 2. USER ADDS LUMPSUM AMOUNT
        lump_total = st.number_input("One-time Lumpsum to Deploy (₹)", min_value=0, value=50000, step=5000)
        
        horizon = st.select_slider("Time Horizon", options=[1, 3, 5], format_func=lambda x: f"{x} Year{'s' if x > 1 else ''}")
        risk = st.select_slider("Risk Appetite", options=["Conservative", "Moderate", "Aggressive"])
        
        # Risk-based expected return configurations
        config = {
            "Conservative": {"return": 0.11}, 
            "Moderate": {"return": 0.14}, 
            "Aggressive": {"return": 0.18}
        }
        exp_return = config[risk]["return"]
        total_invested = (monthly_sip * horizon * 12) + lump_total

    with col_output:
        st.markdown(f"### Strategy: {risk} Growth Model")
        st.markdown(f'<p class="equation-text">Target Index Allocation ({risk})</p>', unsafe_allow_html=True)
        
        if risk == "Aggressive":
            indices = ["Nifty Smallcap 250 (30%)", "Nifty Midcap 150 (25%)", "Nifty IT Index (20%)", "Nifty Bank (15%)", "Microcap Index (10%)"]
            stocks = ["Zomato", "Jio Financial", "Suzlon", "Trent", "Mazagon Dock"]
        elif risk == "Moderate":
            indices = ["Nifty 50 Index (40%)", "Nifty Next 50 (20%)", "Nifty Midcap 100 (20%)", "Bank Nifty (10%)", "Nifty Auto (10%)"]
            stocks = ["Reliance", "ICICI Bank", "L&T", "M&M", "Titan"]
        else:
            indices = ["Nifty 50 Index (50%)", "Gold ETF (20%)", "Nifty Low Volatility 30 (15%)", "Liquid Fund (10%)", "Nifty Pharma (5%)"]
            stocks = ["TCS", "HUL", "HDFC Bank", "ITC", "Asian Paints"]
            
        st.info("**Index Diversification (Top 5):**\n" + "\n".join([f"- {i}" for i in indices]))
        st.divider()
        st.markdown(f'<p class="equation-text">Stock Selection for Lumpsum (₹{lump_total:,.0f})</p>', unsafe_allow_html=True)
        st.success("**Stock Diversification (Top 5):**\n" + ", ".join(stocks))
        
        # --- CALCULATION LOGIC ---
        n = horizon * 12
        r_m = exp_return / 12
        # Future Value of SIP
        fv_sip = monthly_sip * (((1 + r_m)**n - 1) / r_m) * (1 + r_m)
        # Future Value of Lumpsum
        fv_lump = lump_total * (1 + exp_return)**horizon
        total_fv = fv_sip + fv_lump
        
        st.divider()
        st.markdown(f'''
            <div class="metric-card">
                <small>ESTIMATED TOTAL VALUE AFTER {horizon} YEAR(S)</small><br>
                <span style="font-size:28px; color:#c8a45e">₹{total_fv:,.0f}</span><br>
                <small style="color:#888">Total Invested: ₹{total_invested:,.0f} | Net Gain: ₹{total_fv - total_invested:,.0f}</small>
            </div>
            ''', unsafe_allow_html=True)
