import streamlit as st
import threading
import time
import ccxt

# --- APP SETUP ---
st.set_page_config(page_title="MEXC AI Sniper", layout="centered")
st.title("🛡️ بوت القناص الذكي - منصة MEXC")

if 'bot_active' not in st.session_state:
    st.session_state.bot_active = False

# --- وظيفة إغلاق جميع الصفقات في MEXC ---
def close_all_mexc_positions(api_key, api_secret):
    try:
        # الاتصال بمنصة MEXC
        exchange = ccxt.mexc({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })
        balance = exchange.fetch_balance()
        for coin, details in balance['total'].items():
            if coin != 'USDT' and details > 0:
                symbol = f"{coin}/USDT"
                st.warning(f"جاري إغلاق {symbol} لتحرير رأس المال...")
                exchange.create_market_sell_order(symbol, details)
        st.success("✅ تم إغلاق جميع الصفقات! الرصيد الآن بالكامل USDT.")
    except Exception as e:
        st.error(f"خطأ في الاتصال بمنصة MEXC: {e}")

# --- محرك التداول الآلي ---
def trading_engine_mexc(api_key, api_secret):
    exchange = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'enableRateLimit': True})
    while st.session_state.get('bot_active', False):
        try:
            # هنا منطق القناص (تحليل الشموع + الربح التراكمي + حماية 0.4%)
            time.sleep(10)
        except Exception:
            time.sleep(20)

# --- الواجهة ---
with st.sidebar:
    st.header("🔑 إعدادات MEXC")
    k = st.text_input("MEXC API Key", type="password")
    s = st.text_input("MEXC Secret Key", type="password")

# زر الطوارئ المخصص لـ MEXC
if st.button("🚨 بيع كل شيء الآن (تحرير USDT)", type="primary", use_container_width=True):
    if k and s:
        close_all_mexc_positions(k, s)
    else:
        st.error("يرجى إدخال مفاتيح الـ API الخاصة بمنصة MEXC أولاً!")

st.divider()

col1, col2 = st.columns(2)
with col1:
    if st.button("🚀 بدء التداول الآلي", use_container_width=True):
        st.session_state.bot_active = True
        threading.Thread(target=trading_engine_mexc, args=(k, s), daemon=True).start()
        st.success("بدأ البوت بمسح سوق MEXC...")
with col2:
    if st.button("🛑 إيقاف البوت", use_container_width=True):
        st.session_state.bot_active = False
        
