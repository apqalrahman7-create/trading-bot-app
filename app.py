import streamlit as st
from bot_engine import TradingBot
import time

# --- 1. UI Configuration ---
st.set_page_config(
    page_title="AI Trading Control Center",
    page_icon="🤖",
    layout="wide"
)

# Header Section
st.title("🤖 AI Trading Bot Control Panel (MEXC)")
st.markdown("---")

# --- 2. Sidebar (API Settings) ---
with st.sidebar:
    st.header("🔐 Account Settings")
    st.write("Enter your API credentials below:")
    api_key = st.text_input("Access Key (API Key)", type="password")
    secret_key = st.text_input("Secret Key", type="password")
    
    st.divider()
    st.info("Make sure 'Futures Trading' permission is enabled in your MEXC API settings.")

# --- 3. Main Dashboard Logic ---
if api_key and secret_key:
    # Initialize Bot Engine
    bot = TradingBot('mexc', api_key, secret_key)
    
    # Fetch Real-Time Balance (The function that worked for you before)
    real_balance = bot.get_total_balance()
    
    # Display Balance Metrics
    st.subheader("💰 Live Wallet Status")
    col_bal, col_status = st.columns(2)
    
    with col_bal:
        st.metric("Total Available Balance (USDT)", f"${real_balance:.2f}")
    
    with col_status:
        if real_balance > 0:
            st.success("✅ Connected: Balance Detected")
        else:
            st.warning("⚠️ Connected: Balance is 0.00 (Check Futures Wallet)")

    st.markdown("---")

    # Control Buttons
    if 'is_active' not in st.session_state:
        st.session_state.is_active = False

    btn_start, btn_stop = st.columns(2)
    
    with btn_start:
        if st.button("🚀 START REAL TRADING", type="primary", use_container_width=True):
            if real_balance >= 5: # Minimum trade limit
                st.session_state.is_active = True
            else:
                st.error("❌ Cannot Start: Balance below $5")

    with btn_stop:
        if st.button("🛑 STOP SESSION", use_container_width=True):
            st.session_state.is_active = False
            st.warning("Stop command sent to Bot.")

    # --- 4. Live Operation Logs ---
    if st.session_state.is_active:
        st.subheader("📊 Live Trading Logs")
        log_area = st.empty()
        
        # Run the trading loop from bot_engine
        for message in bot.run_automated_logic(real_balance):
            with log_area.container():
                st.info(message)
            
            # Check if user clicked STOP
            if not st.session_state.is_active:
                bot.is_running = False
                break
            
            time.sleep(1)
else:
    st.warning("👈 Please enter your API Keys in the sidebar to activate the bot.")

st.markdown("---")
st.caption("Note: This bot is programmed to run for a 12-hour session to achieve a 10% profit target.")
