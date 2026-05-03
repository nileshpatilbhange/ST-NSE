import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

# --- UI CONFIGURATION ---
st.set_page_config(page_title="QUANTUM NSE | AI Terminal", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS (MIDNIGHT & GOLD THEME) ---
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
    
    /* Button Styling */
    .stButton>button { border-color: #c8a45e33 !important; color: #c8a45e !important; background-color: #0d1117 !important; }
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
            hist = ticker.history(period="5d")
            if len(hist) >= 2:
                price = hist['Close'].iloc[-1]
                change = ((price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
                data[name] = (price, change, sym)
        except: continue
    return data

# --- BRANDING SECTION ---
st.markdown("""
    <div class="brand-container">
        <div class="logo-text">⚡ QUANTUM NSE</div>
        <div class="branding-tagline">"Precision Intelligence for the Modern Indian Investor."</div>
    </div>
    """, unsafe_allow_html=True)

idx_data = get_index_data()
if idx_data:
    cols = st.columns(len(idx_data))
    for i, (name, val) in enumerate(idx_data.items()):
        if cols[i].button(f"{name}\n{val[0]:,.0f} ({val[1]:.2f}%)"):
            st.session_state.selected_index = val[2]
            st.session_state.idx_display_name = name

# --- NAVIGATION ---
selected = option_menu(None, ["Analysis", "Top 10 Picks", "Market News"], 
    icons=["search", "trophy", "newspaper"], orientation="horizontal",
    styles={
        "container": {"background-color": "#0d1117", "padding": "0!important"},
        "nav-link-selected": {"background-color": "#c8a45e", "color": "#05070a"}
    })

# --- INDEX CHART DISPLAY (CORE LOGIC RESTORED) ---
if 'selected_index' in st.session_state:
    st.subheader(f"📈 {st.session_state.idx_display_name} Technical Chart")
    idx_hist = yf.Ticker(st.session_state.selected_index).history(period="1y")
    fig_idx = go.Figure(data=[go.Candlestick(x=idx_hist.index, open=idx_hist['Open'], high=idx_hist['High'], low=idx_hist['Low'], close=idx_hist['Close'])])
    fig_idx.update_layout(template="plotly_dark", height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_idx, use_container_width=True)
    if st.button("Close Index Chart"): 
        del st.session_state.selected_index
        st.rerun()

# --- ANALYSIS PAGE (FULL METRICS RESTORED) ---
if selected == "Analysis":
    search = st.text_input("", placeholder="Search Stock Ticker (e.g., RELIANCE)...").upper()
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
            sector = info.get('sector', 'Unknown')
            industry = info.get('industry', 'Unknown')
            pledged = info.get('pledgedPercent', 0) or 0
            hold_insider = info.get('heldPercentInsiders', 0) * 100
            
            valuation = "Undervalued" if pe < 20 else "Overvalued"
            ma200 = hist['Close'].rolling(200).mean().iloc[-1]
            sentiment = "Bullish" if current_price > ma200 else "Bearish"
            
            score = 0
            if pe < 25: score += 20
            if roe > 15: score += 20
            if (debt_to_equity/100) < 1: score += 20
            if 0.8 <= peg <= 1.2: score += 20
            if sentiment == "Bullish": score += 20
            
            st.subheader(f"💎 Analysis: {info.get('longName', search)}")
            c1, c2, c3 = st.columns(3)
            c1.markdown(f'<div class="metric-card"><small>Current Price</small><br><span style="font-size:24px; color:#c8a45e">₹{current_price:,.2f}</span></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="metric-card"><small>Health Score</small><br><span style="font-size:24px; color:#c8a45e">{score}/100</span></div>', unsafe_allow_html=True)
            v_color = "#c8a45e" if valuation == "Undervalued" else "#ff4b4b"
            c3.markdown(f'<div class="metric-card"><small>Valuation</small><br><span style="font-size:24px; color:{v_color}">{valuation}</span></div>', unsafe_allow_html=True)

            st.subheader("📊 Revenue & Profit Growth")
            try:
                fin = stock.financials.T
                fin_df = pd.DataFrame({
                    "Year": fin.index.year,
                    "Net Profit (Cr)": (fin['Net Income'] / 1e7).round(2),
                    "Growth %": fin['Net Income'].pct_change().fillna(0).apply(lambda x: f"{x*100:+.2f}%")
                }).reset_index(drop=True)
                st.table(fin_df)
            except: st.error("Growth data unavailable.")

            st.subheader("🔍 Vital Signal Audit")
            r1, r2, r3, r4 = st.columns(4)
            d_val = debt_to_equity / 100
            is_bank_infra = any(x in sector.lower() for x in ['bank', 'financial', 'infra', 'construction'])
            d_color = "#c8a45e" if (is_bank_infra and d_val <= 3) or (not is_bank_infra and d_val <= 1) else "#ff4b4b"
            
            r1.markdown(f'<div class="metric-card"><small>Debt-to-Equity</small><br><span style="color:{d_color}; font-size:20px">{d_val:.2f}</span></div>', unsafe_allow_html=True)
            r2.markdown(f'<div class="metric-card"><small>ROE</small><br><span style="color:{"#c8a45e" if roe >= 15 else "#ff4b4b"}; font-size:20px">{roe:.2f}%</span></div>', unsafe_allow_html=True)
            r3.markdown(f'<div class="metric-card"><small>P/E Ratio</small><br><span style="color:{"#c8a45e" if pe <= 25 else "#ff4b4b"}; font-size:20px">{pe:.2f}</span></div>', unsafe_allow_html=True)
            r4.markdown(f'<div class="metric-card"><small>PEG Ratio</small><br><span style="color:{"#c8a45e" if 0.8 <= peg <= 1.2 else "#ff4b4b"}; font-size:20px">{peg:.2f}</span></div>', unsafe_allow_html=True)

            st.divider()
            i1, i2, i3 = st.columns(3)
            i1.markdown(f'<div class="metric-card"><small>Promoter Holding</small><br><span style="color:{"#c8a45e" if pledged < 10 else "#ff4b4b"}; font-size:20px">{hold_insider:.1f}%</span></div>', unsafe_allow_html=True)
            i2.markdown(f'<div class="metric-card"><small>Industry: {industry}</small><br><span style="color:#c8a45e; font-size:20px">Growing</span></div>', unsafe_allow_html=True)
            
            verdict = "BUY" if score >= 70 else "WAIT"
            i3.markdown(f'<div class="status-box" style="background:{"#c8a45e" if verdict == "BUY" else "#ffcc00"}; color:#0d1117">VERDICT: {verdict}</div>', unsafe_allow_html=True)

            st.subheader("📈 3-Year Price Action")
            fig = go.Figure(data=[go.Scatter(x=hist.index, y=hist['Close'], line=dict(color='#c8a45e'))])
            fig.update_layout(template="plotly_dark", height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

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

# --- NEWS PAGE (With Business Standard Focus) ---
elif selected == "Market News":
    st.subheader("📰 Market Intelligence: Business Standard Focus")
    news_stock = yf.Ticker("^NSEI")
    try:
        news_data = news_stock.news
        if news_data:
            bs_news = [n for n in news_data if "Business Standard" in n.get('publisher', '')]
            other_news = [n for n in news_data if "Business Standard" not in n.get('publisher', '')]
            display_news = (bs_news + other_news)[:10]
            for n in display_news:
                title, publisher, link = n.get('title', 'N/A'), n.get('publisher', 'N/A'), n.get('link', '#')
                icon = "⭐" if "Business Standard" in publisher else ""
                st.markdown(f"{icon} **{title}**")
                st.caption(f"Source: {publisher} | [Read Story]({link})")
                st.divider()
    except Exception as e:
        st.error(f"Error fetching news: {e}")
