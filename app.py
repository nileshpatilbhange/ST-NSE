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
    .stat-box { background: #1c2128; border: 1px solid #30363d; border-radius: 12px; padding: 15px; text-align: center; }
    .metric-label { font-size: 11px; color: #8b949e; text-transform: uppercase; }
    .metric-value { font-size: 22px; font-weight: bold; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- BRANDING ---
st.markdown('<div class="brand-container"><div class="logo-text">⚡ QUANTUM NSE PRO</div><div style="color:#8b949e">Autonomous TLS-Validated Market Data</div></div>', unsafe_allow_html=True)

# --- DATA FETCHING (Cleaned Engine) ---
@st.cache_data(ttl=900) # 15-minute cache to respect request frequency
def fetch_analysis(ticker):
    sym = f"{ticker}.NS" 
    try:
        # We stop setting a manual requests session here
        # Letting yfinance use its internal default handler
        stock = yf.Ticker(sym)
        
        # Fetch 5 years to provide deep context for your 3-year horizon
        hist = stock.history(period="5y")
        
        if hist.empty:
            return None, None, "No data returned. Ticker may be delisted or invalid."
        
        info = stock.info
        return hist, info, None
    except Exception as e:
        return None, None, f"Protocol Error: {str(e)}"

# --- MAIN INTERFACE ---
ticker_input = st.text_input("Enter NSE Ticker (e.g., RELIANCE, TCS)", value="RELIANCE").upper()

if ticker_input:
    with st.spinner(f"Establishing secure connection to NSE for {ticker_input}..."):
        df, info, error = fetch_analysis(ticker_input)
        
        if error:
            st.error(error)
            st.warning("🔄 Yahoo Finance is throttling requests. Please wait 30-60 seconds before retrying.")
        else:
            # 1. KEY PERFORMANCE INDICATORS
            c1, c2, c3, c4 = st.columns(4)
            current_price = df['Close'].iloc[-1]
            
            # Using .get() to prevent crashes if certain keys are missing
            pe = info.get('trailingPE', 0)
            roe = info.get('returnOnEquity', 0) * 100
            debt = info.get('debtToEquity', 0)
            
            with c1:
                st.markdown(f'<div class="stat-box"><p class="metric-label">Live Price</p><p class="metric-value">₹{current_price:,.2f}</p></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="stat-box"><p class="metric-label">P/E Ratio</p><p class="metric-value" style="color:{"#00ffcc" if pe < 30 else "#ff4b4b"}">{pe if pe else "N/A"}</p></div>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div class="stat-box"><p class="metric-label">ROE %</p><p class="metric-value">{roe:.1f}%</p></div>', unsafe_allow_html=True)
            with c4:
                st.markdown(f'<div class="stat-box"><p class="metric-label">Debt/Equity</p><p class="metric-value">{debt/100:.2f}</p></div>', unsafe_allow_html=True)

            # 2. 3-YEAR INVESTMENT CHART
            st.subheader("📈 Institutional Trend Analysis (3-Year Context)")
            
            df['MA200'] = df['Close'].rolling(window=200).mean()
            df_3y = df.last('1095D') 
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_3y.index, y=df_3y['Close'], name="Share Price", line=dict(color='#00ffcc', width=2)))
            fig.add_trace(go.Scatter(x=df_3y.index, y=df_3y['MA200'], name="200-DMA Support", line=dict(color='#ffcc00', width=1.5, dash='dot')))
            
            fig.update_layout(
                template="plotly_dark", 
                height=450, 
                margin=dict(l=0,r=0,t=0,b=0),
                paper_bgcolor="rgba(0,0,0,0)", 
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)

            # 3. LONG-TERM VERDICT
            st.divider()
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.subheader("🎯 Investment Verdict")
                if current_price > df['MA200'].iloc[-1]:
                    st.success("✅ **BULLISH:** Stock is trading above its 200-Day Moving Average, indicating a long-term uptrend.")
                else:
                    st.warning("⚠️ **CAUTION:** Stock is below its 200-Day average. Consider waiting for a trend reversal for new 3-year entries.")
            
            with col_b:
                st.subheader("📊 Fundamental Health")
                mcap = info.get('marketCap', 0) / 1e7 # Convert to Crores
                div = info.get('dividendYield', 0) * 100
                
                st.write(f"**Market Cap:** ₹{mcap:,.0f} Cr")
                st.write(f"**Dividend Yield:** {div:.2f}%")
                st.write(f"**Sector:** {info.get('sector', 'N/A')}")
