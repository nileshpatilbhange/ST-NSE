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
    .brand-title { color: #00ffcc; font-size: 32px; font-weight: 800; margin-bottom: 0px; }
    .brand-tagline { color: #8b949e; font-size: 14px; margin-bottom: 25px; }
    .metric-card {
        background: #161b22; border: 1px solid #30363d; border-radius: 8px;
        padding: 15px; text-align: center;
    }
    .signal-buy { color: #00ffcc; font-weight: bold; border: 1px solid #00ffcc; padding: 2px 8px; border-radius: 4px; }
    .signal-sell { color: #ff4b4b; font-weight: bold; border: 1px solid #ff4b4b; padding: 2px 8px; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

# --- BRANDING ---
st.markdown('<p class="brand-title">⚡ QUANTUM NSE</p>', unsafe_allow_html=True)
st.markdown('<p class="brand-tagline">Advanced AI-Powered Analytics for the Indian Capital Markets</p>', unsafe_allow_html=True)

# --- SESSION STATE FOR INTERACTIVITY ---
if 'selected_stock' not in st.session_state:
    st.session_state.selected_stock = "^NSEI"
if 'stock_name' not in st.session_state:
    st.session_state.stock_name = "Nifty 50"

# --- DATA ENGINE ---
@st.cache_data(ttl=300)
def get_all_indices():
    indices = {
        "Nifty 50": "^NSEI", "Bank Nifty": "^NSEBANK", "Nifty IT": "^CNXIT",
        "Nifty Auto": "^CNXAUTO", "Nifty Pharma": "^CNXPHARMA", "Nifty Metal": "^CNXMETAL",
        "Nifty FMCG": "^CNXFMCG", "GIFT Nifty": "IN1!"
    }
    data = {}
    for name, sym in indices.items():
        try:
            t = yf.Ticker(sym)
            h = t.history(period="5d")
            if len(h) >= 2:
                curr, prev = h['Close'].iloc[-1], h['Close'].iloc[-2]
                change = ((curr - prev) / prev) * 100
                data[name] = {"price": curr, "change": change, "sym": sym}
        except: continue
    return data

def get_ai_signal(df):
    """Calculates RSI & MACD for Trading Signals"""
    # RSI
    df['RSI'] = ta.rsi(df['Close'], length=14)
    # MACD
    macd = ta.macd(df['Close'])
    df = pd.concat([df, macd], axis=1)
    
    last_rsi = df['RSI'].iloc[-1]
    # MACD Line vs Signal Line
    macd_val = df['MACD_12_26_9'].iloc[-1]
    macd_sig = df['MACDs_12_26_9'].iloc[-1]
    
    if last_rsi < 35 and macd_val > macd_sig:
        return "STRONG BUY", "Oversold with Bullish MACD Crossover", "#00ffcc"
    elif last_rsi > 65 and macd_val < macd_sig:
        return "STRONG SELL", "Overbought with Bearish MACD Crossover", "#ff4b4b"
    elif macd_val > macd_sig:
        return "BUY", "Bullish MACD Momentum", "#00ffcc"
    elif macd_val < macd_sig:
        return "SELL", "Bearish Trend", "#ff4b4b"
    else:
        return "NEUTRAL", "Consolidating price action", "#8b949e"

# --- NAVIGATION ---
selected = option_menu(
    None, ["Market View", "Top Recommendations", "News"],
    icons=["cpu", "award", "newspaper"], orientation="horizontal",
    styles={"nav-link-selected": {"background-color": "#00ffcc", "color": "#0d1117"}}
)

# --- PAGE 1: MARKET VIEW ---
if selected == "Market View":
    # 1. INDICES GRID
    indices_data = get_all_indices()
    if indices_data:
        # Create two rows of 4 columns
        cols = st.columns(4)
        for i, (name, val) in enumerate(indices_data.items()):
            col_idx = i % 4
            with cols[col_idx]:
                color = "#00ffcc" if val['change'] > 0 else "#ff4b4b"
                if st.button(f"{name}\n₹{val['price']:,.0f}", key=f"btn_{name}"):
                    st.session_state.selected_stock = val['sym']
                    st.session_state.stock_name = name
                st.markdown(f'<p style="color:{color}; font-size:12px; margin-top:-15px; text-align:center;">'
                            f'{"▲" if val["change"] > 0 else "▼"} {abs(val["change"]):.2f}%</p>', unsafe_allow_html=True)
    
    st.write("---")
    
    # 2. SEARCH & LIVE CHART
    col_left, col_right = st.columns([3, 1])
    
    with col_left:
        search = st.text_input("🔍 Search NSE Ticker (e.g., RELIANCE, SBIN)", "").upper()
        active_sym = f"{search}.NS" if search else st.session_state.selected_stock
        active_name = search if search else st.session_state.stock_name
        
        # Native Plotly Chart
        df = yf.download(active_sym, period="6mo", interval="1d", progress=False)
        if not df.empty:
            fig = go.Figure(data=[go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                increasing_line_color='#00ffcc', decreasing_line_color='#ff4b4b', name="Price"
            )])
            # Add SMA 20
            df['SMA20'] = df['Close'].rolling(window=20).mean()
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], line=dict(color='#8b949e', width=1), name="SMA 20"))
            
            fig.update_layout(title=f"{active_name} Technical Canvas", template="plotly_dark", 
                              height=500, xaxis_rangeslider_visible=False,
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
            
    with col_right:
        st.markdown("#### ⚡ AI Signal")
        if not df.empty:
            signal, reason, s_color = get_ai_signal(df)
            st.markdown(f"""
                <div style="background:#161b22; padding:20px; border-radius:10px; border-top:4px solid {s_color};">
                    <h2 style="color:{s_color}; margin:0;">{signal}</h2>
                    <p style="font-size:14px; color:#8b949e;">{reason}</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Stock Stats
            st.write("---")
            st.markdown(f"**Last:** ₹{df['Close'].iloc[-1]:,.2f}")
            st.markdown(f"**Vol:** {df['Volume'].iloc[-1]:,.0f}")
            st.progress(min(max(ta.rsi(df['Close']).iloc[-1]/100, 0.0), 1.0), text="RSI Momentum")

# --- PAGE 2: TOP RECOMMENDATIONS ---
elif selected == "Top Recommendations":
    st.subheader("🚀 High-Confidence Momentum Picks")
    tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "TATAMOTORS.NS", "ADANIENT.NS", "ITC.NS", "SBIN.NS"]
    
    rec_data = []
    for t in tickers:
        d = yf.download(t, period="60d", progress=False)
        sig, reason, _ = get_ai_signal(d)
        if "BUY" in sig:
            rec_data.append({"Ticker": t.replace(".NS",""), "Signal": sig, "Rationale": reason})
    
    st.table(pd.DataFrame(rec_data))

# --- PAGE 3: NEWS ---
elif selected == "News":
    gn = GoogleNews(period='2d', lang='en', region='IN')
    gn.search('NSE Stocks India')
    for item in gn.result()[:8]:
        st.info(f"**{item.get('title')}**")
        st.caption(f"{item.get('media')} | {item.get('date')}")
