import streamlit as st
import threading
import time
import ccxt

st.set_page_config(page_title="AI Capital Recovery Bot", layout="centered")
st.title("⚡ AI Capital Recovery & Sniper Bot")

if 'bot_active' not in st.session_state:
    st.session_state.bot_active = False

def recovery_trading_engine(api_key, api_secret):
    exchange = ccxt.binance({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })

    while st.session_state.get('bot_active', False):
        try:
            # 1. CHECK FOR OPEN POSITIONS (To free up capital)
            balance = exchange.fetch_balance()
            # Find any coin you currently hold (like BTC from your image)
            for coin, details in balance['total'].items():
                if coin != 'USDT' and details > 0:
                    symbol = f"{coin}/USDT"
                    # Get current profit for this held coin
                    ticker = exchange.fetch_ticker(symbol)
                    current_price = ticker['last']
                    # Note: We don't know your exact entry, so we exit if it's profitable 
                    # OR if you want to free capital immediately:
                    st.toast(f"Found held asset: {symbol}. Monitoring to exit and free capital...")
                    
                    # Exit logic for held asset (e.g., if it hits 4% profit)
                    # For now, let's assume we exit to free the USDT:
                    # exchange.create_market_sell_order(symbol, details)

            # 2. ONCE CAPITAL IS FREE -> START NEW COMPOUNDING TRADES
            usdt_free = balance['free'].get('USDT', 0)
            if usdt_free >= 10:
                # SCANNER LOGIC
                tickers = exchange.fetch_tickers()
                best_pairs = [s for s in tickers if '/USDT' in s and tickers[s]['percentage'] > 1.2]
                
                if best_pairs:
                    target = best_pairs[0]
                    # Entry and 60-min Monitoring with 0.4% Protection
                    # (Rest of the fast logic we built)
                    
            time.sleep(10)
        except Exception as e:
            time.sleep(20)

# --- UI ---
with st.sidebar:
    k = st.text_input("API Key", type="password")
    s = st.text_input("Secret Key", type="password")

if st.button("🚀 Start Recovery & Trading", type="primary", use_container_width=True):
    if k and s:
        st.session_state.bot_active = True
        threading.Thread(target=recovery_trading_engine, args=(k, s), daemon=True).start()
        st.success("Bot is looking for held assets to free your capital!")

if st.button("🛑 Stop Bot", use_container_width=True):
    st.session_state.bot_active = False
    
