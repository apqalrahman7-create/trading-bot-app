import streamlit as st
from bot_engine import TradingBot
import time

st.set_page_config(page_title="MEXC AI BOT", layout="wide")
st.title("🤖 منصة التداول الآلي الذكية")

# إدخال المفاتيح في الشاشة الرئيسية
with st.expander("🔐 إعدادات API (ادخل مفاتيحك هنا)", expanded=True):
    col_a, col_b = st.columns(2)
    api = col_a.text_input("API Key", type="password")
    sec = col_b.text_input("Secret Key", type="password")

if api and sec:
    bot = TradingBot('mexc', api, sec)
    res_bal = bot.get_total_balance()
    
    # عرض الرصيد فوراً
    st.metric("رصيدك الحقيقي في MEXC", f"${res_bal:.2f} USDT")

    if 'active' not in st.session_state: st.session_state.active = False

    col1, col2 = st.columns(2)
    if col1.button("🚀 ابدأ التداول التلقائي", type="primary", use_container_width=True):
        st.session_state.active = True
    
    if col2.button("🛑 إيقاف فوري", use_container_width=True):
        st.session_state.active = False

    if st.session_state.active:
        if res_bal > 5:
            st.success("🔄 البوت يعمل الآن ويراقب السوق...")
            log_area = st.empty()
            for msg in bot.run_automated_logic(res_bal):
                with log_area.container(): st.write(msg)
                if not st.session_state.active: break
                time.sleep(1)
        else:
            st.error("⚠️ الرصيد صفر أو أقل من 5$ - تأكد من وجود USDT في محفظة Futures")
else:
    st.warning("👈 يرجى إدخال مفاتيح الـ API في الصندوق أعلاه لتفعيل الأزرار.")
    
