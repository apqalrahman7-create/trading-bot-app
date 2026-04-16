import streamlit as st
import json, os, random
from datetime import datetime, timedelta

# --- 1. حماية البيانات وقاعدة البيانات ---
def def load_db():
    default = {"activated": False, "api": {"key": "", "secret": "", "exchange": "binance"}, "codes": [], "first_run": "", "messages": []}
    if not os.path.exists('database.json'): return default
    with open('database.json', 'r') as f:
        try: 
            data = json.load(f)
            # إضافة الأقسام الناقصة تلقائياً لمنع الأخطاء
            for key in default:
                if key not in data:
                    data[key] = default[key]
            return data
        except: return defaul
    default = {"activated": False, "api": {"key": "", "secret": ""}, "codes": [], "first_run": "", "messages": []}
    if not os.path.exists('database.json'): return default
    with open('database.json', 'r') as f:
        try: return json.load(f)
        except: return default

def save_db(data):
    with open('database.json', 'w') as f: json.dump(data, f)

st.set_page_config(page_title="AI Trader Pro", layout="wide")
db = load_db()

# --- 2. شاشة تسجيل الدخول (إجبارية) ---
if 'logged_in' not in st.session_state:
    st.title("🔐 AI Trader Login")
    user = st.text_input("Username")
    passw = st.text_input("Password", type="password")
    if st.button("Sign In"):
        if user == "admin" and passw == "123": # يمكنك تغييرها
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("Invalid Credentials")
    st.stop()

# --- 3. نظام الوقت (24 ساعة تجريبية) ---
if not db.get("first_run"):
    db["first_run"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_db(db)

trial_start = datetime.strptime(db["first_run"], "%Y-%m-%d %H:%M:%S")
is_trial_over = datetime.now() - trial_start > timedelta(hours=24)

# --- 4. القائمة والواجهة ---
menu = st.sidebar.radio("Navigation", ["Dashboard", "API Connection", "Support & Admin"])

# --- الشاشة الرئيسية ---
if menu == "Dashboard":
    st.title("🚀 Trading Dashboard")
    
    # جلب الرصيد الحقيقي (مع حماية من الفراغ)
    balance = "0.00"
    if db['api'].get('key') and db['api'].get('secret'):
        try:
            from bot_engine import TradingBot
            bot = TradingBot(db['api'].get('exchange', 'binance').lower(), db['api']['key'], db['api']['secret'])
            balance = f"{bot.get_wallet_balance():,.2f}"
        except: balance = "Connection Error"
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Live Balance", f"${balance}")
    col2.metric("Bot Limit", "$2500")
    col3.metric("Daily Target", "10%")

    st.divider()

    if is_trial_over and not db['activated']:
        st.error("⚠️ Trial Expired! Contact Support for Activation Code.")
        code_in = st.text_input("Enter 6-Digit Code")
        if st.button("Verify Code"):
            if code_in in db.get('codes', []):
                db['activated'] = True
                save_db(db)
                st.success("Activated for 60 Days!")
                st.rerun()
    else:
        st.subheader("Bot Control")
        if st.button("▶️ START AUTO-TRADE (12H)", use_container_width=True):
            if not db['api'].get('key'): st.warning("Please link API first!")
            else: st.success("Bot is running in background...")

# --- شاشة الربط (تمنع الربط الوهمي) ---
elif menu == "API Connection":
    st.title("⚙️ Exchange Settings")
    ex = st.selectbox("Select Exchange", ["Binance", "MEXC"])
    k = st.text_input("API Key")
    s = st.text_input("Secret Key", type="password")
    if st.button("Verify & Link"):
        if not k or not s:
            st.error("❌ Cannot link empty keys!")
        else:
            with st.spinner("Checking..."):
                try:
                    from bot_engine import TradingBot
                    test = TradingBot(ex.lower(), k, s)
                    test.get_wallet_balance() # اختبار حقيقي
                    db['api'] = {"key": k, "secret": s, "exchange": ex}
                    save_db(db)
                    st.success(f"✅ Linked successfully to {ex}")
                except:
                    st.error("❌ Failed: Invalid Keys or Permission Error")

# --- شاشة الدعم والدردشة ولوحة المشرف ---
elif menu == "Support & Admin":
    st.title("🎧 Support & Chat")
    
    # 1. الدردشة (Chat)
    st.subheader("💬 Support Chat")
    chat_msg = st.text_input("Type your message here...")
    if st.button("Send Message"):
        db['messages'].append(f"User: {chat_msg}")
        save_db(db)
    
    for m in db['messages'][-5:]: st.write(m) # عرض آخر 5 رسائل

    st.divider()
    
    # 2. لوحة المشرف (إصدار الرموز)
    st.subheader("👨‍💻 Admin Panel")
    if st.button("✅ Approve & Generate 6-Digit Code"):
        new_c = str(random.randint(100000, 999999))
        db['codes'].append(new_c)
        save_db(db)
        st.success(f"New Code Generated: {new_c}")
        st.info("Give this code to the user for 60-day access.")
    
