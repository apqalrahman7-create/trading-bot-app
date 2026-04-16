import streamlit as st
import json
import os
import random
from datetime import datetime, timedelta
from bot_engine import TradingBot

# 1. Setup & Data Persistence
def load_db():
    if os.path.exists('database.json'):
        with open('database.json', 'r') as f: return json.load(f)
    return {"activated": False, "expiry": "", "api": {}, "codes": []}

def save_db(data):
    with open('database.json', 'w') as f: json.dump(data, f)

st.set_page_config(page_title="AI Trading System", layout="wide")
db = load_db()

# 2. Session Management
if 'start_time' not in st.session_state:
    st.session_state['start_time'] = datetime.now()
trial_over = datetime.now() - st.session_state['start_time'] > timedelta(hours=24)

# --- LOGIN SCREEN ---
if 'auth' not in st.session_state:
    st.title("🔐 System Login")
    if st.button("Enter App"):
        st.session_state['auth'] = True
        st.rerun()
else:
    # --- MAIN NAVIGATION ---
    menu = st.sidebar.radio("Menu", ["Dashboard", "Settings (API)", "Customer Service"])

    # SCREEN 1: SETTINGS (API CONNECTION)
    if menu == "Settings (API)":
        st.title("⚙️ Exchange Connection")
        st.info("Link your Binance or MEXC keys here.")
        api_key = st.text_input("API Key", value=db['api'].get('key', ''))
        secret_key = st.text_input("Secret Key", type="password", value=db['api'].get('secret', ''))
        if st.button("Save & Link"):
            db['api'] = {'key': api_key, 'secret': secret_key}
            save_db(db)
            st.success("Platform Linked!")

    # SCREEN 2: DASHBOARD (BOT CONTROL)
    elif menu == "Dashboard":
        st.title("🚀 Trading Dashboard")
        col1, col2, col3 = st.columns(3)
        col1.metric("Wallet Balance", "$10,000") # Simulated
        col2.metric("Today's Profit", "$50")
        col3.metric("Trade Limit", "$2500")

        st.divider()

        # 24h Trial & Activation Logic
        if trial_over and not db['activated']:
            st.error("⚠️ 24h Trial Ended. Enter Activation Code.")
            code_input = st.text_input("Enter 6-Digit Code")
            if st.button("Activate"):
                if code_input in db['codes']:
                    db['activated'] = True
                    db['expiry'] = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
                    save_db(db)
                    st.success("Activated for 60 Days!")
                    st.rerun()
        else:
            c1, c2 = st.columns(2)
            if c1.button("▶️ START BOT (12H)", use_container_width=True):
                st.success("Bot is analyzing market... Target: 10% Profit.")
            if c2.button("⏹️ STOP BOT", use_container_width=True):
                st.warning("Stopping... Returning capital and profits to wallet.")

    # SCREEN 3: CUSTOMER SERVICE (ADMIN)
    elif menu == "Customer Service":
        st.title("🎧 Support & Admin")
        st.subheader("User Request")
        if st.button("Request Activation Code"):
            st.info("Request sent to Admin.")

        st.divider()
        st.subheader("👨‍💻 Admin Panel (Auto-Responder)")
        if st.button("Approve & Send 6-Digit Code"):
            new_code = str(random.randint(100000, 999999))
            db['codes'].append(new_code)
            save_db(db)
            st.code(new_code)
            st.success("Auto-Responder: Activation code generated for 60 days.")
                
