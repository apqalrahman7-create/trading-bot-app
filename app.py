import streamlit as st
import time
from datetime import datetime, timedelta

# 1. الأساسيات وتصميم الصفحة
st.set_page_config(page_title="Crypto Bot System", layout="wide")

# تهيئة الذاكرة (Session State)
if 'trial_start' not in st.session_state:
    st.session_state['trial_start'] = datetime.now()
if 'is_active' not in st.session_state:
    st.session_state['is_active'] = False
if 'bot_running' not in st.session_state:
    st.session_state['bot_running'] = False

# حساب وقت التجربة (24 ساعة)
trial_expired = datetime.now() - st.session_state['trial_start'] > timedelta(hours=24)

# --- شاشة تسجيل الدخول ---
if not st.session_state.get('logged_in'):
    st.title("🔐 Login")
    user = st.text_input("Username")
    if st.button("Login"):
        st.session_state['logged_in'] = True
        st.rerun()
else:
    # --- القائمة الجانبية (Navigation) ---
    st.sidebar.title("Main Menu")
    menu = st.sidebar.radio("Select Screen:", ["Home (Bot Control)", "Settings (API)", "Customer Service"])

    # 1. شاشة الإعدادات (ربط المنصة أولاً)
    if menu == "Settings (API)":
        st.title("⚙️ Exchange Settings")
        st.info("Connect your exchange via API keys to allow the bot to trade.")
        exchange = st.selectbox("Select Exchange", ["MEXC", "Binance"])
        api_key = st.text_input("API Key")
        secret_key = st.text_input("Secret Key", type="password")
        if st.button("Save & Connect"):
            st.success("Successfully linked to Exchange!")

    # 2. الشاشة الرئيسية (تشغيل البوت)
    elif menu == "Home (Bot Control)":
        st.title("📊 Dashboard")
        
        # عرض الرصيد والأرباح (كما طلبت)
        col1, col2, col3 = st.columns(3)
        col1.metric("Real Balance", "$10,000") # مثال للرصيد الحقيقي
        col2.metric("Today's Profit", "$50")
        col3.metric("Trading Limit", "$2500")

        st.divider()

        # منطق الـ 24 ساعة وطلب الرمز
        if trial_expired and not st.session_state['is_active']:
            st.error("⚠️ 24h Trial Expired! Please request an activation code.")
            code = st.text_input("Enter 6-Digit Code")
            if st.button("Activate Now"):
                # سيتم ربطه بموافقة المشرف لاحقاً
                st.info("Waiting for Admin approval...")
        else:
            c1, c2 = st.columns(2)
            if c1.button("▶️ START BOT", use_container_width=True):
                st.session_state['bot_running'] = True
                st.success("Bot started for 12 hours. Target: $50 profit.")
            
            if c2.button("⏹️ STOP BOT", use_container_width=True):
                st.session_state['bot_running'] = False
                st.warning("Bot has been stopped.")

    # 3. شاشة خدمات العملاء (المجيب الآلي ولوحة المشرف)
    elif menu == "Customer Service":
        st.title("🎧 Customer Support")
        
        # قسم المستخدم
        st.subheader("Contact Support")
        msg = st.text_area("Request Activation Code or Send Message")
        if st.button("Send Request"):
            st.success("Request sent to Admin.")

        st.divider()
        # قسم المشرف (هذا يظهر لك أنت فقط)
        st.subheader("👨‍💻 Admin Panel")
        st.write("Requests waiting for approval:")
        if st.button("✅ Approve Activation (60 Days)"):
            st.success("Bot activated for this user for 60 days via Auto-Reply.")
    
