import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import requests

# --- CONFIGURATION & API KEY ---
EOD_API_KEY = "69f6f6918a0d60.33244408"
BASE_URL = "https://eodhd.com/api"

# --- UI CONFIGURATION ---
st.set_page_config(page_title="QUANTUM NSE | EODHD AI", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #ffffff; }
    .brand-container { text-align: center; padding: 20px 0; background: #161b22; border-radius: 0 0 30px 30px; border-bottom: 1px solid #30363d; margin-bottom: 20px; }
    .logo-text { font-size: 38px; font-weight: 800; color: #00ffcc; margin: 0; }
    .stat-box { background: #1c2128; border: 1px solid #30363d; border-radius: 12px; padding: 15px; margin-bottom: 10px; }
    .metric-label { font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { font-size: 20px; font-weight: bold; margin-top: 5px; color: #ffffff; }
    div[data-testid="stTable"] td, div[data-testid="stTable"] th { 
        color: #ffffff !important; font-size: 15px !important; border-bottom: 1px solid #30363d !important; 
    }
    .pick-card { background: #1c2128; border-left: 5px solid #00ffcc; padding: 12px; margin-bottom: 10px; border-radius: 5px; }
    .sell-card { background: #1c2128; border-left: 5px solid #ff4b4b; padding: 12px; margin-bottom: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE ---
@st.cache_data(ttl=600)
def get_eod_indices():
    # EODHD Indices symbols for India
    indices = {"NIFTY 50": "NSEI.INDX", "SENSEX": "BSESN.INDX"}
    results = {}
    for name, sym in indices.items():
        url = f"{BASE_URL}/real-time/{sym}?api_token={EOD_API_KEY}&fmt=json"
        try:
            r = requests.get(url).json()
            results[name] = {"price": r['close'], "change": r['change_p'], "sym": sym}
        except: continue
    return results

@st.cache_data(ttl=3600)
def get_stock_data(ticker):
    # EODHD uses .NSE for National Stock Exchange
    sym = f"{ticker}.NSE"
    hist_url = f"{BASE_URL}/eod/{sym}?api_token={EOD_API_KEY}&fmt=json&period=d&from=2023-01-01"
    fund_url = f"{BASE_URL}/fundamentals/{sym}?api_token={EOD_API_KEY}"
    
    try:
        # Fetch Price History
        h_data = requests.get(hist_url).json()
        df = pd.DataFrame(h_data)
        df['date'] = pd.to_datetime(df['date'])
        
        # Fetch Fundamentals
        f_data = requests.get(fund_url).json()
        
        return df, f_data, None
    except Exception as e:
        return None, None, str(e)

# --- BRANDING ---
st.markdown('<div class="brand-container"><div class="logo-text">⚡ QUANTUM NSE PRO</div><div style="color:#8b949e">Powered by EODHD Institutional Data</div></div>', unsafe_allow_html=True)

# --- INDICES BAR ---
idx_data = get_eod_indices()
if idx_data:
    cols = st.columns(len(idx_data))
    for i, (name, d) in enumerate(idx_data.items()):
        col_color = "#00ffcc" if d['change'] >= 0 else "#ff4b4b"
        with cols[i]:
            st.markdown(f"<div style='text-align:center;'><small style='color:#8b949e'>{name}</small><br><b style='font-size:18px;'>{d['price']:,.2f}</b> <span style='color:{col_color}; font-size:12px;'>({d['change']:+.2f}%)</span></div>", unsafe_allow_html=True)
            if st.button(f"Analyze {name}", key=name):
                st.session_state.active_idx_sym = d['sym']

# --- NAVIGATION ---
menu = option_menu(None, ["Deep Analysis", "Top 10 Picks/Sells"], 
                   icons=["search", "list-check"], orientation="horizontal",
                   styles={"nav-link-selected": {"background-color": "#00ffcc", "color": "#0d1117"}})

if menu == "Deep Analysis":
    search = st.text_input("", placeholder="Enter Ticker (e.g. RELIANCE, TCS, HDFCBANK)...").upper()
    
    if search:
        df, funds, error = get_stock_data(search)
        
        if error:
            st.error(f"EODHD Connection Error: {error}")
        else:
            # 1. KEY FUNDAMENTAL GRID
            highlights = funds.get('Highlights', {})
            valuation = funds.get('Valuation', {})
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f'<div class="stat-box"><p class="metric-label">Price</p><p class="metric-value">₹{df["close"].iloc[-1]:,.2f}</p></div>', unsafe_allow_html=True)
            with c2:
                pe = highlights.get('PERatio', 0)
                st.markdown(f'<div class="stat-box"><p class="metric-label">P/E Ratio</p><p class="metric-value" style="color:{"#00ffcc" if pe and pe < 35 else "#ff4b4b"}">{pe if pe else "N/A"}</p></div>', unsafe_allow_html=True)
            with c3:
                roe = highlights.get('ReturnOnEquityTTM', 0) * 100
                st.markdown(f'<div class="stat-box"><p class="metric-label">ROE %</p><p class="metric-value" style="color:{"#00ffcc" if roe > 15 else "#ff4b4b"}">{roe:.2f}%</p></div>', unsafe_allow_html=True)
            with c4:
                div = highlights.get('DividendYield', 0) * 100
                st.markdown(f'<div class="stat-box"><p class="metric-label">Div. Yield</p><p class="metric-value">{div:.2f}%</p></div>', unsafe_allow_html=True)

            # 2. FINANCIAL GROWTH AUDIT
            st.subheader("📊 Financial Growth Audit (Yearly)")
            # Pulling from Income Statement
            inc_stmt = funds.get('Financials', {}).get('Income_Statement', {}).get('yearly', {})
            if inc_stmt:
                rows = []
                # Get last 4 years
                for date, val in list(inc_stmt.items())[:4]:
                    rows.append({
                        "Year": date[:4],
                        "Revenue (Cr)": round(float(val.get('totalRevenue', 0)) / 1e7, 2),
                        "Net Income (Cr)": round(float(val.get('netIncome', 0)) / 1e7, 2),
                        "EBITDA (Cr)": round(float(val.get('ebitda', 0)) / 1e7, 2)
                    })
                st.table(pd.DataFrame(rows))

            # 3. 3-YEAR TREND CHART
            st.subheader("📈 3-Year Technical Momentum")
            fig = go.Figure(data=[go.Scatter(x=df['date'], y=df['close'], line=dict(color='#00ffcc', width=2))])
            fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

elif menu == "Top 10 Picks/Sells":
    b, s = st.columns(2)
    with b:
        st.subheader("🟢 Top 10 Strong Buy (3Y Horizon)")
        buys = [("RELIANCE", "Energy pivot & Retail Dominance"), ("HDFCBANK", "Post-merger value play"), ("LT", "National Infra pipeline leader"), ("TCS", "AI Services & Free Cash Flow"), ("BHARTIARTL", "Telecom Oligopoly & ARPU"), ("ICICIBANK", "Superior Asset Quality"), ("M&M", "EV & Tractor Market Leadership"), ("BAJFINANCE", "Fintech scale & Data edge"), ("HINDUNILVR", "FMCG Stability"), ("TITAN", "Luxury & Jewellery growth")]
        for t, r in buys:
            st.markdown(f'<div class="pick-card"><b>{t}</b>: {r}</div>', unsafe_allow_html=True)
    with s:
        st.subheader("🔴 Top 10 Strong Sell (Risk Alert)")
        sells = [("PAYTM", "Regulatory/Path to Profitability"), ("WIPRO", "IT Sector Laggard"), ("VEDL", "Debt Service concerns"), ("ZEEL", "Merger fallout/Media churn"), ("UPL", "Agro-chem cycle downturn"), ("PAGEIND", "Valuation vs Slowing Growth"), ("NYKAA", "Margin Compression"), ("DELHIVERY", "Logistics cost structure"), ("ADANIENT", "Stretched Fundamental Ratios"), ("NMDC", "Global Metal Price Volatility")]
        for t, r in sells:
            st.markdown(f'<div class="sell-card"><b>{t}</b>: {r}</div>', unsafe_allow_html=True)
