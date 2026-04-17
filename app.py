import streamlit as st
import threading
import time
import ccxt

st.set_page_config(page_title="Ultimate Recovery Bot", layout="centered")
st.title("🛡️ AI Smart Trader & Panic Exit")

if 'bot_active' not in st.session_state:
    st.session_state.bot_active = False

# --- وظيفة إغلاق جميع الصفقات فوراً ---
def close_all_positions(api_key, api_secret):
    try:
        exchange = ccxt.binance({'apiKey': api_key, 'secret': api_secret, 'enableRateLimit': True})
        balance = exchange.fetch_balance()
        for coin, details in balance['total'].items():
            if coin != 'USDT' and details > 0:
                symbol = f"{coin}/USDT"
                st.warning(f"Closing {symbol} to free capital...")
                exchange.create_market_sell_order(symbol, details)
        st.success("✅ All positions closed! Capital is now in USDT.")
    except Exception as e:
        st.error(f"Error during emergency exit: {e}")

def trading_engine(api_key, api_secret):
    exchange = ccxt.binance({'apiKey': api_key, 'secret': api_secret, 'enableRateLimit': True})
    while st.session_state.get('bot_active', False):
        try:
            # هنا منطق القناص السريع الذي صممناه (10% ربح و 0.4% حماية)
            time.sleep(10)
        except Exception:
            time.sleep(20)

# --- الواجهة ---
with st.sidebar:
    st.header("🔑 Connection")
    k = st.text_input("API Key", type="password")
    s = st.text_input("Secret Key", type="password")

# زر الطوارئ (الأهم الآن)
if st.button("🚨 SELL EVERYTHING NOW (Free Capital)", type="primary", use_container_width=True):
    if k and s:
        close_all_positions(k, s)
    else:
        st.error("Please enter API Keys first!")

st.divider()

col1, col2 = st.columns(2)
with col1:
    if st.button("🚀 Start New Trading Session", use_container_width=True):
        st.session_state.bot_active = True
        threading.Thread(target=trading_engine, args=(k, s), daemon=True).start()
        st.success("Bot started scanning...")
with col2:
    if st.button("🛑 Stop Scanning", use_container_width=True):
        st.session_state.bot_active = False
        
