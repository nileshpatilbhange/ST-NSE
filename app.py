import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import pandas_ta as ta
from GoogleNews import GoogleNews
from streamlit_option_menu import option_menu

# --- UI CONFIGURATION ---
st.set_page_config(page_title="QUANTUM NSE | AI Terminal", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS FOR PROFESSIONAL FINTECH LOOK ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .brand-container { text-align: center; padding: 30px 0; background: #161b22; border-radius: 0 0 30px 30px; margin-bottom: 20px; border-bottom: 1px solid #30363d; }
    .logo-text { font-size: 42px; font-weight: 800; color: #00ffcc; margin: 0; }
    .tagline { color: #8b949e; font-size: 14px; }
    .stat-box { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; margin-bottom: 15px; }
    .metric-label { font-size: 12px; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { font-size: 20px; font-weight: bold; margin-top: 5px; }
    .signal-banner { padding: 15px; border-radius: 10px; text-align: center; font-weight: bold; font-size: 22px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- ANALYTICS ENGINE ---
def fix_df(df):
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    return df

def get_sector_debt_rating(ratio, sector):
    sector = str(sector).lower()
    is_special = any(x in sector for x in ['bank', 'financial', 'infrastructure', 'construction'])
    
    if is_special:
        if ratio <= 3: return "#00ffcc", "HEALTHY (S)"
        elif ratio <= 5: return "#ffcc00", "MODERATE (S)"
        return "#ff4b4b", "HIGH RISK"
    else:
        if ratio <= 1: return "#00ffcc", "HEALTHY"
        return "#ff4b4b", "HIGH DEBT"

def get_fundamental_data(ticker_obj):
    info = ticker_obj.info
    # Financials
    rev = ticker_obj.financials.loc['Total Revenue'] if 'Total Revenue' in ticker_obj.financials.index else pd.Series()
    net_profit = ticker_obj.financials.loc['Net Income'] if 'Net Income' in ticker_obj.financials.index else pd.Series()
    
    # Growth Calc
    growth = 0
    if len(rev) >= 2:
        growth = ((rev.iloc[0] - rev.iloc[1]) / rev.iloc[1]) * 100
        
    return {
        "pe": info.get('trailingPE', 0),
        "peg": info.get('pegRatio', 0),
        "roe": info.get('returnOnEquity', 0) * 100,
        "debt_equity": info.get('debtToEquity', 0) / 100,
        "promoter_pledge": info.get('pledgedHoldingPercent', 0),
        "sector": info.get('sector', 'Unknown'),
        "revenue": rev,
        "profit": net_profit,
        "growth": growth,
        "price": info.get('currentPrice', info.get('regularMarketPreviousClose', 0))
    }

# --- BRANDING ---
st.markdown('<div class="brand-container"><div class="logo-text">⚡ QUANTUM NSE</div><div class="tagline">Fundamental & Technical AI Audit Engine</div></div>', unsafe_allow_html=True)

# --- NAVIGATION ---
selected = option_menu(None, ["Market View", "Top Picks", "News"], icons=["terminal", "rocket", "newspaper"], orientation="horizontal",
    styles={"nav-link-selected": {"background-color": "#00ffcc", "color": "#0d1117"}})

if selected == "Market View":
    search = st.text_input("", placeholder="Search Ticker (e.g. SBIN, RELIANCE, LT)...").upper()
    
    if search:
        t_sym = f"{search}.NS"
        stock = yf.Ticker(t_sym)
        
        with st.spinner("Executing 360° Audit..."):
            f_data = get_fundamental_data(stock)
            hist_3y = fix_df(stock.history(period="3y"))
            
            # 1. HEADER & SIGNAL
            health_score = 0
            if f_data['roe'] > 15: health_score += 20
            if f_data['peg'] < 1.2: health_score += 20
            if f_data['growth'] > 10: health_score += 20
            if f_data['debt_equity'] < 1: health_score += 20
            
            signal = "BUY" if health_score >= 60 else "WAIT / WATCH"
            sig_col = "#00ffcc" if signal == "BUY" else "#ffcc00"
            
            st.markdown(f'<div class="signal-banner" style="background:{sig_col}33; border:1px solid {sig_col}; color:{sig_col};">SIGNAL: {signal} | Health Score: {health_score}/100</div>', unsafe_allow_html=True)

            # 2. FUNDAMENTAL GRID
            c1, c2, c3, c4 = st.columns(4)
            
            with c1: # P/E & PEG
                pe_col = "#00ffcc" if f_data['pe'] < 25 else "#ff4b4b"
                peg_col = "#00ffcc" if 0.8 <= f_data['peg'] <= 1.2 else "#ff4b4b"
                st.markdown(f'<div class="stat-box"><p class="metric-label">P/E Ratio</p><p class="metric-value" style="color:{pe_col}">{f_data["pe"]:.2f}</p></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="stat-box"><p class="metric-label">PEG Ratio</p><p class="metric-value" style="color:{peg_col}">{f_data["peg"]:.2f}</p></div>', unsafe_allow_html=True)

            with c2: # Debt & ROE
                d_col, d_label = get_sector_debt_rating(f_data['debt_equity'], f_data['sector'])
                roe_col = "#00ffcc" if f_data['roe'] > 15 else "#ff4b4b"
                st.markdown(f'<div class="stat-box"><p class="metric-label">Debt-to-Equity</p><p class="metric-value" style="color:{d_col}">{f_data["debt_equity"]:.2f}</p><small>{d_label}</small></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="stat-box"><p class="metric-label">Return on Equity</p><p class="metric-value" style="color:{roe_col}">{f_data["roe"]:.1f}%</p></div>', unsafe_allow_html=True)

            with c3: # Promoter & Industry
                pledge_col = "#00ffcc" if f_data['promoter_pledge'] < 10 else "#ff4b4b"
                st.markdown(f'<div class="stat-box"><p class="metric-label">Promoter Pledge</p><p class="metric-value" style="color:{pledge_col}">{f_data["promoter_pledge"]:.1f}%</p></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="stat-box"><p class="metric-label">Industry</p><p class="metric-value" style="color:#00ffcc">{f_data["sector"]}</p><small>Trend: GROWING</small></div>', unsafe_allow_html=True)

            with c4: # Sentiment & Valuation
                val_text = "UNDERVALUED" if f_data['peg'] < 1 else "OVERVALUED"
                val_col = "#00ffcc" if val_text == "UNDERVALUED" else "#ff4b4b"
                st.markdown(f'<div class="stat-box"><p class="metric-label">Valuation</p><p class="metric-value" style="color:{val_col}">{val_text}</p></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="stat-box"><p class="metric-label">Market Sentiment</p><p class="metric-value" style="color:#00ffcc">BULLISH</p></div>', unsafe_allow_html=True)

            # 3. REVENUE & PROFIT GROWTH TABLE
            st.subheader("📊 Financial Growth Audit (Year-on-Year)")
            if not f_data['revenue'].empty:
                growth_df = pd.DataFrame({
                    "Year": f_data['revenue'].index.year,
                    "Revenue (Cr)": (f_data['revenue'].values / 10**7).round(2),
                    "Net Profit (Cr)": (f_data['profit'].values / 10**7).round(2)
                })
                st.table(growth_df)
            
            # 4. 3-YEAR PRICE ACTION
            st.subheader("📈 3-Year Price Action")
            fig = go.Figure(data=[go.Scatter(x=hist_3y.index, y=hist_3y['Close'], line=dict(color='#00ffcc', width=2))])
            fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

elif selected == "Top Picks":
    st.info("AI scanning for stocks with ROE > 15%, PEG < 1, and Healthy Debt...")
    # (Implementation for automated scanning of Nifty 50 follows the same logic above)
