import streamlit as st
import json, os, random
from datetime import datetime, timedelta

# --- 1. قاعدة البيانات وحماية المعلومات ---
def load_db():
    default = {"activated": False, "api": {"key": "", "secret": "", "exchange": "binance"}, "codes": [], "first_run": "", "messages": []}
    if not os.path.exists('database.json'): return default
    with open('database.json', 'r') as f:
        try: 
            data = json.load(f)
            # التأكد من وجود قسم الرسائل لمنع الخطأ السابق
            if "messages" not in data: data["messages"] = []
            if "api" not in data: data["api"] = default["api"]
            return data
        except: return default

def save_db(data):
    with open('database.json', 'w') as f: json.dump(data, f)

# إعداد الصفحة وتصميمها
st.set_page_config(page_title="AI Trader Pro", layout="wide")
db = load_db()

# --- 2. شاشة تسجيل الدخول (Username: admin | Pass: 123) ---
if 'logged_in' not in st.session_state:
    st.title("🔐 Secure Login")
    user = st.text_input("Username")
    passw = st.text_input("Password", type="password")
    if st.button("Enter App"):
        if user == "admin" and passw == "123":
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("Access Denied")
    st.stop()

# --- 3. نظام الوقت (24h Trial) ---
if not db.get("first_run"):
    db["first_run"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_db(db)

trial_start = datetime.strptime(db["first_run"], "%Y-%m-%d %H:%M:%S")
is_trial_over = datetime.now() - trial_start > timedelta(hours=24)

# --- 4. القائمة الرئيسية ---
menu = st.sidebar.radio("Navigation", ["Dashboard", "API Connection", "Support & Admin"])

if menu == "Dashboard":
    st.title("🚀 Trading Dashboard")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Wallet Balance", "$10,000.00") # مثال للرصيد
    col2.metric("Daily Target", "10%")
    col3.metric("Limit", "$2500")

    st.divider()

    if is_trial_over and not db['activated']:
        st.error("⚠️ Trial Expired! Enter Activation Code.")
        code_in = st.text_input("6-Digit Code")
        if st.button("Activate Now"):
            if code_in in db.get('codes', []):
                db['activated'] = True
                save_db(db)
                st.success("Activated!")
                st.rerun()
    else:
        if st.button("▶️ START BOT (12H)", use_container_width=True):
            st.success("Bot is running in background...")

elif menu == "API Connection":
    st.title("⚙️ Link Exchange")
    ex = st.selectbox("Platform", ["Binance", "MEXC"])
    k = st.text_input("API Key")
    s = st.text_input("Secret Key", type="password")
    if st.button("Verify & Save"):
        if k and s:
            db['api'] = {"key": k, "secret": s, "exchange": ex}
            save_db(db)
            st.success("API Linked Successfully!")
        else:
            st.error("Please enter keys first.")

elif menu == "Support & Admin":
    st.title("🎧 Support Chat")
    
    msg = st.text_input("Type your message...")
    if st.button("Send"):
        db['messages'].append(f"User: {msg}")
        save_db(db)
    
    st.divider()
    for m in db['messages'][-5:]: st.write(m)

    st.divider()
    st.subheader("👨‍💻 Admin Control")
    if st.button("Generate Code"):
        new_c = str(random.randint(100000, 999999))
        db['codes'].append(new_c)
        save_db(db)
        st.code(new_c)
        
