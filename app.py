import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

# --- UI CONFIGURATION ---
st.set_page_config(page_title="QUANTUM NSE | AI Terminal", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS (THE GOLD STANDARD THEME) ---
st.markdown("""
    <style>
    .stApp { background-color: #05070a; color: #ffffff; }
    .brand-container { 
        text-align: center; 
        padding: 30px 0; 
        background: #0d1117; 
        border-radius: 0 0 30px 30px; 
        margin-bottom: 20px; 
        border-bottom: 1px solid #c8a45e44; 
    }
    .logo-text { font-size: 42px; font-weight: 800; color: #c8a45e; margin: 0; }
    .branding-tagline { font-size: 16px; color: #888; font-style: italic; margin-top: 5px; }
    
    div[data-testid="stTable"] td, div[data-testid="stTable"] th {
        color: #ffffff !important; font-size: 14px !important; border-bottom: 1px solid #30363d !important;
        background-color: #0d1117 !important;
    }
    .metric-card { background: #0d1117; border: 1px solid #c8a45e33; padding: 15px; border-radius: 12px; text-align: center; }
    .status-box { padding: 10px; border-radius: 8px; font-weight: bold; text-align: center; margin-bottom: 10px; }
    .pick-card { background: #0d1117; border-left: 5px solid #c8a45e; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
    .sell-card { background: #0d1117; border-left: 5px solid #ff4b4b; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
    
    .stButton>button { border-color: #c8a45e33 !important; color: #c8a45e !important; background-color: #0d1117 !important; transition: 0.3s; }
    .stButton>button:hover { border-color: #c8a45e !important; color: #ffffff !important; background-color: #c8a45e22 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINES ---
@st.cache_data(ttl=600)
def get_index_data():
    indices = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "SENSEX": "^BSESN", "NIFTY IT": "^CNXIT", "NIFTY AUTO": "^CNXAUTO", "NIFTY PHARMA": "^CNXPHARMA"}
    data = {}
    for name, sym in indices.items():
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="5d")
            if len(hist) >= 2:
                price, change = hist['Close'].iloc[-1], ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
                data[name] = (price, change, sym)
        except: continue
    return data

# --- BRANDING ---
st.markdown('<div class="brand-container"><div class="logo-text">⚡ QUANTUM NSE</div><div class="branding-tagline">"Precision Intelligence for the Modern Indian Investor."</div></div>', unsafe_allow_html=True)

# --- INDEX TICKER TAPE ---
idx_data = get_index_data()
if idx_data:
    cols = st.columns(len(idx_data))
    for i, (name, val) in enumerate(idx_data.items()):
        if cols[i].button(f"{name}\n{val[0]:,.0f} ({val[1]:.2f}%)"):
            st.session_state.selected_index = val[2]
            st.session_state.idx_display_name = name

# --- NAVIGATION ---
selected = option_menu(None, ["Analysis", "Top 10 Picks", "AI Capital Planner", "Market News"], 
    icons=["search", "trophy", "calculator", "newspaper"], orientation="horizontal",
    styles={"container": {"background-color": "#0d1117", "border": "1px solid #c8a45e22"},
            "nav-link-selected": {"background-color": "#c8a45e", "color": "#05070a", "font-weight": "bold"}})

# --- INDEX CHART DISPLAY ---
if 'selected_index' in st.session_state:
    idx_hist = yf.Ticker(st.session_state.selected_index).history(period="3y")
    fig_idx = go.Figure(data=[go.Scatter(x=idx_hist.index, y=idx_hist['Close'], line=dict(color='#c8a45e', width=2))])
    fig_idx.update_layout(template="plotly_dark", height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_idx, use_container_width=True)
    if st.button("Close Index Action"): 
        del st.session_state.selected_index
        st.rerun()

# --- ANALYSIS PAGE ---
if selected == "Analysis":
    search = st.text_input("", placeholder="Search Stock Ticker (e.g., RELIANCE)...").upper()
    if search:
        t_sym = f"{search}.NS"
        stock = yf.Ticker(t_sym)
        info, hist = stock.info, stock.history(period="3y")
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            pe, peg, roe, debt_to_equity = info.get('trailingPE', 0), info.get('pegRatio', 0), info.get('returnOnEquity', 0) * 100, info.get('debtToEquity', 0)
            sector, pledged, hold_insider = info.get('sector', 'Unknown'), info.get('pledgedPercent', 0) or 0, info.get('heldPercentInsiders', 0) * 100
            valuation, ma200 = ("Undervalued" if pe < 20 else "Overvalued"), hist['Close'].rolling(200).mean().iloc[-1]
            sentiment = "Bullish" if current_price > ma200 else "Bearish"
            score = sum([20 if pe < 25 else 0, 20 if roe > 15 else 0, 20 if (debt_to_equity/100) < 1 else 0, 20 if 0.8 <= peg <= 1.2 else 0, 20 if sentiment == "Bullish" else 0])
            
            st.subheader(f"💎 Analysis: {info.get('longName', search)}")
            c1, c2, c3 = st.columns(3)
            c1.markdown(f'<div class="metric-card"><small>Current Price</small><br><span style="font-size:24px; color:#c8a45e">₹{current_price:,.2f}</span></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="metric-card"><small>Health Score</small><br><span style="font-size:24px; color:#c8a45e">{score}/100</span></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="metric-card"><small>Valuation</small><br><span style="font-size:24px; color:{"#c8a45e" if valuation == "Undervalued" else "#ff4b4b"}">{valuation}</span></div>', unsafe_allow_html=True)
            
            try:
                fin = stock.financials.T
                fin_df = pd.DataFrame({"Year": fin.index.year, "Net Profit (Cr)": (fin['Net Income'] / 1e7).round(2), "Growth %": fin['Net Income'].pct_change().fillna(0).apply(lambda x: f"{x*100:+.2f}%")}).reset_index(drop=True)
                st.table(fin_df)
            except: st.error("Financials unavailable.")
            
            fig = go.Figure(data=[go.Scatter(x=hist.index, y=hist['Close'], line=dict(color='#c8a45e'))])
            fig.update_layout(template="plotly_dark", height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

# --- AI CAPITAL PLANNER (NEW 4TH MODULE) ---
elif selected == "AI Capital Planner":
    st.subheader("🤖 Quantum AI Capital Allocation")
    col_a, col_b = st.columns([1, 2])
    
    with col_a:
        amt = st.number_input("Investment Amount (₹)", min_value=5000, value=50000, step=5000)
        horizon = st.radio("Time Horizon", [3, 5], format_func=lambda x: f"{x} Years")
        risk = st.select_slider("Risk Appetite", options=["Conservative", "Moderate", "Aggressive"])
        
    with col_b:
        st.markdown(f'<div class="metric-card" style="text-align:left"><b>AI Strategy for ₹{amt:,.0f} over {horizon} years:</b><br><br>'
                    f'70% Allocation: <b>Index SIP (Wealth Compounder)</b><br>'
                    f'30% Allocation: <b>Satellite Stocks (Alpha Generator)</b></div>', unsafe_allow_html=True)
        
        s1, s2 = st.columns(2)
        sip_amt = (amt * 0.7) / (horizon * 12)
        stock_pool = amt * 0.3
        
        with s1:
            st.info(f"Monthly SIP: ₹{sip_amt:,.0f}")
            st.markdown("- **Nifty 50 Index Fund** (40%)\n- **Nifty Next 50** (30%)\n- **Midcap 150 Index** (30%)")
        with s2:
            st.success(f"Stock Lumpsum: ₹{stock_pool:,.0f}")
            st.markdown("- **Reliance** (Bluechip)\n- **TCS** (Cash Rich)\n- **HDFC Bank** (Valuation Play)")

# --- TOP 10 PICKS ---
elif selected == "Top 10 Picks":
    b, s = st.columns(2)
    with b:
        st.subheader("🏆 Top 10 Strong Buy")
        for sym, res in [("RELIANCE", "Green Energy Expansion"), ("HDFCBANK", "Banking Gold Standard"), ("L&T", "Infra Pipeline"), ("BHARTIARTL", "5G ARPU Growth"), ("TCS", "AI Deal Pipeline"), ("ICICIBANK", "Superior Asset Quality"), ("BAJFINANCE", "Lending Leader"), ("M&M", "EV & SUV Dominance"), ("HUL", "Zero Debt Defensive"), ("INFY", "High FCF")]:
            st.markdown(f'<div class="pick-card"><b>{sym}</b><br>{res}</div>', unsafe_allow_html=True)
    with s:
        st.subheader("⚠️ Top 10 Strong Sell")
        for sym, res in [("IDEA", "Debt Stress"), ("PAYTM", "Regulatory Issues"), ("YESBANK", "Slow Recovery"), ("RPOWER", "Inconsistent Cash"), ("NYKAA", "Margin Pressure"), ("PEL", "Stressed Exposure"), ("SUZLON", "Overextended"), ("DELHIVERY", "Structural Loss"), ("AWL", "Valuation Gap"), ("DIXON", "Low Margin")]:
            st.markdown(f'<div class="sell-card"><b>{sym}</b><br>{res}</div>', unsafe_allow_html=True)

# --- NEWS PAGE ---
elif selected == "Market News":
    st.subheader("📰 Business Standard Intelligence")
    try:
        news_data = yf.Ticker("^NSEI").news
        bs_news = [n for n in news_data if "Business Standard" in n.get('publisher', '')]
        other_news = [n for n in news_data if "Business Standard" not in n.get('publisher', '')]
        for n in (bs_news + other_news)[:10]:
            st.markdown(f"{'⭐' if 'Business Standard' in n.get('publisher','') else ''} **{n.get('title')}**")
            st.caption(f"Source: {n.get('publisher')} | [Read Story]({n.get('link')})")
            st.divider()
    except: st.info("News feed currently unavailable.")
