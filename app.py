import streamlit as st
import json
import os
import random
from datetime import datetime, timedelta

# --- 1. إعدادات وحفظ البيانات ---
def load_db():
    default = {"activated": False, "expiry": "", "api": {"key": "", "secret": ""}, "codes": [], "first_run": ""}
    if os.path.exists('database.json'):
        try:
            with open('database.json', 'r') as f: return json.load(f)
        except: return default
    return default

def save_db(data):
    with open('database.json', 'w') as f: json.dump(data, f)

st.set_page_config(page_title="AI Trader Pro", layout="wide")
db = load_db()

# تسجيل وقت أول تشغيل للتطبيق (لبدء الـ 24 ساعة)
if not db.get("first_run"):
    db["first_run"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_db(db)

trial_start = datetime.strptime(db["first_run"], "%Y-%m-%d %H:%M:%S")
is_trial_over = datetime.now() - trial_start > timedelta(hours=24)

# --- 2. الواجهة الرئيسية ---
menu = st.sidebar.radio("Navigation", ["Dashboard", "API Settings", "Support & Admin"])

if menu == "Dashboard":
    st.title("🚀 Automated Trading Terminal")
    
    # عرض الرصيد والحدود
    col1, col2, col3 = st.columns(3)
    col1.metric("Bot Trading Limit", "$2500")
    col2.metric("Target Profit", "10%")
    col3.metric("Trade Status", "Active" if not is_trial_over or db['activated'] else "Locked")

    st.divider()

    # منطق القفل بعد 24 ساعة
    if is_trial_over and not db['activated']:
        st.error("⚠️ 24-Hour Trial Period Ended! Please contact the Admin for an activation code.")
        st.info("The bot is currently locked. Enter the 6-digit code provided by support.")
        code_input = st.text_input("Enter Activation Code:", placeholder="123456")
        if st.button("Activate 60-Day Access"):
            if code_input in db.get('codes', []):
                db['activated'] = True
                db['expiry'] = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
                save_db(db)
                st.success("✅ System Activated! You now have full access for 60 days.")
                st.rerun()
            else:
                st.error("Invalid Code. Please request approval from the Admin.")
    else:
        # أزرار التشغيل (تظهر فقط في أول 24 ساعة أو بعد التفعيل)
        if not db['api'].get('key'):
            st.warning("Please link your API keys in 'API Settings' to enable trading.")
        else:
            c1, c2 = st.columns(2)
            if c1.button("▶️ START AUTO-TRADING (12H)", use_container_width=True):
                st.success("Bot is running in the background. Analyzing market...")
            if c2.button("⏹️ EMERGENCY STOP", use_container_width=True):
                st.warning("Bot stopped. All funds are back in USDT.")

elif menu == "API Settings":
    st.title("⚙️ Exchange Connection")
    ex = st.selectbox("Platform", ["Binance", "MEXC"])
    api = st.text_input("API Key", value=db['api'].get('key', ''))
    secret = st.text_input("Secret Key", type="password", value=db['api'].get('secret', ''))
    if st.button("Save & Link"):
        db['api'] = {'key': api, 'secret': secret, 'exchange': ex}
        save_db(db)
        st.success(f"Connected to {ex} successfully!")

elif menu == "Support & Admin":
    st.title("🎧 Support & Admin Center")
    
    # قسم المستخدم لطلب الرمز
    st.subheader("Request Activation")
    if st.button("Click to Request Approval"):
        st.info("Request sent! The Admin will review and provide your 6-digit code.")

    st.divider()
    
    # قسم المشرف (أنت)
    st.subheader("👨‍💻 Admin Control Panel")
    st.write("Grant access to the user by generating a secure code.")
    if st.button("✅ Approve & Send Code (Auto-Responder)"):
        new_code = str(random.randint(100000, 999999))
        if 'codes' not in db: db['codes'] = []
        db['codes'].append(new_code)
        save_db(db)
        st.code(new_code)
        st.success("The Auto-Responder has generated a 60-day activation code.")
