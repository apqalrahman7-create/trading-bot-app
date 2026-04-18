import streamlit as st
import ccxt
import pandas as pd
import time

# --- الإعدادات ---
SYMBOL = 'ORDI/USDT:USDT'
LEVERAGE = 5
ENTRY_AMOUNT = 15

st.set_page_config(page_title="Global Sniper", layout="wide")
st.title("🌎 قناص عالمي محترف - ORDI")

# 1. إعداد واجهة التحكم (تظهر أولاً)
with st.sidebar:
    st.header("🔑 الإعدادات")
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    st.divider()
    col1, col2 = st.columns(2)
    start_btn = col1.button("🚀 تشغيل")
    stop_btn = col2.button("🛑 إيقاف")

if "running" not in st.session_state:
    st.session_state.running = False

if start_btn: st.session_state.running = True
if stop_btn: st.session_state.running = False

# 2. منطقة عرض البيانات
status_area = st.empty()
log_area = st.container()

# 3. محرك التداول (يعمل فقط عند الضغط على تشغيل)
if st.session_state.running:
    if not api_key or not api_secret:
        st.error("يرجى إدخال المفاتيح أولاً!")
    else:
        try:
            mexc = ccxt.mexc({
                'apiKey': api_key, 'secret': api_secret,
                'options': {'defaultType': 'future'}, 'enableRateLimit': True
            })
            
            st.success("المحرك يعمل الآن... جاري فحص الفرص")
            
            while st.session_state.running:
                # جلب البيانات
                ohlcv = mexc.fetch_ohlcv(SYMBOL, timeframe='5m', limit=50)
                df = pd.DataFrame(ohlcv, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
                
                # حساب RSI بسيط
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]
                price = df['close'].iloc[-1]

                # فحص الصفقات
                positions = mexc.fetch_positions([SYMBOL])
                has_pos = any(float(p['contracts']) != 0 for p in positions)

                with status_area.container():
                    st.metric("السعر الحالي", f"{price} USDT", f"RSI: {rsi:.2f}")
                    st.info(f"حالة الحساب: {'يوجد صفقة مفتوحة' if has_pos else 'جاري البحث عن فرصة...'}")

                # منطق الدخول
                if not has_pos:
                    if rsi <= 32:
                        mexc.create_market_buy_order(SYMBOL, ENTRY_AMOUNT/price)
                        st.toast("🎯 تم فتح صفقة شراء!")
                    elif rsi >= 68:
                        mexc.create_market_sell_order(SYMBOL, ENTRY_AMOUNT/price)
                        st.toast("🎯 تم فتح صفقة بيع!")

                time.sleep(10)
                
        except Exception as e:
            st.error(f"خطأ: {e}")
            st.session_state.running = False
else:
    st.warning("البوت متوقف حالياً. اضغط على 'تشغيل' من القائمة الجانبية للبدء.")

