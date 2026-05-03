import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- UI CONFIGURATION ---
st.set_page_config(page_title="QUANTUM NSE | AI Terminal", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #ffffff; }
    .brand-container { text-align: center; padding: 25px 0; background: #161b22; border-radius: 0 0 30px 30px; border-bottom: 2px solid #00ffcc; margin-bottom: 20px; }
    .logo-text { font-size: 38px; font-weight: 800; color: #00ffcc; margin: 0; }
    .stat-box { background: #1c2128; border: 1px solid #30363d; border-radius: 12px; padding: 15px; text-align: center; min-height: 100px; }
    .metric-label { font-size: 11px; color: #8b949e; text-transform: uppercase; margin-bottom: 8px; }
    .metric-value { font-size: 22px; font-weight: bold; margin: 0; }
    </style>
    """, unsafe_allow_html=True)

# --- BRANDING ---
st.markdown('<div class="brand-container"><div class="logo-text">⚡ QUANTUM NSE PRO</div><div style="color:#8b949e">Autonomous Market Data Terminal</div></div>', unsafe_allow_html=True)

# --- DATA FETCHING ---
@st.cache_data(ttl=900)
def fetch_analysis(ticker):
    sym = f"{ticker}.NS" 
    try:
        stock = yf.Ticker(sym)
        hist = stock.history(period="5y")
        if hist.empty:
            return None, None, "No data returned. Ticker may be invalid."
        info = stock.info
        return hist, info, None
    except Exception as e:
        return None, None, f"Protocol Error: {str(e)}"

# --- MAIN INTERFACE ---
ticker_input = st.text_input("Enter NSE Ticker", value="RELIANCE").upper()

if ticker_input:
    with st.spinner(f"Analyzing {ticker_input}..."):
        df, info, error = fetch_analysis(ticker_input)
        
        if error:
            st.error(error)
        else:
            # 1. DATA PREP (Fixes the ValueError)
            current_price = df['Close'].iloc[-1]
            pe = info.get('trailingPE')
            roe = info.get('returnOnEquity')
            debt = info.get('debtToEquity')

            # Formatting Logic safely outside the f-string
            pe_val = f"{pe:.2f}" if isinstance(pe, (int, float)) else "N/A"
            roe_val = f"{roe * 100:.1f}%" if isinstance(roe, (int, float)) else "N/A"
            debt_val = f"{debt / 100:.2f}" if isinstance(debt, (int, float)) else "N/A"

            # 2. KPI GRID
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f'<div class="stat-box"><p class="metric-label">Live Price</p><p class="metric-value">₹{current_price:,.2f}</p></div>', unsafe_allow_html=True)
            with c2:
                color = "#00ffcc" if isinstance(pe, (int, float)) and pe < 30 else "#ff4b4b"
                st.markdown(f'<div class="stat-box"><p class="metric-label">P/E Ratio</p><p class="metric-value" style="color:{color}">{pe_val}</p></div>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div class="stat-box"><p class="metric-label">ROE %</p><p class="metric-value">{roe_val}</p></div>', unsafe_allow_html=True)
            with c4:
                st.markdown(f'<div class="stat-box"><p class="metric-label">Debt/Equity</p><p class="metric-value">{debt_val}</p></div>', unsafe_allow_html=True)

            # 3. 3-YEAR TREND ANALYSIS
            st.subheader("📈 Institutional Trend Analysis (3-Year Context)")
            df['MA200'] = df['Close'].rolling(window=200).mean()
            
            three_years_ago = df.index[-1] - pd.DateOffset(years=3)
            df_3y = df[df.index >= three_years_ago]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_3y.index, y=df_3y['Close'], name="Share Price", line=dict(color='#00ffcc', width=2)))
            fig.add_trace(go.Scatter(x=df_3y.index, y=df_3y['MA200'], name="200-DMA Support", line=dict(color='#ffcc00', width=1.5, dash='dot')))
            
            fig.update_layout(
                template="plotly_dark", height=450, margin=dict(l=0,r=0,t=0,b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)

            # 4. LONG-TERM VERDICT
            st.divider()
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("🎯 Investment Verdict")
                last_ma200 = df['MA200'].iloc[-1]
                if current_price > last_ma200:
                    st.success(f"✅ **BULLISH:** Price is above 200-DMA (₹{last_ma200:,.2f}).")
                else:
                    st.warning(f"⚠️ **CAUTION:** Price is below 200-DMA (₹{last_ma200:,.2f}).")
            
            with col_b:
                st.subheader("📊 Fundamental Health")
                mcap = (info.get('marketCap', 0) or 0) / 1e7
                div = (info.get('dividendYield', 0) or 0) * 100
                st.write(f"**Market Cap:** ₹{mcap:,.0f} Cr")
                st.write(f"**Dividend Yield:** {div:.2f}%")
                st.write(f"**Sector:** {info.get('sector', 'N/A')}")
