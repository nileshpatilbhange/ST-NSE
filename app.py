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
    .signal-box {
        background: #161b22; padding: 20px; border-radius: 10px; border-left: 5px solid;
    }
    </style>
    """, unsafe_allow_html=True)

# --- BRANDING ---
st.markdown('<p class="brand-title">⚡ QUANTUM NSE</p>', unsafe_allow_html=True)
st.markdown('<p class="brand-tagline">Advanced AI-Powered Analytics for the Indian Capital Markets</p>', unsafe_allow_html=True)

# --- SESSION STATE ---
if 'selected_stock' not in st.session_state:
    st.session_state.selected_stock = "^NSEI"
if 'stock_name' not in st.session_state:
    st.session_state.stock_name = "Nifty 50"

# --- DATA HELPERS ---
def fix_dataframe(df):
    """Flattens MultiIndex columns from yfinance."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

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
    """Calculates signals using technical indicators."""
    try:
        # Ensure we have clean columns
        df = fix_dataframe(df)
        
        # Calculate Indicators
        df['RSI'] = ta.rsi(df['Close'], length=14)
        macd = ta.macd(df['Close'])
        df = pd.concat([df, macd], axis=1)
        
        # Dynamically find MACD column names (they vary by parameters)
        macd_col = [c for c in df.columns if 'MACD_' in c and 's' not in c and 'h' not in c][0]
        sig_col = [c for c in df.columns if 'MACDs_' in c][0]
        
        last_rsi = df['RSI'].iloc[-1]
        last_macd = df[macd_col].iloc[-1]
        last_sig = df[sig_col].iloc[-1]
        
        if last_rsi < 35 and last_macd > last_sig:
            return "STRONG BUY", "Oversold RSI + Bullish MACD Crossover", "#00ffcc"
        elif last_rsi > 65 and last_macd < last_sig:
            return "STRONG SELL", "Overbought RSI + Bearish MACD Crossover", "#ff4b4b"
        elif last_macd > last_sig:
            return "BUY", "Positive MACD Momentum", "#00ffcc"
        elif last_macd < last_sig:
            return "SELL", "Negative MACD Momentum", "#ff4b4b"
        else:
            return "NEUTRAL", "No clear trend detected", "#8b949e"
    except Exception as e:
        return "NEUTRAL", "Analyzing indicators...", "#8b949e"

# --- NAVIGATION ---
selected = option_menu(
    None, ["Market View", "Top Recommendations", "News"],
    icons=["cpu", "award", "newspaper"], orientation="horizontal",
    styles={"nav-link-selected": {"background-color": "#00ffcc", "color": "#0d1117"}}
)

# --- PAGE 1: MARKET VIEW ---
if selected == "Market View":
    indices_data = get_all_indices()
    if indices_data:
        cols = st.columns(4)
        for i, (name, val) in enumerate(indices_data.items()):
            col_idx = i % 4
            with cols[col_idx]:
                color = "#00ffcc" if val['change'] > 0 else "#ff4b4b"
                if st.button(f"{name}\n₹{val['price']:,.0f}", key=f"btn_{name}"):
                    st.session_state.selected_stock = val['sym']
                    st.session_state.stock_name = name
                    st.rerun()
                st.markdown(f'<p style="color:{color}; font-size:12px; margin-top:-15px; text-align:center;">'
                            f'{"▲" if val["change"] > 0 else "▼"} {abs(val["change"]):.2f}%</p>', unsafe_allow_html=True)
    
    st.write("---")
    
    col_left, col_right = st.columns([3, 1])
    
    with col_left:
        search = st.text_input("🔍 Search NSE Ticker (e.g., RELIANCE, SBIN)", "").upper()
        active_sym = f"{search}.NS" if search else st.session_state.selected_stock
        active_name = search if search else st.session_state.stock_name
        
        # Download Data
        df = yf.download(active_sym, period="6mo", interval="1d", progress=False)
        
        if not df.empty:
            df = fix_dataframe(df) # Essential fix for Charting
            fig = go.Figure(data=[go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                increasing_line_color='#00ffcc', decreasing_line_color='#ff4b4b'
            )])
            fig.update_layout(title=f"{active_name} Analytics", template="plotly_dark", height=500, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
            
    with col_right:
        st.markdown("#### ⚡ AI Signal")
        if not df.empty:
            signal, reason, s_color = get_ai_signal(df)
            st.markdown(f"""
                <div class="signal-box" style="border-color:{s_color};">
                    <h2 style="color:{s_color}; margin:0;">{signal}</h2>
                    <p style="font-size:14px; color:#8b949e;">{reason}</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.write("---")
            # Extra stats
            last_price = df['Close'].iloc[-1]
            st.metric("Price", f"₹{last_price:,.2f}")
            st.caption("AI updates based on 1D closing data.")

# --- PAGE 2: TOP RECOMMENDATIONS ---
elif selected == "Top Recommendations":
    st.subheader("🚀 High-Confidence Recommendations")
    st.write("Stocks filtered by AI for potential 3-year growth.")
    
    # Watchlist for scanning
    watchlist = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "TATAMOTORS.NS", "SBIN.NS", "ITC.NS", "LTI.NS"]
    
    results = []
    for t in watchlist:
        try:
            d = yf.download(t, period="60d", progress=False)
            sig, reason, _ = get_ai_signal(d)
            if "BUY" in sig:
                results.append({"Ticker": t.replace(".NS",""), "Signal": sig, "Rationale": reason})
        except: continue
        
    if results:
        st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
    else:
        st.info("No strong buy signals detected currently. Markets are consolidating.")

# --- PAGE 3: NEWS ---
elif selected == "News":
    gn = GoogleNews(period='2d', lang='en', region='IN')
    gn.search('NSE Indian Stocks')
    for item in gn.result()[:10]:
        st.info(f"**{item.get('title')}**")
        st.caption(f"{item.get('media')} | {item.get('date')}")
