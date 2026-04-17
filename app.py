import streamlit as st
import pandas as pd
from pymexc import spot
import time

# --- إعدادات الصفحة ---
st.set_page_config(page_title="AI Trading Bot", layout="wide")
st.title("🤖 بوت التداول الذكي - MEXC")

# --- المدخلات (مفاتيح API) ---
with st.sidebar:
    st.header("إعدادات الاتصال")
    api_key = st.text_input("API Key", type="password")
    secret_key = st.text_input("Secret Key", type="password")
    symbol = st.text_input("العملة (مثلاً BTCUSDT)", value="BTCUSDT")
    trade_amount = st.number_input("مبلغ التداول ($)", min_value=5, value=10)

# --- الاتصال بالمنصة ---
if api_key and secret_key:
    client = spot.HTTP(api_key=api_key, api_secret=secret_key)
else:
    st.warning("يرجى إدخال مفاتيح الـ API في القائمة الجانبية.")
    st.stop()

# --- واجهة العرض الرئيسية ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("💰 الرصيد الحالي")
    if st.button("تحديث الرصيد"):
        acc = client.account_info()
        balances = [b for b in acc['balances'] if float(b['free']) > 0]
        st.table(balances)

with col2:
    st.subheader("📈 مراقبة السوق")
    status_placeholder = st.empty()
    price_placeholder = st.empty()

# --- زر التشغيل الرئيسي ---
if st.button("🚀 تشغيل البوت الآن"):
    st.success(f"تم تفعيل البوت على زوج {symbol}")
    
    # حلقة تشغيل البوت
    while True:
        try:
            ticker = client.ticker_price(symbol)
            current_price = float(ticker['price'])
            
            price_placeholder.metric(label=f"سعر {symbol} الآن", value=f"${current_price}")
            
            # --- هنا يتدخل الذكاء الاصطناعي الخاص بك لاتخاذ القرار ---
            # مثال: قرر الذكاء الاصطناعي الشراء (AI_DECISION == "BUY")
            
            status_placeholder.info("البوت يحلل البيانات حالياً...")
            time.sleep(5) # فحص كل 5 ثوانٍ
            
        except Exception as e:
            st.error(f"خطأ: {e}")
            break
            
