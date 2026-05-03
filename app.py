import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import pandas_ta as ta

# --- UI CONFIGURATION ---
st.set_page_config(page_title="QUANTUM NSE | AI Terminal", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS (High Contrast & Professional Branding) ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #ffffff; }
    .brand-container { text-align: center; padding: 25px 0; background: #161b22; border-radius: 0 0 30px 30px; border-bottom: 1px solid #30363d; margin-bottom: 20px; }
    .logo-text { font-size: 42px; font-weight: 800; color: #00ffcc; margin: 0; }
    .tagline { color: #8b949e; font-size: 14px; }
    
    /* Table Visibility Fix */
    div[data-testid="stTable"] td, div[data-testid="stTable"] th { 
        color: #ffffff !important; font-weight: 600 !important; font-size: 16px !important; border-bottom: 1px solid #30363d !important; 
    }
    
    /* Analysis Cards */
    .stat-box { background: #1c2128; border: 1px solid #30363d; border-radius: 12px; padding: 15px; margin-bottom: 10px; min-height: 100px; }
    .metric-label { font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { font-size: 20px; font-weight: bold; margin-top: 5px; }
    
    /* Picks & Sells */
    .pick-card { background: #1c2128; border-left: 5px solid #00ffcc; padding: 15px; margin-bottom: 12px; border-radius: 5px; }
    .sell-card { background: #1c2128; border-left: 5px solid #ff4b4b; padding: 15px; margin-bottom: 12px; border-radius: 5px; }
    
    /* Signal Banner */
    .signal-banner { padding: 15px; border-radius: 10px; text-align: center; font-weight: bold; font-size: 22px; margin-bottom: 20px; border: 1px solid; }
    </style>
    """, unsafe_allow_html=True)

# --- CORE ENGINE FUNCTIONS ---
def fix_df(df):
    if isinstance(df.columns, pd.MultiIndex): 
        df.columns = df.columns.get_level_values(0)
    return df

@st.cache_data(ttl=300)
def get_index_snapshot(indices):
    data = {}
    for name, sym in indices.items():
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="2d")
            if len(hist) > 1:
                price = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                change = ((price - prev) / prev) * 100
                data[name] = {"price": price, "change": change, "sym": sym}
        except: continue
    return data

def get_debt_status(ratio, sector):
    sector = str(sector).lower()
    is_special = any(x in sector for x in ['bank', 'financial', 'infrastructure', 'construction'])
    if is_special:
        if ratio <= 3: return "#00ffcc", "HEALTHY (S)"
        elif ratio <= 5: return "#ffcc00", "MODERATE (S)"
        return "#ff4b4b", "HIGH RISK"
    else:
        if ratio <= 1: return "#00ffcc", "HEALTHY"
        return "#ff4b4b", "HIGH DEBT"

# --- BRANDING & TOP NAVIGATION ---
st.markdown('<div class="brand-container"><div class="logo-text">⚡ QUANTUM NSE PRO</div><div class="tagline">360° Fundamental & Technical Intelligence</div></div>', unsafe_allow_html=True)

# --- INDICES DASHBOARD ---
major_indices = {
    "NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "FIN NIFTY": "NIFTY_FIN_SERVICE.NS",
    "NIFTY IT": "^CNXIT", "NIFTY AUTO": "^CNXAUTO", "NIFTY PHARMA": "^CNXPHARMA"
}

idx_results = get_index_snapshot(major_indices)

if idx_results:
    cols = st.columns(len(idx_results))
    for i, (name, d) in enumerate(idx_results.items()):
        col_color = "#00ffcc" if d['change'] >= 0 else "#ff4b4b"
        with cols[i]:
            st.markdown(f"<p style='color:{col_color}; margin-bottom:-10px; font-size:12px; font-weight:bold; text-align:center;'>{d['change']:+.2f}%</p>", unsafe_allow_html=True)
            if st.button(f"{name}\n{d['price']:,.1f}", key=name):
                st.session_state.active_index = d['sym']
                st.session_state.active_name = name
else:
    st.error("Market data connection failed. Check your internet or API limits.")

# Show Technical Chart for Index if selected
if "active_index" in st.session_state:
    st.write("---")
    st.subheader(f"📈 {st.session_state.active_name} 1-Year Performance")
    idx_hist = yf.Ticker(st.session_state.active_index).history(period="1y")
    fig = go.Figure(data=[go.Candlestick(x=idx_hist.index, open=idx_hist['Open'], high=idx_hist['High'], low=idx_hist['Low'], close=idx_hist['Close'])])
    fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

# --- MAIN MENU ---
menu = option_menu(None, ["Stock Analysis", "Top 10 Picks/Sells", "Market News"], 
    icons=["search", "list-check", "newspaper"], orientation="horizontal",
    styles={"nav-link-selected": {"background-color": "#00ffcc", "color": "#0d1117"}})

if menu == "Stock Analysis":
    search = st.text_input("", placeholder="Enter NSE Ticker (e.g., RELIANCE, SBIN, LT)...").upper()
    
    if search:
        t_sym = f"{search}.NS"
        stock = yf.Ticker(t_sym)
        info = stock.info
        
        if 'currentPrice' in info or 'regularMarketPrice' in info:
            with st.spinner("Executing Intelligence Audit..."):
                # Fundamental Metrics
                pe = info.get('trailingPE', 0)
                peg = info.get('pegRatio', 0)
                roe = info.get('returnOnEquity', 0) * 100
                debt = info.get('debtToEquity', 0) / 100
                pledge = info.get('pledgedHoldingPercent', 0)
                price = info.get('currentPrice', 0)
                sector = info.get('sector', 'General')
                
                # Signal Logic
                health_score = 0
                if roe > 15: health_score += 25
                if debt < 1: health_score += 25
                if peg < 1.2: health_score += 25
                if pledge < 5: health_score += 25
                
                signal = "STRONG BUY" if health_score >= 75 else "BUY / ACCUMULATE" if health_score >= 50 else "WAIT / AVOID"
                sig_col = "#00ffcc" if health_score >= 75 else "#ffcc00" if health_score >= 50 else "#ff4b4b"
                
                st.markdown(f'<div class="signal-banner" style="background:{sig_col}22; border-color:{sig_col}; color:{sig_col};">ANALYSIS: {signal} | Health Score: {health_score}/100</div>', unsafe_allow_html=True)

                # 1. PARAMETERS GRID
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.markdown(f'<div class="stat-box"><p class="metric-label">Current Price</p><p class="metric-value">₹{price:,.2f}</p></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="stat-box"><p class="metric-label">P/E Ratio</p><p class="metric-value" style="color:{"#00ffcc" if pe < 30 else "#ff4b4b"}">{pe:.2f}</p></div>', unsafe_allow_html=True)
                with c2:
                    st.markdown(f'<div class="stat-box"><p class="metric-label">PEG Ratio</p><p class="metric-value" style="color:{"#00ffcc" if 0.8<peg<1.2 else "#ff4b4b"}">{peg:.2f}</p></div>', unsafe_allow_html=True)
                    d_col, d_lbl = get_debt_status(debt, sector)
                    st.markdown(f'<div class="stat-box"><p class="metric-label">Debt/Equity</p><p class="metric-value" style="color:{d_col}">{debt:.2f}</p><small>{d_lbl}</small></div>', unsafe_allow_html=True)
                with c3:
                    st.markdown(f'<div class="stat-box"><p class="metric-label">Return on Equity</p><p class="metric-value" style="color:{"#00ffcc" if roe>15 else "#ff4b4b"}">{roe:.1f}%</p></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="stat-box"><p class="metric-label">Promoter Pledged</p><p class="metric-value" style="color:{"#00ffcc" if pledge<10 else "#ff4b4b"}">{pledge:.1f}%</p></div>', unsafe_allow_html=True)
                with c4:
                    st.markdown(f'<div class="stat-box"><p class="metric-label">Industry</p><p class="metric-value">{sector}</p></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="stat-box"><p class="metric-label">Valuation</p><p class="metric-value" style="color:{"#00ffcc" if peg<1 else "#ff4b4b"}">{"UNDERVALUED" if peg<1 else "OVERVALUED"}</p></div>', unsafe_allow_html=True)

                # 2. FINANCIAL AUDIT (High Visibility)
                st.subheader("📊 Financial Growth Audit (Year-on-Year)")
                fin = stock.financials.T
                if not fin.empty:
                    growth_df = pd.DataFrame({
                        "Year": fin.index.year,
                        "Net Profit (Cr)": (fin['Net Income'] / 1e7).round(2),
                        "Revenue (Cr)": (fin['Total Revenue'] / 1e7).round(2)
                    }).reset_index(drop=True)
                    st.table(growth_df)

                # 3. 3-YEAR PRICE ACTION
                st.subheader("📈 3-Year Price Action")
                h3y = stock.history(period="3y")
                fig3 = go.Figure(data=[go.Scatter(x=h3y.index, y=h3y['Close'], line=dict(color='#00ffcc', width=2))])
                fig3.update_layout(template="plotly_dark", height=450, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig3, use_container_width=True)
        else:
            st.error("Ticker not found. Please check the NSE symbol.")

elif menu == "Top 10 Picks/Sells":
    st.subheader("🚀 May 2026 High-Conviction Dashboard")
    buy_col, sell_col = st.columns(2)
    
    with buy_col:
        st.markdown("### 🟢 Top 10 Strong Buy")
        buys = [
            ("RELIANCE", "Green Energy transition & Retail ecosystem growth."),
            ("HDFCBANK", "Deep value post-merger with stabilizing NIMs."),
            ("L&T", "Record order book fueled by National Infra Pipeline."),
            ("BHARTIARTL", "Dominant ARPU growth and 5G market leadership."),
            ("TCS", "Unmatched EBIT margins and AI service deal pipeline."),
            ("ICICIBANK", "Best-in-class risk management and digital ROA."),
            ("M&M", "Strong SUV demand and leadership in Tractor segment."),
            ("BAJFINANCE", "Massive customer data advantage in consumer credit."),
            ("HINDUNILVR", "Defensive king with rural consumption recovery play."),
            ("TITAN", "Resilient luxury demand and jewellery market share gain.")
        ]
        for s, r in buys:
            st.markdown(f'<div class="pick-card"><b>{s}</b>: {r}</div>', unsafe_allow_html=True)
            
    with sell_col:
        st.markdown("### 🔴 Top 10 Strong Sell")
        sells = [
            ("PAYTM", "Persistent regulatory scrutiny and path to profit risks."),
            ("WIPRO", "Consistent underperformance vs. IT peers in revenue."),
            ("VEDL", "High debt-to-equity and commodity price volatility."),
            ("ZEEL", "Uncertainty in merger timelines and ad-revenue dip."),
            ("UPL", "Heavy leverage in a slowing global agrochemical cycle."),
            ("PAGEIND", "Extreme valuation facing premium clothing slowdown."),
            ("NYKAA", "Intense competition compressing beauty-segment margins."),
            ("DELHIVERY", "Logistics cost pressures and slow unit economics."),
            ("ADANIENT", "Stretched valuations relative to cash flow ratios."),
            ("NMDC", "Global iron ore price correction and cooling demand.")
        ]
        for s, r in sells:
            st.markdown(f'<div class="sell-card"><b>{s}</b>: {r}</div>', unsafe_allow_html=True)

elif menu == "Market News":
    st.subheader("📰 NSE Market Moving Headlines")
    try:
        from GoogleNews import GoogleNews
        gn = GoogleNews(period='2d', lang='en', region='IN')
        gn.search('NSE India Stock Market')
        for item in gn.result()[:10]:
            st.info(f"**{item.get('title')}**")
            st.caption(f"{item.get('media')} | {item.get('date')}")
    except:
        st.write("Live news feed is momentarily unavailable.")
