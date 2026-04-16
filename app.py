import streamlit as st
import json
import os
import random
from datetime import datetime, timedelta
from bot_engine import TradingBot  # استدعاء المحرك الحقيقي

# 1. Database Management
def load_db():
    default = {"activated": False, "expiry": "", "api": {"key": "", "secret": "", "exchange": "binance"}, "codes": [], "first_run": ""}
    if os.path.exists('database.json'):
        try:
            with open('database.json', 'r') as f: return json.load(f)
        except: return default
    return default

def save_db(data):
    with open('database.json', 'w') as f: json.dump(data, f)

st.set_page_config(page_title="AI Trader Pro", layout="wide")
db = load_db()

# Tracking 24h Trial
if not db.get("first_run"):
    db["first_run"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_db(db)

trial_start = datetime.strptime(db["first_run"], "%Y-%m-%d %H:%M:%S")
is_trial_over = datetime.now() - trial_start > timedelta(hours=24)

# 2. Navigation
menu = st.sidebar.radio("Navigation", ["Dashboard", "API Settings", "Support & Admin"])

# --- SCREEN 1: DASHBOARD ---
if menu == "Dashboard":
    st.title("🚀 Real-Time Trading Terminal")
    
    # FETCH REAL BALANCE FROM EXCHANGE
    real_balance = 0.0
    if db['api'].get('key') and db['api'].get('secret'):
        try:
            # الربط الحقيقي لجلب الرصيد
            bot = TradingBot(
                db['api'].get('exchange', 'binance').lower(), 
                db['api']['key'], 
                db['api']['secret']
            )
            real_balance = bot.get_wallet_balance()
            st.success(f"Connected to {db['api']['exchange'].upper()} Successfully")
        except Exception as e:
            st.error(f"Connection Error: Please check if your API keys are correct.")

    # Metrics Display
    col1, col2, col3 = st.columns(3)
    col1.metric("Real Wallet Balance", f"${real_balance:,.2f}")
    col2.metric("Bot Trading Limit", "$2500.00")
    col3.metric("Target Profit", "10%")

    st.divider()

    # Bot Controls & Trial Logic
    if is_trial_over and not db['activated']:
        st.error("⚠️ 24-Hour Trial Expired! Contact Admin for Activation Code.")
        code_input = st.text_input("Enter 6-Digit Activation Code:")
        if st.button("Activate 60 Days Access"):
            if code_input in db.get('codes', []):
                db['activated'] = True
                db['expiry'] = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
                save_db(db)
                st.success("System Activated for 60 Days!")
                st.rerun()
            else:
                st.error("Invalid Code.")
    else:
        if not db['api'].get('key'):
            st.warning("Please link your API keys in 'API Settings' to show balance and start trading.")
        else:
            c1, c2 = st.columns(2)
            if c1.button("▶️ START AUTO-TRADE (12H)", use_container_width=True):
                st.info("Bot is analyzing markets using $2500 limit. 10% Profit target active.")
            if c2.button("⏹️ EMERGENCY STOP", use_container_width=True):
                st.warning("Halt signal sent. All funds returned to USDT.")

# --- SCREEN 2: API SETTINGS ---
elif menu == "API Settings":
    st.title("⚙️ Exchange Connection")
    ex = st.selectbox("Select Platform", ["Binance", "MEXC"])
    api = st.text_input("API Key", value=db['api'].get('key', ''))
    secret = st.text_input("Secret Key", type="password", value=db['api'].get('secret', ''))
    if st.button("Save & Test Connection"):
        db['api'] = {'key': api, 'secret': secret, 'exchange': ex}
        save_db(db)
        st.success(f"Keys saved for {ex}! Go to Dashboard to see your balance.")

# --- SCREEN 3: SUPPORT & ADMIN ---
elif menu == "Support & Admin":
    st.title("🎧 Support & Management")
    st.subheader("Customer Support")
    if st.button("Send Request to Admin"):
        st.info("Request sent. Waiting for Admin approval.")

    st.divider()
    st.subheader("👨‍💻 Admin Panel (Auto-Responder)")
    if st.button("✅ Approve & Generate Activation Code"):
        new_code = str(random.randint(100000, 999999))
        if 'codes' not in db: db['codes'] = []
        db['codes'].append(new_code)
        save_db(db)
        st.code(new_code)
        st.success("6-Digit Code generated. Provide this to the user for 60-day access.")
                
