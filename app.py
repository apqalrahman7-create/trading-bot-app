import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة والأزرار (تظهر أولاً دائماً) ---
st.set_page_config(page_title="AI Sniper 12h", layout="centered")
st.title("⚡ AI Sniper - MEXC")

# إدارة الحالة
if 'running' not in st.session_state:
    st.session_state.running = False
if 'total_profit' not in st.session_state:
    st.session_state.total_profit = 0.0

# القائمة الجانبية
st.sidebar.header("⚙️ التحكم")
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

col1, col2 = st.sidebar.columns(2)
btn_start = col1.button("🚀 تشغيل")
btn_stop = col2.button("🛑 إيقاف")

# تحديث الحالة بناءً على الضغط
if btn_start:
    st.session_state.running = True
if btn_stop:
    st.session_state.running = False

# --- 2. عرض المؤشرات ---
m1, m2 = st.columns(2)
m1.metric("الربح الحالي", f"${st.session_state.total_profit:.2f}")
status_text = st.empty()

# --- 3. منطق التداول (يعمل فقط إذا كانت الحالة True) ---
if st.session_state.running:
    if not api_key or not api_secret:
        st.error("⚠️ من فضلك أدخل مفاتيح API أولاً")
        st.session_state.running = False
    else:
        try:
            # الاتصال بالمنصة
            ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'enableRateLimit': True})
            status_text.success("✅ البوت متصل ويبحث عن فرص...")
            
            # جلب العملات (مرة واحدة لتوفير الوقت)
            markets = ex.load_markets()
            symbols = [s for s in markets if '/USDT' in s and markets[s]['active']]
            
            # حلقة التداول
            while st.session_state.running:
                for symbol in symbols[:50]: # فحص أول 50 عملة نشطة لتجنب التعليق
                    if not st.session_state.running: break
                    
                    try:
                        ticker = ex.fetch_ticker(symbol)
                        # شرط شراء بسيط (صعود أكثر من 3%)
                        if ticker['percentage'] > 3.0:
                            status_text.warning(f"🎯 اكتشاف حركة في {symbol}.. محاولة دخول")
                            
                            # تنفيذ صفقة تجريبية بـ 11 دولار
                            price = ticker['last']
                            amount = 11.0 / price
                            p_amount = ex.amount_to_precision(symbol, amount)
                            
                            order = ex.create_market_buy_order(symbol, p_amount)
                            st.write(f"✅ تم شراء {symbol} بسعر {price}")
                            
                            # انتظار الربح 1.5%
                            time.sleep(5) 
                            # (هنا يمكن إضافة كود المراقبة المستمرة)
                            
                    except Exception as e:
                        continue
                
                time.sleep(2) # راحة قصيرة
                st.rerun() # تحديث الصفحة لرؤية النتائج

        except Exception as e:
            st.error(f"❌ حدث خطأ: {e}")
            st.session_state.running = False
else:
    status_text.info("البوت متوقف حالياً. اضغط 'تشغيل' للبدء.")
    
