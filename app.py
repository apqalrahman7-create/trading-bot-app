import streamlit as st
from datetime import datetime, timedelta
import random

# 1. Page Configuration
st.set_page_config(page_title="Pro Trading Bot AI", layout="wide")

# 2. Strategy Rules (Limits)
MAX_TRADING_CAPITAL = 2500.0  # البوت لن يلمس أكثر من هذا المبلغ
MIN_ORDER_SIZE = 10.0         # الحد الأدنى لفتح صفقة

# 3. Initialize Memory
if 'first_login' not in st.session_state:
    st.session_state['first_login'] = datetime.now()
if 'is_verified' not in st.session_state:
    st.session_state['is_verified'] = False
if 'generated_code' not in st.session_state:
    st.session_state['generated_code'] = None

# Trial Logic
time_elapsed = datetime.now() - st.session_state['first_login']
is_trial_over = time_elapsed > timedelta(hours=24)

# 4. Interface
st.sidebar.title("🤖 Control Panel")
menu = st.sidebar.radio("Menu:", ["Dashboard", "Settings", "Admin"])

if menu == "Dashboard":
    st.title("Trading Terminal")
    
    # Wallet Info
    wallet_total = 10000.0 # مثال: إجمالي ما في المحفظة
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Wallet", f"${wallet_total}")
    col2.metric("Bot Trading Limit", f"${MAX_TRADING_CAPITAL}")
    col3.metric("Min Trade", f"${MIN_ORDER_SIZE}")

    st.divider()

    # Execution Logic
    if st.button("▶️ ACTIVATE BOT (12H)", use_container_width=True):
        if is_trial_over and not st.session_state['is_verified']:
            st.error("Trial Expired! Activation Code Required.")
        else:
            st.success(f"Bot Active: Trading using ${MAX_TRADING_CAPITAL} only (Safe Mode).")
            st.info(f"Orders will be placed between ${MIN_ORDER_SIZE} and ${MAX_TRADING_CAPITAL}.")

    if st.button("⏹️ EMERGENCY STOP", use_container_width=True):
        st.warning("Bot Stopped. No new orders will be placed.")

    # Verification Section
    if is_trial_over and not st.session_state['is_verified']:
        st.divider()
        st.subheader("Activation Required")
        input_code = st.text_input("Enter 6-Digit Code:")
        if st.button("Verify"):
            if input_code == st.session_state['generated_code']:
                st.session_state['is_verified'] = True
                st.success("Full Access Granted!")
                st.rerun()

elif menu == "Settings":
    st.title("API Integration")
    st.text_input("API Key")
    st.text_input("Secret Key", type="password")
    st.write(f"⚠️ **Security Note:** The bot is programmed to ignore any capital above ${MAX_TRADING_CAPITAL}.")

elif menu == "Admin":
    st.title("Admin Panel")
    if st.button("Generate Code"):
        new_code = str(random.randint(100000, 999999))
        st.session_state['generated_code'] = new_code
        st.code(new_code)
  
