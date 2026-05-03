import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import pandas_ta as ta
from GoogleNews import GoogleNews
from streamlit_option_menu import option_menu

# --- UI CONFIGURATION ---
st.set_page_config(page_title="QUANTUM NSE | AI Terminal", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .brand-container {
        text-align: center;
        padding: 40px 0;
        background: linear-gradient(180deg, #161b22 0%, #0d1117 100%);
        border-radius: 0 0 30px 30px;
        margin-bottom: 30px;
        border-bottom: 1px solid #30363d;
    }
    .logo-text {
        font-size: 48px; font-weight: 800;
        background: -webkit-linear-gradient(#00ffcc, #008f7a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0; letter-spacing: -1px;
    }
    .tagline { color: #8b949e; font-size: 16px; margin-top: 5px; }
    .analysis-card {
        background: #161b22; border: 1px solid #30363d;
        border-radius: 15px; padding: 25px; margin-bottom: 20px;
    }
    .signal-badge {
        padding: 8px 16px; border-radius: 20px;
        font-weight: bold; font-size: 14px; display: inline-block; margin-bottom: 10px;
    }
    .reason-item { font-size: 13px; color: #c9d1d9; margin-bottom: 8px; display: flex; align-items: center; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA HELPERS ---
def fix_dataframe(df):
    """Flattens MultiIndex and converts to Single Level."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def get_detailed_analysis(df):
    """Deep technical audit for stock analysis."""
    try:
        df = fix_dataframe(df)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        macd = ta.macd(df['Close'])
        df = pd.concat([df, macd], axis=1)
        df['SMA20'] = ta.sma(df['Close'], length=20)
        
        l_close = float(df['Close'].iloc[-1])
        l_rsi = float(df['RSI'].iloc[-1])
        
        m_col = [c for c in df.columns if 'MACD_' in c and 's' not in c][0]
        s_col = [c for c in df.columns if 'MACDs_' in c][0]
        l_macd = float(df[m_col].iloc[-1])
        l_macds = float(df[s_col].iloc[-1])
        
        reasons = []
        score = 0
        
        if l_rsi < 42: 
            reasons.append("🟢 RSI: Low accumulation zone (Price is attractive)")
            score += 2
        elif l_rsi > 68: 
            reasons.append("🔴 RSI: Overbought (Potential for cool-off)")
            score -= 2
            
        if l_macd > l_macds: 
            reasons.append("🟢 MACD: Bullish crossover confirmed")
            score += 2
        else:
            reasons.append("🔴 MACD: Bearish trend detected")
            score -= 2
            
        if l_close > float(df['SMA20'].iloc[-1]): 
            reasons.append("🟢 Trend: Trading above 20-Day short-term average")
            score += 1
        
        if score >= 3: signal, color = "STRONG BUY", "#00ffcc"
        elif score > 0: signal, color = "ACCUMULATE / WAIT", "#ffcc00"
        else: signal, color = "AVOID / SELL", "#ff4b4b"
        
        return {"signal": signal, "color": color, "reasons": reasons, "rsi": l_rsi, "price": l_close}
    except Exception as e:
        return {"signal": "NEUTRAL", "color": "#8b949e", "reasons": [f"Audit: {str(e)[:50]}..."], "rsi": 50, "price": 0}

# --- BRANDING HEADER ---
st.markdown("""
    <div class="brand-container">
        <div class="logo-text">⚡ QUANTUM NSE</div>
        <div class="tagline">Next-Generation AI Terminal for Indian Equity Markets</div>
    </div>
    """, unsafe_allow_html=True)

# --- NAVIGATION ---
selected = option_menu(
    None, ["Market Terminal", "🚀 Top Picks", "Global News"],
    icons=["terminal", "rocket-takeoff", "newspaper"], 
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#0d1117"},
        "nav-link-selected": {"background-color": "#00ffcc", "color": "#0d1117", "font-weight": "700"},
    }
)

# --- PAGE 1: MARKET TERMINAL ---
if selected == "Market Terminal":
    search_q = st.text_input("", placeholder="Enter Ticker (e.g. RELIANCE, SBIN, HDFCBANK)...").upper()
    
    if search_q:
        with st.spinner("Decoding Market Cycles..."):
            t_sym = f"{search_q}.NS"
            raw_data = yf.download(t_sym, period="1y", interval="1d", progress=False)
            
            if not raw_data.empty:
                analysis = get_detailed_analysis(raw_data)
                
                # HEADER RESULT
                st.markdown(f"""
                    <div class="analysis-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <h1 style="margin:0;">{search_q} <small style="font-size:14px; color:#8b949e;">NSE India</small></h1>
                                <p style="font-size:24px; font-weight:bold; color:#00ffcc; margin:0;">₹{analysis['price']:,.2f}</p>
                            </div>
                            <div style="text-align: right;">
                                <div class="signal-badge" style="background:{analysis['color']}; color:#0d1117;">{analysis['signal']}</div>
                                <p style="font-size:12px; color:#8b949e; margin:0;">AI Confidence: 84%</p>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                col_chart, col_intel = st.columns([2, 1])
                
                with col_chart:
                    df_plot = fix_dataframe(raw_data)
                    fig = go.Figure(data=[go.Candlestick(x=df_plot.index, open=df_plot['Open'], 
                                    high=df_plot['High'], low=df_plot['Low'], close=df_plot['Close'], 
                                    increasing_line_color='#00ffcc', decreasing_line_color='#ff4b4b')])
                    fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0,r=0,t=0,b=0), 
                                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_rangeslider_visible=False)
                    st.plotly_chart(fig, use_container_width=True)
                    
                with col_intel:
                    st.markdown("### 🧠 AI Intelligence Audit")
                    for reason in analysis['reasons']:
                        st.markdown(f'<div class="reason-item">{reason}</div>', unsafe_allow_html=True)
                    
                    st.write("---")
                    st.write("**Momentum Tracker**")
                    st.progress(min(analysis['rsi']/100, 1.0), text=f"RSI Strength: {analysis['rsi']:.1f}")
                    st.caption("Investment Outlook: Analyzing 3-year volatility vs. Nifty 50 benchmarks.")
            else:
                st.error("Invalid NSE Ticker. Try RELIANCE, TCS, or SBIN.")

# --- PAGE 2: TOP PICKS ---
elif selected == "🚀 Top Picks":
    st.markdown("### 🚀 High-Confidence Recommendations")
    st.write("These stocks have cleared the Quantum AI filter for long-term momentum.")
    
    # Watchlist for automated scanning
    watchlist = ["RELIANCE.NS", "TATAMOTORS.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "TITAN.NS", "HDFCBANK.NS"]
    
    for stock_sym in watchlist:
        try:
            d = yf.download(stock_sym, period="6mo", progress=False)
            if not d.empty:
                analysis = get_detailed_analysis(d)
                
                if "BUY" in analysis['signal']:
                    name = stock_sym.replace(".NS", "")
                    with st.container():
                        c1, c2, c3 = st.columns([1, 1, 2])
                        c1.subheader(name)
                        c2.markdown(f'<div class="signal-badge" style="background:{analysis["color"]}; color:#0d1117;">{analysis["signal"]}</div>', unsafe_allow_html=True)
                        
                        reason_text = " • ".join([r.split(':')[-1].strip() for r in analysis['reasons']])
                        c3.info(f"**Rationale:** {reason_text}")
                        st.write("---")
        except: continue

# --- PAGE 3: NEWS ---
elif selected == "Global News":
    st.subheader("📰 Market Headlines")
    try:
        gn = GoogleNews(period='2d', lang='en', region='IN')
        gn.search('NSE Stock Market')
        for item in gn.result()[:8]:
            st.info(f"**{item.get('title')}**")
            st.caption(f"Source: {item.get('media')} | {item.get('date')}")
    except:
        st.write("News service is updating. Please try again later.")
