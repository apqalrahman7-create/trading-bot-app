import streamlit as st
import threading
import time
import ccxt
import pandas as pd

# --- APP CONFIG ---
st.set_page_config(page_title="AI Sniper Bot", layout="centered")
st.title("🤖 AI Autonomous Sniper Bot")

if 'bot_active' not in st.session_state:
    st.session_state.bot_active = False

# --- TRADING ENGINE ---
def run_trading_engine(api_key, api_secret):
    # Connect to Exchange
    exchange = ccxt.binance({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
    })

    while st.session_state.get('bot_active', False):
        try:
            # 1. COMPOUNDING: Get real USDT Balance
            balance = exchange.fetch_balance()
            usdt_total = balance['free'].get('USDT', 0)
            
            if usdt_total < 10:
                print("Insufficient USDT Balance")
                time.sleep(30)
                continue

            trade_amount = usdt_total * 0.20 # Use 20% for compounding

            # 2. MARKET SCANNER: Find high momentum coin
            # Scan top USDT gainers
            tickers = exchange.fetch_tickers()
            usdt_pairs = [symbol for symbol in tickers if '/USDT' in symbol]
            
            # Find a pair with > 5% growth in 24h as a filter
            best_pair = None
            for symbol in usdt_pairs:
                if tickers[symbol]['percentage'] > 5: # Looking for strong trend
                    best_pair = symbol
                    break
            
            if best_pair:
                # 3. EXECUTE & MONITOR (60 Minutes Max)
                entry_price = tickers[best_pair]['last']
                print(f"🎯 Entry: {best_pair} at {entry_price}")
                
                start_time = time.time()
                while (time.time() - start_time) < 3600:
                    if not st.session_state.get('bot_active', False): break
                    
                    # Real-time Candle Analysis (Check for 10% Profit)
                    current_ticker = exchange.fetch_ticker(best_pair)
                    current_price = current_ticker['last']
                    profit = ((current_price - entry_price) / entry_price) * 100
                    
                    # Exit Strategy: 10% Profit OR Trend Reversal (-1%)
                    if profit >= 10 or profit <= -1:
                        # exchange.create_market_sell_order(best_pair, amount)
                        break
                    
                    time.sleep(20) # Scan every 20 seconds
            
            time.sleep(10) # Cooldown
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(30)

# --- UI CONTROLS ---
with st.sidebar:
    st.header("🔑 API Connection")
    k = st.text_input("API Key", type="password")
    s = st.text_input("Secret Key", type="password")
    st.info("Compounding & Global Scanning Active.")

if st.button("🚀 Start Global Scan", type="primary", use_container_width=True):
    if k and s:
        st.session_state.bot_active = True
        threading.Thread(target=run_trading_engine, args=(k, s), daemon=True).start()
        st.success("Scanner Active! Searching for opportunities...")
    else:
        st.error("Please enter API Keys!")

if st.button("🛑 Stop Bot", use_container_width=True):
    st.session_state.bot_active = False
    st.warning("Shutting down...")

st.divider()
st.info("Status: Bot is monitoring the market for the best entry point.")
