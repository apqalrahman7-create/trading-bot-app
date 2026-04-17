import streamlit as st
from bot_engine import TradingBot
import time

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="AI Trading Control Center",
    page_icon="🤖",
    layout="wide"
)

# Application Header
st.title("🤖 AI Trading Bot Control Panel (MEXC)")
st.markdown("---")

# --- 2. Sidebar Configuration (API Keys) ---
with st.sidebar:
    st.header("🔐 Connection Settings")
    st.write("Enter your MEXC API credentials:")
    api_key = st.text_input("Access Key (API Key)", type="password")
    secret_key = st.text_input("Secret Key", type="password")
    
    st.divider()
    st.info("Note: The bot will trade in the wallet where funds (USDT) are available.")

# --- 3. Main Dashboard Logic ---
if api_key and secret_key:
    # Initialize the trading engine
    bot = TradingBot('mexc', api_key, secret_key)
    
    # Fetch real-time balance from the bot engine
    current_balance = bot.get_total_balance()
    
    # Display Balance Metrics
    st.subheader("💰 Live Portfolio Status")
    col_bal, col_status = st.columns(2)
    
    with col_bal:
        st.metric("Total Real-Time Balance (USDT)", f"${current_balance:.2f}")
    
    with col_status:
        if current_balance > 0:
            st.success("✅ Connection Active: Balance Found")
        else:
            st.warning("⚠️ Connected: Balance is $0.00 (Check Spot/Futures Wallet)")

    st.markdown("---")

    # Bot Control State
    if 'is_active' not in st.session_state:
        st.session_state.is_active = False

    # Control Buttons
    btn_start, btn_stop = st.columns(2)
    
    with btn_start:
        if st.button("🚀 START AUTOMATED TRADING", type="primary", use_container_width=True):
            if current_balance >= 5: # Minimum exchange requirement
                st.session_state.is_active = True
            else:
                st.error("❌ Error: Insufficient balance ($5 minimum required)")

    with btn_stop:
        if st.button("🛑 STOP SESSION", use_container_width=True):
            st.session_state.is_active = False
            st.warning("Stop command issued to the engine.")

    # --- 4. Live Operation Logs ---
    if st.session_state.is_active:
        st.subheader("📊 Live Trading Logs")
        log_area = st.empty()
        
        # Start the trading cycle from bot_engine
        for message in bot.run_automated_logic(current_balance):
            with log_area.container():
                st.info(message)
            
            # Check for manual stop
            if not st.session_state.is_active:
                bot.is_running = False
                break
            
            # Allow for UI refresh
            time.sleep(1)
else:
    # Prompt for credentials
    st.warning("👈 Please enter your API Keys in the sidebar to activate the control panel.")
    
