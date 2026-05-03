import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURATION ---
EOD_API_KEY = "YOUR_EODHD_API_KEY"  # Replace with your actual key
BASE_URL = "https://eodhd.com/api"

st.set_page_config(page_title="Indian Market Analyzer", layout="wide")

# --- DATA FETCHING ---
@st.cache_data(ttl=3600)
def get_stock_data(ticker):
    """
    Fetches EOD and Fundamental data with explicit error catching
    to avoid the 'Expecting value' JSON error.
    """
    # EODHD requires the .NSE suffix for Indian Stocks
    sym = f"{ticker}.NSE"
    hist_url = f"{BASE_URL}/eod/{sym}?api_token={EOD_API_KEY}&fmt=json&period=d&from=2023-01-01"
    fund_url = f"{BASE_URL}/fundamentals/{sym}?api_token={EOD_API_KEY}"
    
    try:
        # 1. Fetch Historical Data
        h_resp = requests.get(hist_url)
        if h_resp.status_code != 200:
            return None, None, f"Error {h_resp.status_code}: {h_resp.reason}. (Check API Plan for NSE access)"
        
        # Check if the content is empty before parsing JSON
        if not h_resp.text.strip():
            return None, None, f"Empty response for {sym}. Ticker may not exist on EODHD."
            
        h_data = h_resp.json()
        df = pd.DataFrame(h_data)
        df['date'] = pd.to_datetime(df['date'])
        
        # 2. Fetch Fundamental Data
        f_resp = requests.get(fund_url)
        f_data = None
        if f_resp.status_code == 200 and f_resp.text.strip():
            f_data = f_resp.json()
        
        return df, f_data, None
        
    except Exception as e:
        return None, None, f"Connection Failed: {str(e)}"

# --- UI LAYOUT ---
st.title("📈 Indian Stock Market Analysis (3-Year Horizon)")
st.sidebar.header("Settings")

ticker_input = st.sidebar.text_input("Enter NSE Ticker (e.g., RELIANCE, TCS, HDFCBANK)", value="RELIANCE").upper()

if ticker_input:
    df, fundamentals, error = get_stock_data(ticker_input)

    if error:
        st.error(error)
        st.info("💡 **Tip:** Most free EODHD keys are restricted to US markets. If you are using a free tier, you may need a 'Standard' plan for Indian NSE data.")
    else:
        # Layout: 2 Columns
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader(f"{ticker_input}.NSE - Price History")
            fig = go.Figure(data=[go.Candlestick(
                x=df['date'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close']
            )])
            fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Key Metrics")
            if fundamentals:
                # Extracting specific fundamental data
                stats = fundamentals.get('Highlights', {})
                valuation = fundamentals.get('Valuation', {})
                
                st.metric("Market Cap", f"₹{stats.get('MarketCapitalization', 'N/A'):,.0f}")
                st.metric("PE Ratio", f"{stats.get('PERatio', 'N/A')}")
                st.metric("Forward PE", f"{valuation.get('ForwardPE', 'N/A')}")
                st.metric("Dividend Yield", f"{stats.get('DividendYield', '0')}%")
            else:
                st.warning("Fundamentals data unavailable for this ticker.")

        # Long Term Analysis Section
        st.divider()
        st.subheader("Analysis for 3+ Year Holding")
        
        if len(df) > 200:
            current_price = df['close'].iloc[-1]
            ma_200 = df['close'].rolling(window=200).mean().iloc[-1]
            st.write(f"**Current Price:** ₹{current_price:,.2f}")
            st.write(f"**200-Day Moving Average:** ₹{ma_200:,.2f}")
            
            if current_price > ma_200:
                st.success("Analysis: Stock is currently in a long-term uptrend (Above 200-DMA).")
            else:
                st.warning("Analysis: Stock is below its 200-day average. Caution advised for new entries.")
