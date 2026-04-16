import streamlit as st
import json, os
from bot_engine import TradingBot

# إعداد الصفحة ومنع أخطاء الترجمة
st.set_page_config(page_title="AI Futures Trader", layout="wide")
st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;}</style>""", unsafe_allow_html=True)

# دالة لإدارة حفظ المفاتيح في ملف محلي
def manage_keys(action="load", data=None):
    file = "keys_config.json"
    if action == "save":
        with open(file, "w") as f: json.dump(data, f)
    elif os.path.exists(file):
        with open(file, "r") as f: return json.load(f)
    return {"key": "", "secret": ""}

st.title("🤖 Smart Futures Terminal")
saved_keys = manage_keys("load")

# الشريط الجانبي لحفظ البيانات
with st.sidebar:
    st.header("🔑 API Settings")
    api_key = st.text_input("MEXC API Key", value=saved_keys["key"], type="password")
    api_secret = st.text_input("MEXC Secret Key", value=saved_keys["secret"], type="password")
    if st.button("💾 Save & Remember Me"):
        manage_keys("save", {"key": api_key, "secret": api_secret})
        st.success("Keys Saved Safely!")
    st.divider()
    st.info("Limit: $10 - $2500 | Target: 10%")

# تشغيل البوت عند توفر المفاتيح
if api_key and api_secret:
    try:
        bot = TradingBot('mexc', api_key, api_secret)
        balance = bot.get_total_balance()
        
        # عرض العدادات (Metrics)
        col1, col2, col3 = st.columns(3)
        col1.metric("Wallet Balance", f"${balance:.2f}")
        col2.metric("Daily Target", "10%", delta=f"${balance*0.1:.2f}")
        col3.metric("Status", "Active ✅" if "active" in st.session_state else "Standby 💤")

        st.divider()

        # أزرار التحكم
        if st.button("▶️ START AUTO-TRADING (Background)", type="primary", use_container_width=True):
            st.session_state["active"] = True
            st.subheader("📡 Live Market Scanner Activity")
            # تشغيل المحرك
            for log_msg in bot.run_automated_logic(balance):
                st.write(log_msg)
        
        if st.button("🛑 STOP BOT", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    except Exception as e:
        st.error(f"Connection Error: {e}")
else:
    st.warning("👈 Please enter and save your API Keys to view your wallet.")
    
