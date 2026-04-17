import streamlit as st
from bot_engine import TradingBot
import time

st.set_page_config(page_title="MEXC BOT", layout="wide")

st.title("🤖 AI Trading Bot (MEXC)")

with st.sidebar:
    st.header("🔐 API Settings")
    api_key = st.text_input("API Key", type="password")
    secret_key = st.text_input("Secret Key", type="password")

if api_key and secret_key:
    bot = TradingBot('mexc', api_key, secret_key)
    balance = bot.get_total_balance()
    
    st.metric("Total Balance (USDT)", f"${balance:.2f}")

    if 'active' not in st.session_state:
        st.session_state.active = False

    c1, c2 = st.columns(2)
    if c1.button("🚀 START"):
        st.session_state.active = True
    if c2.button("🛑 STOP"):
        st.session_state.active = False

    if st.session_state.active:
        log_area = st.empty()
        for msg in bot.run_automated_logic(balance):
            log_area.info(msg)
            if not st.session_state.active:
                break
            time.sleep(1)
else:
    st.warning("Enter API Keys to start.")
    
