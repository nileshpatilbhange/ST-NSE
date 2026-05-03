import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from GoogleNews import GoogleNews
import json

# --- CONFIG ---
st.set_page_config(page_title="NSE Expert Analytics", layout="wide")

# --- 1. MARKET WATCH (TOP 20 NSE) ---
st.header("📋 Market Watch: Top 20 NSE")

top_20 = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "BHARTIARTL.NS", "ICICIBANK.NS", 
    "INFY.NS", "SBIN.NS", "HINDUNILVR.NS", "ITC.NS", "LICI.NS",
    "LTIM.NS", "BAJFINANCE.NS", "HCLTECH.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "ADANIENT.NS", "KOTAKBANK.NS", "TITAN.NS", "ONGC.NS", "TATAMOTORS.NS"
]

@st.cache_data(ttl=600)
def get_top_20():
    rows = []
    # Fetching in bulk is faster and more reliable
    try:
        data = yf.download(top_20, period="2d", group_by='ticker', progress=False)
        for t in top_20:
            if t in data and not data[t].empty:
                c = data[t]['Close'].iloc[-1]
                p = data[t]['Close'].iloc[-2]
                change = ((c - p) / p) * 100
                rows.append({
                    "Symbol": t.replace(".NS", ""),
                    "Price": round(float(c), 2),
                    "Change": f"{change:.2f}%",
                    "Signal": "🟢" if change > 0 else "🔴"
                })
    except Exception as e:
        st.warning(f"Market Watch update delayed: {e}")
    return pd.DataFrame(rows)

watch_df = get_top_20()
if not watch_df.empty:
    st.table(watch_df)
else:
    st.info("Market is closed or data is currently refreshing.")

# --- 2. STOCKS IN-NEWS ---
st.header("🗞️ Stocks In-News")

@st.cache_data(ttl=3600)
def get_news():
    try:
        gn = GoogleNews(period='7d', lang='en', region='IN')
        gn.search('NSE India Stock Market News')
        results = gn.result()
        # Clean results to ensure every item has a title
        return [n for n in results if n.get('title') and len(n['title'].strip()) > 0]
    except:
        return []

news_list = get_news()
if news_list:
    for n in news_list[:8]: # Show top 8 news items
        # Safety check for title to prevent the Expander Error
        title = n.get('title', 'News Update')
        with st.expander(title):
            st.write(f"**Source:** {n.get('media', 'N/A')} | **Date:** {n.get('date', 'Recent')}")
            desc = n.get('desc', 'No description available.')
            st.write(desc)
            
            # Scam Alert logic
            scam_keywords = ['scam', 'fraud', 'probe', 'sebi', 'penalty', 'fine', 'irregularity']
            is_neg = any(w in title.lower() or w in desc.lower() for w in scam_keywords)
            
            if is_neg:
                st.error("Signal: 🔴 Negative Sentiment Alert")
            else:
                st.success("Signal: 🟢 Neutral/Positive")
            
            if n.get('link'):
                st.link_button("Read Full Story", n['link'])
else:
    st.info("No major stock news found in the last week.")

# --- 3. DEEP AUDIT (EXPERT JSON) ---
st.divider()
st.sidebar.header("Expert Analysis Settings")
ticker_raw = st.sidebar.text_input("Enter Ticker for Deep Audit", "RELIANCE").upper()
ticker_ns = f"{ticker_raw}.NS" if not ticker_raw.endswith(".NS") else ticker_raw

st.header(f"🕵️ Deep Audit: {ticker_raw}")

if st.button("Generate Expert Deep Audit JSON"):
    try:
        with st.spinner("Expert Agent is analyzing..."):
            s = yf.Ticker(ticker_ns)
            info = s.info
            h3y = s.history(period="3y")
            
            if not info or 'currentPrice' not in info:
                st.error("Could not fetch fundamental data for this ticker.")
            else:
                # Financial Rules Logic
                sector = info.get('sector', 'General')
                # Debt to Equity (converting percentage to decimal if needed)
                de_raw = info.get('debtToEquity', 0)
                de = de_raw / 100 if de_raw else 0
                
                # Rule: Industry-specific Debt
                is_finance_infra = any(x in sector.lower() for x in ['bank', 'finance', 'infra', 'construction'])
                de_safe = de < 3 if is_finance_infra else de < 1
                
                # ROE status
                roe_val = (info.get('returnOnEquity', 0) * 100)
                roe_status = "Increasing/Stable" if roe_val > 15 else "Review Needed"
                
                # PEG & Valuation
                peg = info.get('pegRatio', 1.0)
                val_status = "Fair" if 0.8 <= peg <= 1.2 else ("Undervalued" if peg < 0.8 else "Overvalued")
                
                # Health Score (0-10)
                score = 0
                if de_safe: score += 2
                if roe_val > 15: score += 2
                if info.get('heldPercentInsiders', 0) > 0.45: score += 2
                if val_status != "Overvalued": score += 2
                if info.get('revenueGrowth', 0) > 0.10: score += 2

                audit_json = {
                    "details": {
                        "current_price": f"₹{info.get('currentPrice')}",
                        "health_score": f"{score}/10",
                        "valuation_status": val_status,
                        "sentiment": "Positive" if score >= 7 else "Cautious/Negative",
                        "price_action_3y": f"{((h3y['Close'].iloc[-1]/h3y['Close'].iloc[0])-1)*100:.2f}%",
                        "final_recommendation": "BUY" if score >= 8 else ("HOLD" if score >= 5 else "AVOID")
                    },
                    "growth": {
                        "net_profit": f"₹{info.get('netIncomeToCommon', 0)/10**7:.2f} Cr",
                        "profit_growth_pct": f"{info.get('revenueGrowth', 0)*100:.2f}%"
                    },
                    "ratios": {
                        "debt_to_equity": f"{de:.2f} ({'Safe' if de_safe else 'High'})",
                        "roe": f"{roe_val:.2f}% ({roe_status})",
                        "pe_ratio": info.get('trailingPE', 'N/A'),
                        "peg_ratio": peg
                    },
                    "holdings": {
                        "promoter_holding_pct": f"{info.get('heldPercentInsiders', 0)*100:.2f}%",
                        "pledged_pct": "Refer to NSE direct filings"
                    },
                    "industry": {
                        "sector_name": sector,
                        "trend_status": "Bullish Trend" if score > 6 else "Consolidating"
                    }
                }
                
                st.subheader("Financial Analyst JSON Result:")
                st.json(audit_json)

    except Exception as e:
        st.error(f"Audit could not be completed: {e}")
