import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from GoogleNews import GoogleNews
import plotly.graph_objects as go
from datetime import datetime

# --- UI CONFIG & STYLING ---
st.set_page_config(page_title="NSE Pro Terminal", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for FinTech Dark Mode & Glassmorphism
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div.stButton > button:first-child {
        background-color: #00ffcc; color: #0e1117; border-radius: 10px; 
        font-weight: bold; border: none; width: 100%; height: 45px;
    }
    .metric-card {
        background-color: #1e2227; border-radius: 15px; padding: 20px; 
        border: 1px solid #30363d; margin-bottom: 10px;
    }
    .news-card {
        background-color: #1e2227; padding: 15px; border-radius: 10px; 
        margin-bottom: 12px; border-left: 5px solid #00ffcc;
    }
    a { text-decoration: none !important; }
    </style>
    """, unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
@st.cache_data(ttl=300)
def get_quick_stats():
    # Top indices and heavyweights for the header
    tickers = ["^NSEI", "^BSESN", "RELIANCE.NS", "HDFCBANK.NS"]
    stats = []
    try:
        # Download data one by one to avoid Multi-Index column issues
        for t in tickers:
            ticker_obj = yf.Ticker(t)
            data = ticker_obj.history(period="2d")
            if len(data) >= 2:
                curr = data['Close'].iloc[-1]
                prev = data['Close'].iloc[-2]
                change = ((curr - prev) / prev) * 100
                name = t.replace(".NS", "").replace("^", "INDX ")
                stats.append({"name": name, "price": curr, "change": change})
    except:
        pass
    return stats

@st.cache_data(ttl=3600)
def get_safe_news(query):
    try:
        gn = GoogleNews(period='7d', lang='en', region='IN')
        gn.search(f'{query} Stock News India')
        results = gn.result()
        # Filter out broken results
        return [n for n in results if n.get('title') and n.get('link')]
    except:
        return []

# --- 1. HEADER METRIC BAR ---
st.title("⚡ NSE Pro Terminal")
m_cols = st.columns(4)
quick_stats = get_quick_stats()

for i, col in enumerate(m_cols):
    if i < len(quick_stats):
        stat = quick_stats[i]
        color = "#00ffcc" if stat['change'] > 0 else "#ff4b4b"
        icon = "▲" if stat['change'] > 0 else "▼"
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <p style="color:#8b949e; margin-bottom:0; font-size:14px;">{stat['name']}</p>
                <h3 style="margin:0;">₹{stat['price']:,.2f}</h3>
                <p style="margin:0; color:{color}; font-size:14px;">
                    {icon} {abs(stat['change']):.2f}%
                </p>
            </div>
            """, unsafe_allow_html=True)

# --- 2. MAIN DASHBOARD ---
col_main, col_news = st.columns([2, 1])

with col_main:
    st.subheader("🔍 Deep Audit Terminal")
    
    # Search Bar Row
    search_col, btn_col = st.columns([4, 1])
    with search_col:
        ticker_input = st.text_input("Search Ticker", value="RELIANCE", label_visibility="collapsed").upper()
    with btn_col:
        run_audit = st.button("ANALYZE")
    
    ticker_ns = f"{ticker_input}.NS" if not ticker_input.endswith(".NS") else ticker_input

    if run_audit:
        try:
            with st.spinner("Processing Terminal Data..."):
                stock = yf.Ticker(ticker_ns)
                info = stock.info
                hist = stock.history(period="2y") # 2 years for trend visualization

                if not hist.empty:
                    # Professional Interactive Chart
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=hist.index, y=hist['Close'], 
                        name="Price", line=dict(color='#00ffcc', width=2),
                        fill='tozeroy', fillcolor='rgba(0, 255, 204, 0.1)'
                    ))
                    fig.update_layout(
                        template="plotly_dark", height=350, 
                        margin=dict(l=0, r=0, t=20, b=0),
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#30363d")
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # --- CALCULATIONS & RULES ---
                    de = (info.get('debtToEquity', 0) / 100) if info.get('debtToEquity') else 0
                    roe = (info.get('returnOnEquity', 0) * 100)
                    peg = info.get('pegRatio', 1.0)
                    rev_growth = info.get('revenueGrowth', 0)
                    
                    # Sector Specific Rules
                    sector = info.get('sector', 'Other')
                    is_fin = any(x in sector.lower() for x in ['bank', 'finance', 'infra'])
                    de_status = "Safe" if (de < 3 if is_fin else de < 1) else "High"
                    
                    # Scoring Logic
                    score = 0
                    if de_status == "Safe": score += 3
                    if roe > 15: score += 3
                    if peg < 1.2: score += 2
                    if rev_growth > 0.1: score += 2

                    # --- RESULTS GRID ---
                    st.markdown("### Fundamental Scorecard")
                    res_cols = st.columns(3)
                    
                    with res_cols[0]:
                        st.markdown(f'<div class="metric-card"><p style="color:#8b949e;">Health Score</p><h2 style="color:#00ffcc; margin:0;">{score}/10</h2></div>', unsafe_allow_html=True)
                    with res_cols[1]:
                        val_label = "UNDERVALUED" if peg < 0.8 else ("FAIR" if peg < 1.3 else "EXPENSIVE")
                        st.markdown(f'<div class="metric-card"><p style="color:#8b949e;">Valuation</p><h2 style="color:#ffcc00; margin:0;">{val_label}</h2></div>', unsafe_allow_html=True)
                    with res_cols[2]:
                        rec = "STRONG BUY" if score >= 8 else ("HOLD" if score >= 5 else "AVOID")
                        st.markdown(f'<div class="metric-card"><p style="color:#8b949e;">Expert Signal</p><h2 style="color:#00ffcc; margin:0;">{rec}</h2></div>', unsafe_allow_html=True)

                    # Detailed Ratio Table
                    st.markdown("#### Audit Ratios")
                    audit_df = pd.DataFrame({
                        "Metric": ["Debt to Equity", "ROE (%)", "PEG Ratio", "Promoter Holding", "Revenue Growth"],
                        "Value": [f"{de:.2f}", f"{roe:.2f}%", f"{peg}", f"{info.get('heldPercentInsiders', 0)*100:.2f}%", f"{rev_growth*100:.2f}%"],
                        "Analysis": [de_status, "Strong" if roe > 15 else "Neutral", "Good" if peg < 1.2 else "High", "High" if info.get('heldPercentInsiders', 0) > 0.45 else "Average", "Positive" if rev_growth > 0 else "Negative"]
                    })
                    st.table(audit_df)
                else:
                    st.error("No historical data found. Please check the Ticker symbol.")
        except Exception as e:
            st.error(f"Audit Terminal Error: {e}")

with col_news:
    st.subheader("📰 Market Feed")
    news_items = get_safe_news(ticker_input)
    
    if not news_items:
        st.info("No recent news found for this ticker.")
    else:
        for n in news_items[:6]:
            # Safety check for title to prevent TypeError
            raw_title = n.get('title', 'News Update')
            clean_title = (raw_title[:75] + '...') if len(raw_title) > 75 else raw_title
            
            st.markdown(f"""
            <div class="news-card">
                <p style="font-size:11px; color:#8b949e; margin:0;">{n.get('media', 'Finance')} • {n.get('date', 'Recent')}</p>
                <a href="{n.get('link', '#')}" target="_blank">
                    <p style="color:white; font-weight:bold; margin:5px 0 0 0; font-size:14px;">{clean_title}</p>
                </a>
            </div>
            """, unsafe_allow_html=True)
