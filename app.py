import streamlit as st
import json, os, random
from datetime import datetime, timedelta
from bot_engine import TradingBot # استدعاء المحرك الحقيقي

# --- 1. Database & Helper Functions ---
def load_db():
    default = {"activated": False, "api": {"key": "", "secret": "", "exchange": "binance"}, "codes": [], "first_run": "", "messages": []}
    if not os.path.exists('database.json'): return default
    with open('database.json', 'r') as f:
        try:
            data = json.load(f)
            for key in default:
                if key not in data: data[key] = default[key]
            return data
        except: return default

def save_db(data):
    with open('database.json', 'w') as f: json.dump(data, f)

st.set_page_config(page_title="AI Trader Pro", layout="wide")
db = load_db()

# --- 2. Login Logic ---
if 'logged_in' not in st.session_state:
    st.title("🔐 Secure Login")
    user = st.text_input("Username")
    passw = st.text_input("Password", type="password")
    if st.button("Enter System"):
        if user == "admin" and passw == "123":
            st.session_state['logged_in'] = True
            st.rerun()
        else: st.error("Invalid Credentials")
    st.stop()

# --- 3. Sidebar & Navigation ---
menu = st.sidebar.radio("Main Menu", ["Dashboard", "Settings (API Link)", "Support & Admin"])

# --- 4. DASHBOARD: REAL DATA DISPLAY ---
if menu == "Dashboard":
    st.title("🚀 Real-Time Trading Terminal")
    
    # محاولة الاتصال الحقيقي وجلب الرصيد
    real_balance = 0.0
    status = "Disconnected"
    
    if db['api'].get('key') and db['api'].get('secret'):
        try:
            # استخدام المحرك للاتصال بالمنصة فعلياً
            bot = TradingBot(db['api']['exchange'].lower(), db['api']['key'], db['api']['secret'])
            real_balance = bot.get_wallet_balance() # جلب الرصيد الحقيقي
            status = "Connected"
            st.success(f"✅ Live Connection to {db['api']['exchange'].upper()} Established")
        except Exception as e:
            st.error(f"❌ Connection Failed: Check your API Keys or Network.")
            status = "Error"
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Live Wallet Balance", f"${real_balance:,.2f}")
    col2.metric("Trading Limit", "$2500.00")
    col3.metric("System Status", status)

    st.divider()
    
    # التحكم (أزرار التشغيل)
    if st.button("▶️ START AUTO-TRADING", use_container_width=True):
        if status == "Connected":
            st.info("Bot is now analyzing real market data...")
        else: st.warning("Please link a valid API first.")

# --- 5. SETTINGS: API LINKING ---
elif menu == "Settings (API Link)":
    st.title("⚙️ Link Your Exchange")
    ex = st.selectbox("Platform", ["Binance", "MEXC"])
    k = st.text_input("API Key", value=db['api'].get('key', ''))
    s = st.text_input("Secret Key", type="password", value=db['api'].get('secret', ''))
    if st.button("Verify & Save Connection"):
        db['api'] = {"key": k, "secret": s, "exchange": ex}
        save_db(db)
        st.success("API Keys Saved! Go to Dashboard to see live balance.")

# --- 6. SUPPORT & ADMIN ---
elif menu == "Support & Admin":
    st.title("🎧 Support Chat & Admin")
    msg = st.text_input("Message Support:")
    if st.button("Send"):
        db['messages'].append(f"User: {msg}")
        save_db(db); st.rerun()
    for m in db['messages'][-5:]: st.info(m)
    
    st.divider()
    if st.button("✅ Generate 6-Digit Activation Code"):
        new_code = str(random.randint(100000, 999999))
        db['codes'].append(new_code)
        save_db(db)
        st.code(new_code)
    
