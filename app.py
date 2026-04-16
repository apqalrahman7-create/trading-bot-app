import streamlit as st
from bot_engine import TradingBot

# إعداد الصفحة وتجنب أخطاء الترجمة
st.set_page_config(page_title="AI Trader Pro", layout="wide")
st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;}</style>""", unsafe_allow_html=True)

st.title("🤖 AI Market Scanner & Trader")
st.write("Current Status: **Direct Access Enabled (No Password)**")

# إدخال مفاتيح الـ API في الشريط الجانبي
with st.sidebar:
    st.header("🔑 Connection Settings")
    api_key = st.text_input("MEXC API Key", type="password")
    api_secret = st.text_input("MEXC Secret Key", type="password")
    st.divider()
    st.info("Limit: $10 - $2500 | Target: 10%")

if api_key and api_secret:
    try:
        bot = TradingBot('mexc', api_key, api_secret)
        balance = bot.get_total_balance()
        
        if balance >= 10:
            st.success(f"✅ Connected! Balance: ${balance}")
            
            if st.button("▶️ START AUTO-TRADING", use_container_width=True):
                st.divider()
                st.subheader("Live Market Activity")
                # تشغيل البوت وعرض النتائج مباشرة
                for msg in bot.run_automated_logic(balance):
                    st.write(msg)
        else:
            st.warning(f"Low Balance: ${balance}. Min $10 required.")
    except Exception as e:
        st.error(f"Connection Error: {e}")
else:
    st.info("💡 Please enter your API Keys to link your wallet.")
    
