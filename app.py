import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from GoogleNews import GoogleNews
import plotly.graph_objects as go
from datetime import datetime

# --- UI CONFIG & STYLING ---
st.set_page_config(page_title="NSE Pro Terminal", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for FinTech Look
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div.stButton > button:first-child {
        background-color: #00ffcc; color: #0e1117; border-radius: 10px; font-weight: bold; border: none; width: 100%;
    }
    .metric-card {
        background-color: #1e2227; border-radius: 15px; padding: 20px; border: 1px solid #30363d;
    }
    .status-green { color: #00ffcc; font-weight: bold; }
    .status-red { color: #ff4b4b; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. TOP NAVIGATION & MARKET WATCH ---
st.title("⚡ NSE Pro Terminal")

@st.cache_data(ttl=300)
def get_quick_stats():
    top_tickers = ["^NSEI", "^BSESN", "RELIANCE.NS", "HDFCBANK.NS"]
    data = yf.download(top_tickers, period="2d", interval="1m", progress=False)['Close']
    stats = []
    for t in top_tickers:
        curr, prev = data[t].iloc[-1], data[t].iloc[0]
        change = ((curr - prev) / prev) * 100
        stats.append({"name": t.replace(".NS", "").replace("^", ""), "price": curr, "change": change})
    return stats

# Header Metric Bar
m_cols = st.columns(4)
for i, stat in enumerate(get_quick_stats()):
    with m_cols[i]:
        st.markdown(f"""
        <div class="metric-card">
            <p style="color:#8b949e; margin-bottom:0;">{stat['name']}</p>
            <h3 style="margin:0;">₹{stat['price']:,.2f}</h3>
            <p style="margin:0; color:{'#00ffcc' if stat['change'] > 0 else '#ff4b4b'};">
                {'▲' if stat['change'] > 0 else '▼'} {abs(stat['change']):.2f}%
            </p>
        </div>
        """, unsafe_allow_html=True)

# --- 2. MAIN DASHBOARD ---
col_main, col_news = st.columns([2, 1])

with col_main:
    st.subheader("🔍 Deep Audit Terminal")
    t_col1, t_col2 = st.columns([3, 1])
    ticker_input = t_col1.text_input("Enter NSE Ticker", "RELIANCE", label_visibility="collapsed")
    run_audit = t_col2.button("RUN AUDIT")
    
    ticker_ns = f"{ticker_input.upper()}.NS" if not ticker_input.endswith(".NS") else ticker_input.upper()

    if run_audit:
        stock = yf.Ticker(ticker_ns)
        info = stock.info
        hist = stock.history(period="3y")

        if not hist.empty:
            # Interactive Plotly Chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name="Price", line=dict(color='#00ffcc', width=2)))
            fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_運用=True)

            # Audit Logic (Calculations)
            de = (info.get('debtToEquity', 0) / 100)
            roe = (info.get('returnOnEquity', 0) * 100)
            peg = info.get('pegRatio', 1)
            score = 0
            if de < 1.5: score += 3
            if roe > 15: score += 3
            if peg < 1.2: score += 2
            if info.get('revenueGrowth', 0) > 0.1: score += 2

            # FinTech Result Grid
            st.markdown("### Fundamental Scorecard")
            r_col1, r_col2, r_col3 = st.columns(3)
            
            with r_col1:
                st.markdown(f'<div class="metric-card"><h5>Health Score</h5><h2 style="color:#00ffcc;">{score}/10</h2></div>', unsafe_allow_html=True)
            with r_col2:
                st.markdown(f'<div class="metric-card"><h5>Valuation</h5><h2 style="color:#ffcc00;">{"FAIR" if 0.8<peg<1.2 else "CHEAP" if peg<0.8 else "EXPENSIVE"}</h2></div>', unsafe_allow_html=True)
            with r_col3:
                rec = "STRONG BUY" if score >= 8 else "HOLD" if score >= 5 else "SELL"
                st.markdown(f'<div class="metric-card"><h5>Signal</h5><h2 style="color:#00ffcc;">{rec}</h2></div>', unsafe_allow_html=True)

            # Simple Table for Ratios
            st.write("---")
            audit_table = pd.DataFrame({
                "Parameter": ["Debt to Equity", "ROE", "PE Ratio", "PEG Ratio", "Promoter Holding"],
                "Value": [f"{de:.2f}", f"{roe:.2f}%", info.get('trailingPE', 'N/A'), peg, f"{info.get('heldPercentInsiders', 0)*100:.2f}%"],
                "Status": ["✅ Safe" if de<1.5 else "⚠️ High", "✅ Strong" if roe>15 else "➖ Average", "N/A", "✅ Fair" if peg<1.2 else "❌ High", "✅ High" if info.get('heldPercentInsiders', 0)>0.4 else "➖ Low"]
            })
            st.table(audit_table)

with col_news:
    st.subheader("📰 Market Feed")
    gn = GoogleNews(period='7d', lang='en', region='IN')
    gn.search(f'{ticker_input} Stock News India')
    news = gn.result()[:5]
    
    for n in news:
        with st.container():
            st.markdown(f"""
            <div style="background-color:#1e2227; padding:15px; border-radius:10px; margin-bottom:10px; border-left: 5px solid #00ffcc;">
                <p style="font-size:12px; color:#8b949e; margin:0;">{n['media']} • {n['date']}</p>
                <a href="{n['link']}" style="text-decoration:none; color:white; font-weight:bold;">{n['title'][:70]}...</a>
            </div>
            """, unsafe_allow_html=True)
