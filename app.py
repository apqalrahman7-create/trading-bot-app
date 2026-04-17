import streamlit as st
from bot_engine import TradingBot
import time

st.set_page_config(page_title="MEXC Real Trader", layout="wide")
st.title("🤖 بوت التداول المباشر والأرباح")

# لوحة المفاتيح
with st.sidebar:
    st.header("⚙️ الإعدادات")
    api = st.text_input("API Key", type="password")
    sec = st.text_input("Secret Key", type="password")

if api and sec:
    bot = TradingBot('mexc', api, sec)
    res_bal = bot.get_total_balance()
    
    # عرض الرصيد الحقيقي (المربع الذي كان يظهر لك)
    st.metric("إجمالي رصيد المحفظة الحقيقي", f"${res_bal:.2f} USDT")

    if 'active' not in st.session_state: st.session_state.active = False

    col1, col2 = st.columns(2)
    if col1.button("▶️ ابدأ التداول الحقيقي الآن", type="primary", use_container_width=True):
        st.session_state.active = True
    
    if col2.button("🛑 إيقاف وحفظ الأرباح", use_container_width=True):
        st.session_state.active = False

    if st.session_state.active and res_bal > 0:
        log_area = st.empty()
        for msg in bot.run_automated_logic(res_bal):
            with log_area.container():
                st.write(msg)
            if not st.session_state.active: break
    elif res_bal == 0:
        st.warning("⚠️ الرصيد يظهر 0.00 - تأكد من وجود عملات في محفظة الـ Futures بـ MEXC.")
else:
    st.info("👈 أدخل مفاتيح الـ API في القائمة الجانبية ليظهر رصيدك.")
    
