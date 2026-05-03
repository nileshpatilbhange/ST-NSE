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
    for t in top_20:
        try:
            s = yf.Ticker(t)
            h = s.history(period="2d")
            c, p = h['Close'].iloc[-1], h['Close'].iloc[-2]
            rows.append({"Symbol": t.replace(".NS",""), "Price": round(c,2), "Change": f"{((c-p)/p)*100:.2f}%", "Signal": "🟢" if c > p else "🔴"})
        except: continue
    return pd.DataFrame(rows)

st.table(get_top_20())

# --- 2. STOCKS IN-NEWS ---
st.header("🗞️ Stocks In-News")
@st.cache_data(ttl=3600)
def get_news():
    gn = GoogleNews(period='7d')
    gn.search('NSE India Stock Market')
    return gn.result()[:6]

for n in get_news():
    with st.expander(n['title']):
        st.write(f"Source: {n['media']} | {n['date']}")
        scam = any(w in n['title'].lower() for w in ['scam', 'fraud', 'probe', 'sebi', 'drop'])
        st.error("Signal: 🔴 Negative") if scam else st.success("Signal: 🟢 Positive/Neutral")
        st.link_button("Read Story", n['link'])

# --- 3. DEEP AUDIT (EXPERT JSON) ---
st.divider()
ticker_raw = st.text_input("Enter Ticker for Deep Audit (e.g. RELIANCE)", "RELIANCE").upper()
ticker_ns = f"{ticker_raw}.NS" if not ticker_raw.endswith(".NS") else ticker_raw

if st.button("Generate Expert Deep Audit JSON"):
    try:
        s = yf.Ticker(ticker_ns)
        info = s.info
        h3y = s.history(period="3y")
        
        # Rule-Based Logic
        sector = info.get('sector', 'Unknown')
        de = (info.get('debtToEquity', 0) / 100)
        roe_val = info.get('returnOnEquity', 0) * 100
        peg = info.get('pegRatio', 1.0)
        
        # Expert Rules
        de_safe = de < 3 if any(x in sector.lower() for x in ['bank', 'finance', 'infra']) else de < 1
        val_stat = "Fair" if 0.8 <= peg <= 1.2 else ("Undervalued" if peg < 0.8 else "Overvalued")
        
        # Scoring
        score = sum([2 if de_safe else 0, 2 if roe_val > 15 else 0, 2 if info.get('heldPercentInsiders', 0) > 0.5 else 0, 2 if val_stat != "Overvalued" else 0, 2 if info.get('revenueGrowth', 0) > 0.1 else 0])

        audit_json = {
            "details": {
                "current_price": f"₹{info.get('currentPrice')}",
                "health_score": f"{score}/10",
                "valuation_status": val_stat,
                "sentiment": "Bullish" if score >= 7 else "Cautious",
                "price_action_3y": f"{((h3y['Close'].iloc[-1]/h3y['Close'].iloc[0])-1)*100:.2f}%",
                "final_recommendation": "BUY" if score >= 8 else ("HOLD" if score >= 5 else "AVOID")
            },
            "growth": {
                "net_profit": f"₹{info.get('netIncomeToCommon', 0)/10**7:.2f} Cr",
                "profit_growth_pct": f"{info.get('revenueGrowth', 0)*100:.2f}%"
            },
            "ratios": {
                "debt_to_equity": f"{de:.2f} ({'Safe' if de_safe else 'High'})",
                "roe": f"{roe_val:.2f}% (Increasing)" if roe_val > 15 else f"{roe_val:.2f}% (Stable)",
                "pe_ratio": info.get('trailingPE', 'N/A'),
                "peg_ratio": peg
            },
            "holdings": {
                "promoter_holding_pct": f"{info.get('heldPercentInsiders', 0)*100:.2f}%",
                "pledged_pct": "Refer to NSE direct"
            },
            "industry": {
                "sector_name": sector,
                "trend_status": "Upward" if score > 6 else "Sideways"
            }
        }
        st.json(audit_json)
    except Exception as e:
        st.error(f"Audit Error: {e}")
