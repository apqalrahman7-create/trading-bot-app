import streamlit as st
from bot_engine import TradingBot
import time

st.set_page_config(page_title="MEXC AI BOT", layout="wide")
st.title("🤖 مركز تحكم بوت MEXC")

# إدخال المفاتيح مباشرة في واجهة التطبيق
with st.sidebar:
    st.header("🔑 إعدادات API")
    api = st.text_input("API Key", type="password")
    sec = st.text_input("Secret Key", type="password")

if api and sec:
    bot = TradingBot('mexc', api, sec)
    res_bal = bot.get_total_balance()
    
    # عرض الرصيد فوراً
    st.metric("رصيد المحفظة (USDT)", f"${res_bal:.2f}")

    if 'active' not in st.session_state: st.session_state.active = False

    col1, col2 = st.columns(2)
    if col1.button("🚀 ابدأ التداول الآن", type="primary", use_container_width=True):
        st.session_state.active = True
    
    if col2.button("🛑 إيقاف الجلسة", use_container_width=True):
        st.session_state.active = False

    if st.session_state.active:
        if res_bal > 5:
            log_area = st.empty()
            for msg in bot.run_automated_logic(res_bal):
                with log_area.container(): st.write(msg)
                if not st.session_state.active: break
        else:
            st.error("⚠️ الرصيد صفر! تأكد من وجود USDT في محفظة Futures بـ MEXC.")
else:
    st.warning("👈 يرجى إدخال API Key و Secret Key في القائمة الجانبية.")
    
