import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

# --- UI CONFIGURATION ---
st.set_page_config(page_title="QUANTUM NSE | AI Terminal", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS (Visibility Upgrades) ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #ffffff; }
    .index-bar { background: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; margin-bottom: 20px; display: flex; justify-content: space-around; }
    .index-item { text-align: center; font-weight: bold; }
    .brand-container { text-align: center; padding: 25px 0; background: #161b22; border-radius: 0 0 30px 30px; margin-bottom: 20px; border-bottom: 1px solid #30363d; }
    .logo-text { font-size: 42px; font-weight: 800; color: #00ffcc; margin: 0; }
    /* Visibility fix for Tables */
    div[data-testid="stTable"] td, div[data-testid="stTable"] th {
        color: #ffffff !important; font-weight: 500 !important; font-size: 16px !important; border-bottom: 1px solid #30363d !important;
    }
    .stat-box { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; margin-bottom: 15px; }
    .pick-card { background: #1c2128; border-left: 5px solid #00ffcc; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- UTILITY FUNCTIONS ---
def get_index_data():
    indices = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "SENSEX": "^BSESN"}
    data = {}
    for name, sym in indices.items():
        try:
            ticker = yf.Ticker(sym)
            price = ticker.info.get('regularMarketPrice') or ticker.history(period="1d")['Close'].iloc[-1]
            change = ticker.info.get('regularMarketChangePercent') or 0.0
            data[name] = (price, change)
        except: data[name] = (0, 0)
    return data

# --- BRANDING & INDICES ---
st.markdown('<div class="brand-container"><div class="logo-text">⚡ QUANTUM NSE</div></div>', unsafe_allow_html=True)

idx_data = get_index_data()
cols = st.columns(len(idx_data))
for i, (name, val) in enumerate(idx_data.items()):
    color = "#00ffcc" if val[1] >= 0 else "#ff4b4b"
    cols[i].markdown(f"""
        <div class="index-item">
            <small style="color:#8b949e">{name}</small><br>
            <span style="font-size:20px">{val[0]:,.2f}</span>
            <span style="color:{color}; font-size:14px"> ({val[1]:.2f}%)</span>
        </div>
    """, unsafe_allow_html=True)

# --- NAVIGATION ---
selected = option_menu(None, ["Analysis", "Top 10 Picks", "News"], 
    icons=["search", "trophy", "newspaper"], orientation="horizontal",
    styles={"nav-link-selected": {"background-color": "#00ffcc", "color": "#0d1117"}})

if selected == "Analysis":
    search = st.text_input("", placeholder="Search Stock Ticker (e.g., RELIANCE)...").upper()
    if search:
        t_sym = f"{search}.NS"
        stock = yf.Ticker(t_sym)
        info = stock.info
        
        # Financial Growth Table (High Visibility)
        st.subheader("📊 Financial Growth Audit (Year-on-Year)")
        try:
            fin = stock.financials.T
            growth_df = pd.DataFrame({
                "Year": fin.index.year,
                "Net Profit (Cr)": (fin['Net Income'] / 1e7).round(2),
                "Revenue (Cr)": (fin['Total Revenue'] / 1e7).round(2)
            }).reset_index(drop=True)
            st.table(growth_df)
        except: st.warning("Financial data currently unavailable for this ticker.")

        # Price Action (3 Years)
        st.subheader("📈 3-Year Price Action")
        hist = stock.history(period="3y")
        fig = go.Figure(data=[go.Scatter(x=hist.index, y=hist['Close'], line=dict(color='#00ffcc'))])
        fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True)

elif selected == "Top 10 Picks":
    st.subheader("🏆 Top 10 Strong Buy Ratings (May 2026)")
    picks = [
        ("RELIANCE", "Diversified conglomerate; aggressive Green Energy pivot and Retail expansion."),
        ("HDFCBANK", "Gold standard in banking; stabilizing NIMs post-merger and massive branch network."),
        ("L&T", "Record order book; primary beneficiary of India's ₹111 Trillion National Infra Pipeline."),
        ("BHARTIARTL", "Consistently rising ARPU; leading the 5G monetization and digital services race."),
        ("TCS", "Deep AI integration and robust deal pipeline; unmatched EBIT margins in IT."),
        ("ICICIBANK", "Superior asset quality; ROE consistently hitting 17-18% with strong digital focus."),
        ("BAJFINANCE", "Massive customer base (100M+); market leader in unsecured and EMI financing."),
        ("M&M", "Dominant in SUV and EV segments; strong agricultural demand boosting tractor sales."),
        ("HINDUNILVR", "Defensive play; zero-debt balance sheet and products in 9/10 Indian households."),
        ("INFY", "High free cash flow and dividend yield; strong recovery in BFSI sector spending.")
    ]
    
    for symbol, reason in picks:
        st.markdown(f"""
            <div class="pick-card">
                <span style="font-size:18px; font-weight:bold; color:#00ffcc">{symbol}</span><br>
                <span style="color:#ffffff">{reason}</span>
            </div>
        """, unsafe_allow_html=True)
