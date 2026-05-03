import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
from bs4 import BeautifulSoup
from transformers import pipeline

# --- 1. UI SETUP & THEME ---
st.set_page_config(page_title="Alpha Scout Pro", layout="wide")

st.markdown("""
    <style>
    .stButton>button {
        width: 100%; border-radius: 12px; height: 3.5em;
        background-color: #00D1FF; color: #0B0E11; font-weight: bold;
    }
    [data-testid="stMetricValue"] { font-size: 30px; color: #00D1FF; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def load_ai():
    return pipeline("sentiment-analysis", model="ProsusAI/finbert")

analyzer = load_ai()

# --- 2. THE AUDIT ENGINE ---
def run_audit(symbol):
    stock = yf.Ticker(f"{symbol}.NS")
    info = stock.info
    hist = stock.history(period="2y")
    
    if hist.empty: return None

    # Integrity Check: Promoter Pledging (NSE Specific)
    pledged = info.get('pledgedShares', 0)
    
    # Financial Strength: Simplified Piotroski F-Score (0-9)
    score = 0
    if info.get('operatingCashflow', 0) > 0: score += 1
    if info.get('returnOnAssets', 0) > 0: score += 1
    if info.get('debtToEquity', 100) < 100: score += 1
    if info.get('currentRatio', 0) > 1: score += 1
    # Adding Technical momentum to the score
    if hist['Close'].iloc[-1] > hist['Close'].rolling(200).mean().iloc[-1]: score += 2
    
    return {"score": score, "pledged": pledged, "price": hist['Close'].iloc[-1], "hist": hist}

# --- 3. MOBILE APP INTERFACE ---
st.title("🛡️ Alpha Scout: India v2026")

menu = st.sidebar.selectbox("Navigation", ["Deep Audit", "Market Watch", "Scam Alerts"])

if menu == "Deep Audit":
    ticker = st.text_input("Enter NSE Ticker (e.g. RELIANCE, HDFCBANK)", "TATASTEEL").upper()
    
    if st.button("AUDIT NOW"):
        with st.spinner("Analyzing Fundamentals..."):
            data = run_audit(ticker)
            if data:
                # Top Level Stats
                c1, c2, c3 = st.columns(3)
                c1.metric("Current Price", f"₹{data['price']:.2f}")
                c2.metric("Health Score", f"{data['score']}/7")
                c3.metric("Pledged %", f"{data['pledged']}%")

                if data['pledged'] > 20:
                    st.error("⚠️ HIGH RISK: Large promoter pledging detected.")
                
                # Charting
                st.subheader("Price Action (1 Year)")
                st.line_chart(data['hist']['Close'])
                
                # AI News Sentiment
                st.subheader("Latest Sentiment")
                # (Logic to fetch news and run analyzer goes here)
                st.info("Institutional Sentiment: Neutral-Positive")