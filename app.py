import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

# --- UI CONFIGURATION ---
st.set_page_config(page_title="QUANTUM NSE | AI Terminal", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS (Visibility & Branding) ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #ffffff; }
    .brand-container { text-align: center; padding: 25px 0; background: #161b22; border-radius: 0 0 30px 30px; border-bottom: 1px solid #30363d; margin-bottom: 20px; }
    .logo-text { font-size: 42px; font-weight: 800; color: #00ffcc; margin: 0; }
    div[data-testid="stTable"] td, div[data-testid="stTable"] th { color: #ffffff !important; font-size: 16px !important; border-bottom: 1px solid #30363d !important; }
    .stat-box { background: #1c2128; border: 1px solid #30363d; border-radius: 12px; padding: 15px; margin-bottom: 10px; }
    .metric-label { font-size: 12px; color: #8b949e; text-transform: uppercase; }
    .metric-value { font-size: 22px; font-weight: bold; margin-top: 5px; }
    .pick-card { background: #1c2128; border-left: 5px solid #00ffcc; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
    .sell-card { background: #1c2128; border-left: 5px solid #ff4b4b; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- ENGINE FUNCTIONS ---
def get_index_data(indices):
    data = {}
    for name, sym in indices.items():
        ticker = yf.Ticker(sym)
        hist = ticker.history(period="2d")
        if len(hist) > 1:
            price = hist['Close'].iloc[-1]
            change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
            data[name] = {"price": price, "change": change, "sym": sym}
    return data

# --- BRANDING ---
st.markdown('<div class="brand-container"><div class="logo-text">⚡ QUANTUM NSE PRO</div></div>', unsafe_allow_html=True)

# --- ALL INDICES DASHBOARD ---
major_indices = {
    "NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "FIN NIFTY": "NIFTY_FIN_SERVICE.NS",
    "NIFTY IT": "^CNXIT", "NIFTY AUTO": "^CNXAUTO", "NIFTY PHARMA": "^CNXPHARMA"
}

idx_results = get_index_data(major_indices)
cols = st.columns(len(idx_results))
for i, (name, d) in enumerate(idx_results.items()):
    col_color = "#00ffcc" if d['change'] >= 0 else "#ff4b4b"
    with cols[i]:
        if st.button(f"{name}\n{d['price']:,.1f}", key=name):
            st.session_state.active_index = d['sym']
            st.session_state.active_name = name

# Show Technical Chart for Index if selected
if "active_index" in st.session_state:
    st.subheader(f"📈 {st.session_state.active_name} Technical Chart")
    idx_hist = yf.Ticker(st.session_state.active_index).history(period="1y")
    fig = go.Figure(data=[go.Candlestick(x=idx_hist.index, open=idx_hist['Open'], high=idx_hist['High'], low=idx_hist['Low'], close=idx_hist['Close'])])
    fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

# --- NAVIGATION ---
menu = option_menu(None, ["Stock Search", "Top 10 Picks/Sells"], icons=["search", "list-check"], orientation="horizontal")

if menu == "Stock Search":
    search = st.text_input("", placeholder="Enter Ticker (e.g., RELIANCE)...").upper()
    if search:
        t_sym = f"{search}.NS"
        stock = yf.Ticker(t_sym)
        info = stock.info
        
        # 1. CORE STATS GRID
        c1, c2, c3, c4 = st.columns(4)
        pe = info.get('trailingPE', 0)
        peg = info.get('pegRatio', 0)
        roe = info.get('returnOnEquity', 0) * 100
        debt = info.get('debtToEquity', 0) / 100
        
        with c1:
            st.markdown(f'<div class="stat-box"><p class="metric-label">Price</p><p class="metric-value">₹{info.get("currentPrice", 0):,.2f}</p></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="stat-box"><p class="metric-label">P/E Ratio</p><p class="metric-value" style="color:{"#00ffcc" if pe < 30 else "#ff4b4b"}">{pe:.2f}</p></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="stat-box"><p class="metric-label">PEG Ratio</p><p class="metric-value" style="color:{"#00ffcc" if 0.8<peg<1.2 else "#ff4b4b"}">{peg:.2f}</p></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="stat-box"><p class="metric-label">Debt/Equity</p><p class="metric-value" style="color:{"#00ffcc" if debt<1 else "#ff4b4b"}">{debt:.2f}</p></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="stat-box"><p class="metric-label">ROE</p><p class="metric-value" style="color:{"#00ffcc" if roe>15 else "#ff4b4b"}">{roe:.1f}%</p></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="stat-box"><p class="metric-label">Pledged %</p><p class="metric-value">{info.get("pledgedHoldingPercent", 0):.1f}%</p></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="stat-box"><p class="metric-label">Health Score</p><p class="metric-value" style="color:#00ffcc">{"Strong" if roe > 15 and debt < 1 else "Average"}</p></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="stat-box"><p class="metric-label">Sentiment</p><p class="metric-value">BULLISH</p></div>', unsafe_allow_html=True)

        # 2. FINANCIALS (Visible Table)
        st.subheader("📊 Financial Growth Audit (YoY)")
        fin = stock.financials.T
        if not fin.empty:
            growth_df = pd.DataFrame({
                "Year": fin.index.year,
                "Net Profit (Cr)": (fin['Net Income'] / 1e7).round(2),
                "Revenue (Cr)": (fin['Total Revenue'] / 1e7).round(2)
            }).reset_index(drop=True)
            st.table(growth_df)

        # 3. 3-YEAR CHART
        st.subheader("📈 3-Year Price Action")
        h3y = stock.history(period="3y")
        fig3 = go.Figure(data=[go.Scatter(x=h3y.index, y=h3y['Close'], line=dict(color='#00ffcc'))])
        fig3.update_layout(template="plotly_dark", height=400)
        st.plotly_chart(fig3, use_container_width=True)

elif menu == "Top 10 Picks/Sells":
    buy_col, sell_col = st.columns(2)
    
    with buy_col:
        st.subheader("🟢 Top 10 Strong Buy")
        buys = [("RELIANCE", "Energy transition Alpha"), ("HDFCBANK", "Valuation bottoming"), ("LT", "Infra Orderbook peak"), ("TCS", "AI Margin expansion"), ("BHARTIARTL", "ARPU growth dominance"), ("ICICIBANK", "Best-in-class ROA"), ("M&M", "EV/SUV Market leader"), ("BAJFINANCE", "Digital lending scale"), ("HINDUNILVR", "Consumption recovery"), ("TITAN", "Luxury demand resilient")]
        for s, r in buys:
            st.markdown(f'<div class="pick-card"><b>{s}</b>: {r}</div>', unsafe_allow_html=True)
            
    with sell_col:
        st.subheader("🔴 Top 10 Strong Sell")
        sells = [("PAYTM", "Regulatory headwinds"), ("WIPRO", "Revenue growth laggard"), ("VEDL", "High debt concerns"), ("ZEEL", "Merger uncertainty"), ("UPL", "Global agro-chemical slowdown"), ("PAGEIND", "High valuation/Low growth"), ("NYKAA", "Margin compression"), ("DELHIVERY", "Path to profitability slow"), ("ADANIENT", "High leverage levels"), ("NMDC", "Global iron ore volatility")]
        for s, r in sells:
            st.markdown(f'<div class="sell-card"><b>{s}</b>: {r}</div>', unsafe_allow_html=True)
