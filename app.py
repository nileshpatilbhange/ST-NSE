import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

# --- UI CONFIGURATION ---
st.set_page_config(page_title="QUANTUM NSE | AI Terminal", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS (Visibility Fixes) ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #ffffff; }
    .brand-container { text-align: center; padding: 20px 0; background: #161b22; border-radius: 0 0 30px 30px; margin-bottom: 20px; border-bottom: 1px solid #30363d; }
    .logo-text { font-size: 42px; font-weight: 800; color: #00ffcc; margin: 0; }
    .metric-card { background: #1c2128; border: 1px solid #30363d; padding: 15px; border-radius: 12px; text-align: center; }
    .status-box { padding: 15px; border-radius: 8px; font-weight: bold; text-align: center; margin: 10px 0; font-size: 18px; }
    div[data-testid="stTable"] td, div[data-testid="stTable"] th { color: #ffffff !important; background-color: #161b22 !important; }
    .stButton>button { width: 100%; background-color: #1c2128; color: #00ffcc; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINES ---
@st.cache_data(ttl=600)
def get_index_data():
    indices = {
        "NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "SENSEX": "^BSESN",
        "NIFTY IT": "^CNXIT", "NIFTY AUTO": "^CNXAUTO", "NIFTY PHARMA": "^CNXPHARMA"
    }
    data = []
    for name, sym in indices.items():
        try:
            t = yf.Ticker(sym)
            h = t.history(period="2d")
            p = h['Close'].iloc[-1]
            c = ((p - h['Close'].iloc[-2]) / h['Close'].iloc[-2]) * 100
            data.append({"name": name, "price": p, "change": c, "sym": sym})
        except: continue
    return data

# --- BRANDING ---
st.markdown('<div class="brand-container"><div class="logo-text">⚡ QUANTUM NSE</div></div>', unsafe_allow_html=True)

# --- INDICES TOP BAR (Interactive) ---
idx_list = get_index_data()
idx_cols = st.columns(len(idx_list))
for i, item in enumerate(idx_list):
    color = "#00ffcc" if item['change'] >= 0 else "#ff4b4b"
    if idx_cols[i].button(f"{item['name']}\n{item['price']:,.0f} ({item['change']:.2f}%)"):
        st.session_state.active_index = item['sym']
        st.session_state.active_name = item['name']

# --- INDEX CHART DISPLAY (Fixed Visibility) ---
if 'active_index' in st.session_state:
    st.subheader(f"📈 {st.session_state.active_name} Technical View")
    idx_h = yf.Ticker(st.session_state.active_index).history(period="1y")
    
    fig_idx = go.Figure(data=[go.Candlestick(x=idx_h.index, open=idx_h['Open'], high=idx_h['High'], low=idx_h['Low'], close=idx_h['Close'])])
    fig_idx.update_layout(
        template="plotly_dark", height=450,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(gridcolor='#30363d'), yaxis=dict(gridcolor='#30363d')
    )
    st.plotly_chart(fig_idx, use_container_width=True)
    if st.button("✖ Close Chart"):
        del st.session_state.active_index
        st.rerun()

# --- MAIN NAVIGATION ---
selected = option_menu(None, ["Analysis", "Top 10 Picks", "Market News"], 
    icons=["search", "trophy", "newspaper"], orientation="horizontal",
    styles={"nav-link-selected": {"background-color": "#00ffcc", "color": "#0d1117"}})

if selected == "Analysis":
    ticker = st.text_input("", placeholder="Enter Ticker (e.g. RELIANCE)...").upper()
    if ticker:
        stock = yf.Ticker(f"{ticker}.NS")
        info = stock.info
        hist = stock.history(period="3y")
        
        if not hist.empty:
            # 1. LOGIC CALCULATIONS
            curr_price = hist['Close'].iloc[-1]
            pe = info.get('trailingPE', 0) or 0
            peg = info.get('pegRatio', 0) or 0
            roe = (info.get('returnOnEquity', 0) or 0) * 100
            debt = (info.get('debtToEquity', 0) or 0) / 100
            sector = info.get('sector', '').lower()
            pledged = info.get('pledgedPercent', 0) or 0
            
            # Health Score & Sentiment
            ma200 = hist['Close'].rolling(200).mean().iloc[-1]
            sentiment = "Bullish" if curr_price > ma200 else "Bearish"
            val_status = "Undervalued" if pe < 20 else "Overvalued"
            
            score = 0
            if pe < 25: score += 20
            if roe > 15: score += 20
            if debt < 1: score += 20
            if pledged < 10: score += 20
            if sentiment == "Bullish": score += 20

            # 2. HEADER GRID
            st.subheader(f"💎 {info.get('longName', ticker)}")
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f'<div class="metric-card"><small>Price</small><br><span style="color:#00ffcc; font-size:22px">₹{curr_price:,.2f}</span></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="metric-card"><small>Health Score</small><br><span style="color:#00ffcc; font-size:22px">{score}/100</span></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="metric-card"><small>Valuation</small><br><span style="font-size:22px">{val_status}</span></div>', unsafe_allow_html=True)
            c4.markdown(f'<div class="metric-card"><small>Sentiment</small><br><span style="font-size:22px">{sentiment}</span></div>', unsafe_allow_html=True)

            # 3. GROWTH TABLE
            st.write("### 📊 Financial Growth")
            fin = stock.financials.T
            if not fin.empty:
                growth_data = pd.DataFrame({
                    "Year": fin.index.year,
                    "Net Profit (Cr)": (fin['Net Income'] / 1e7).round(2),
                    "Growth %": fin['Net Income'].pct_change().fillna(0).apply(lambda x: f"{x*100:+.1f}%")
                }).reset_index(drop=True)
                st.table(growth_data)

            # 4. SIGNAL AUDIT (Color Logic)
            st.write("### 🔍 Vital Signals")
            s1, s2, s3, s4 = st.columns(4)
            
            # Debt Logic
            is_infra = any(x in sector for x in ['bank', 'infra', 'construction', 'finance'])
            if is_infra:
                d_color = "#00ffcc" if debt <= 3 else ("#ffcc00" if debt <= 5 else "#ff4b4b")
            else:
                d_color = "#00ffcc" if debt <= 1 else "#ff4b4b"
            
            # P/E & PEG & ROE
            roe_color = "#00ffcc" if roe >= 15 else "#ff4b4b"
            pe_color = "#00ffcc" if pe <= 25 else "#ff4b4b"
            peg_color = "#00ffcc" if 0.8 <= peg <= 1.2 else "#ff4b4b"

            s1.markdown(f'<div class="metric-card"><small>Debt-to-Equity</small><br><span style="color:{d_color}; font-size:20px">{debt:.2f}</span></div>', unsafe_allow_html=True)
            s2.markdown(f'<div class="metric-card"><small>ROE</small><br><span style="color:{roe_color}; font-size:20px">{roe:.1f}%</span></div>', unsafe_allow_html=True)
            s3.markdown(f'<div class="metric-card"><small>P/E Ratio</small><br><span style="color:{pe_color}; font-size:20px">{pe:.1f}</span></div>', unsafe_allow_html=True)
            s4.markdown(f'<div class="metric-card"><small>PEG Ratio</small><br><span style="color:{peg_color}; font-size:20px">{peg:.2f}</span></div>', unsafe_allow_html=True)

            # 5. PROMOTER & TREND
            st.divider()
            t1, t2, t3 = st.columns(3)
            p_color = "#00ffcc" if pledged < 10 else "#ff4b4b"
            t1.markdown(f'<div class="metric-card"><small>Promoter Pledged</small><br><span style="color:{p_color}; font-size:20px">{pledged:.1f}%</span></div>', unsafe_allow_html=True)
            t2.markdown(f'<div class="metric-card"><small>Industry: {info.get("industry","N/A")}</small><br><span style="color:#00ffcc; font-size:20px">Growing</span></div>', unsafe_allow_html=True)
            
            verdict = "BUY" if score >= 70 else "WAIT"
            v_color = "#00ffcc" if verdict == "BUY" else "#ffcc00"
            t3.markdown(f'<div class="status-box" style="background:{v_color}; color:#0d1117">DECISION: {verdict}</div>', unsafe_allow_html=True)

            # 6. PRICE ACTION CHART
            st.write("### 📈 3-Year Price Action")
            fig = go.Figure(data=[go.Scatter(x=hist.index, y=hist['Close'], line=dict(color='#00ffcc', width=2))])
            fig.update_layout(template="plotly_dark", height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

# --- OTHER TABS (As previously designed) ---
elif selected == "Top 10 Picks":
    b, s = st.columns(2)
    with b:
        st.subheader("🏆 Strong Buy")
        for sym in ["RELIANCE", "HDFCBANK", "L&T", "BHARTIARTL", "TCS"]:
            st.markdown(f'<div style="background:#1c2128; border-left:5px solid #00ffcc; padding:10px; margin-bottom:5px">{sym}.NS</div>', unsafe_allow_html=True)
    with s:
        st.subheader("⚠️ Strong Sell")
        for sym in ["IDEA", "PAYTM", "YESBANK", "RPOWER", "NYKAA"]:
            st.markdown(f'<div style="background:#1c2128; border-left:5px solid #ff4b4b; padding:10px; margin-bottom:5px">{sym}.NS</div>', unsafe_allow_html=True)

elif selected == "Market News":
    st.subheader("📰 Market Intelligence")
    for n in yf.Ticker("^NSEI").news[:10]:
        st.markdown(f"**{n['title']}**\n\nSource: {n['publisher']} | [Read Story]({n['link']})")
        st.divider()
