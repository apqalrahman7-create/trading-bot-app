import streamlit as st
from bot_engine import TradingBot
import time

# 1. Page Configuration
st.set_page_config(
    page_title="AI Trading Control Center",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI Trading Bot (MEXC)")
st.markdown("---")

# 2. Sidebar Settings
with st.sidebar:
    st.header("🔐 API Settings")
    api_key = st.text_input("Access Key (API Key)", type="password")
    secret_key = st.text_input("Secret Key", type="password")
    st.divider()
    st.info("Ensure 'Futures Trading' is enabled in MEXC.")

# 3. Main Logic
if api_key and secret_key:
    bot = TradingBot('mexc', api_key, secret_key)
    real_balance = bot.get_total_balance()
    
    st.subheader("💰 Live Wallet Status")
    c1, c2 = st.columns(2)
    c1.metric("Total Balance (USDT)", f"${real_balance:.2f}")
    
    if real_balance > 0:
        c2.success("✅ Connected: Balance Detected")
    else:
        c2.warning("⚠️ Connected: Balance is 0.00")

    if 'active' not in st.session_state:
        st.session_state.active = False

    st.markdown("---")
    col1, col2 = st.columns(2)
    
    if col1.button("🚀 START REAL TRADING", type="primary", use_container_width=True):
        if real_balance >= 5:
            st.session_state.active = True
        else:
            st.error("❌ Balance below $5")

    if col2.button("🛑 STOP SESSION", use_container_width=True):
        st.session_state.active = False

    if st.session_state.active:
        st.subheader("📊 Live Logs")
        log_area = st.empty()
        for msg in bot.run_automated_logic(real_balance):
            with log_area.container():
                st.info(msg)
            if not st.session_state.active:
                bot.is_running = False
                break
            time.sleep(1)
else:
    st.warning("👈 Please enter API Keys to start.")
    
