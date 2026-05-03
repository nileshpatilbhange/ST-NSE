import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from GoogleNews import GoogleNews
import json

# --- CONFIGURATION ---
st.set_page_config(page_title="NSE India Analyzer", layout="wide")

# --- 1. MARKET WATCH (TOP 20) ---
st.title("📈 NSE India Dashboard")
st.header("📋 Market Watch: Top 20 Bluechips")

top_20_nse = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "BHARTIARTL.NS", "ICICIBANK.NS", 
    "INFY.NS", "SBIN.NS", "HINDUNILVR.NS", "ITC.NS", "LICI.NS",
    "LTIM.NS", "BAJFINANCE.NS", "HCLTECH.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "ADANIENT.NS", "KOTAKBANK.NS", "TITAN.NS", "ONGC.NS", "TATAMOTORS.NS"
]

@st.cache_data(ttl=600)
def get_market_watch():
    data_list = []
    for ticker in top_20_nse:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2d")
            if len(hist) >= 2:
                curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                change = ((curr - prev) / prev) * 100
                data_list.append({
                    "Symbol": ticker.replace(".NS", ""),
                    "Price": f"₹{curr:.2f}",
                    "Change %": f"{change:.2f}%",
                    "Trend": "🟢" if change > 0 else "🔴"
                })
        except: continue
    return pd.DataFrame(data_list)

st.table(get_market_watch())

# --- 2. STOCKS IN-NEWS ---
st.divider()
st.header("🗞️ Stocks In-News (Last 7 Days)")

@st.cache_data(ttl=3600)
def fetch_news():
    googlenews = GoogleNews(period='7d')
    googlenews.search('NSE India Stocks')
    return googlenews.result()[:8]

news_items = fetch_news()
if news_items:
    cols = st.columns(2)
    for i, item in enumerate(news_items):
        with cols[i % 2].expander(f"{item['title'][:60]}..."):
            st.write(f"**Source:** {item['media']} | **Date:** {item['date']}")
            st.write(item['desc'])
            scam_keywords = ['scam', 'fraud', 'probe', 'fall', 'penalty', 'sebi', 'drop']
            is_neg = any(w in item['title'].lower() or w in item['desc'].lower() for w in scam_keywords)
            st.markdown(f"**Signal:** {'🔴 Negative/Alert' if is_neg else '🟢 Neutral/Positive'}")
            st.link_button("Read More", item['link'])

# --- 3. DEEP AUDIT SECTION ---
st.divider()
st.sidebar.header("Deep Audit Settings")
ticker_input = st.sidebar.text_input("Enter NSE Ticker", "RELIANCE").upper()
search_ticker = f"{ticker_input}.NS" if not ticker_input.endswith(".NS") else ticker_input

st.header(f"🕵️ Deep Audit: {ticker_input}")

if st.button("Run Financial Expert Audit"):
    try:
        with st.spinner("Analyzing Fundamentals..."):
            ticker_obj = yf.Ticker(search_ticker)
            info = ticker_obj.info
            hist_3y = ticker_obj.history(period="3y")
            
            # Calculations
            sector = info.get('sector', '')
            d_e = (info.get('debtToEquity', 0) / 100) if info.get('debtToEquity') else 0
            roe = (info.get('returnOnEquity', 0) * 100)
            peg = info.get('pegRatio', 1.0)
            
            # Rule Processing
            if any(x in sector.lower() for x in ['bank', 'financial', 'infra']):
                de_status = "Safe" if d_e < 3 else "High"
            else:
                de_status = "Safe" if d_e < 1 else "High"
            
            val_status = "Fair" if 0.8 <= peg <= 1.2 else ("Undervalued" if peg < 0.8 else "Overvalued")
            
            # Health Score Logic
            score = 0
            if de_status == "Safe": score += 2
            if roe > 15: score += 2
            if info.get('heldPercentInsiders', 0) > 0.4: score += 2
            if val_status != "Overvalued": score += 2
            if info.get('revenueGrowth', 0) > 0.1: score += 2

            # JSON Structure
            audit_json = {
                "details": {
                    "current_price": f"₹{info.get('currentPrice', 0)}",
                    "health_score": f"{score}/10",
                    "valuation_status": val_status,
                    "sentiment": "Positive" if score >= 7 else "Cautious",
                    "price_action_3y": f"{((hist_3y['Close'].iloc[-1]/hist_3y['Close'].iloc[0])-1)*100:.2f}%",
                    "final_recommendation": "BUY" if score >= 8 else ("HOLD" if score >= 5 else "AVOID")
                },
                "growth": {
                    "net_profit": f"₹{info.get('netIncomeToCommon', 0)/10**7:.2f} Cr",
                    "profit_growth_pct": f"{info.get('revenueGrowth', 0)*100:.2f}%"
                },
                "ratios": {
                    "debt_to_equity": f"{d_e:.2f} ({de_status})",
                    "roe": f"{roe:.2f}% (Stable)",
                    "pe_ratio": info.get('trailingPE', 'N/A'),
                    "peg_ratio": peg
                },
                "holdings": {
                    "promoter_holding_pct": f"{info.get('heldPercentInsiders', 0)*100:.2f}%",
                    "pledged_pct": "Refer to BSE/NSE Filings"
                },
                "industry": {
                    "sector_name": sector,
                    "trend_status": "Bullish" if info.get('currentPrice', 0) > hist_3y['Close'].mean() else "Bearish"
                }
            }
            st.json(audit_json)
    except Exception as e:
        st.error(f"Could not complete audit: {e}")
