import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime, timedelta

# --- الإعدادات الفنية ---
PROFIT_GOAL_USD = 5.0   # الهدف (10% من الـ 50$)
TRADE_AMOUNT = 12.0     # مبلغ الصفقة الواحدة
TAKE_PROFIT = 1.015     # هدف الربح 1.5%
STOP_LOSS = 0.985       # إيقاف الخسارة 1.5%

st.set_page_config(page_title="AI Sniper 12h", page_icon="⚡")
st.title("⚡ AI Sniper - دورة الـ 12 ساعة")

# إدارة حالة التشغيل
if 'running' not in st.session_state:
    st.session_state.running = False
if 'total_profit' not in st.session_state:
    st.session_state.total_profit = 0.0

# القائمة الجانبية للإعدادات
st.sidebar.header("🔑 إعدادات الوصول")
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

# أزرار التحكم
col1, col2 = st.sidebar.columns(2)
if col1.button("🚀 تشغيل", use_container_width=True):
    st.session_state.running = True
if col2.button("🛑 إيقاف", use_container_width=True):
    st.session_state.running = False

# منطقة العرض الرئيسية
status_placeholder = st.empty()
metrics_col1, metrics_col2 = st.columns(2)
log_area = st.container()

if st.session_state.running:
    if not api_key or not api_secret:
        st.error("الرجاء إدخال الـ API Keys في القائمة الجانبية!")
        st.session_state.running = False
    else:
        try:
            ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'enableRateLimit': True})
            markets = ex.load_markets()
            # جلب أزواج USDT النشطة فقط
            symbols = [s for s in markets if '/USDT' in s and markets[s]['active']]
            
            start_time = datetime.now()
            end_time = start_time + timedelta(hours=12)

            while st.session_state.running:
                # 1. تحديث المؤشرات
                time_left = end_time - datetime.now()
                if time_left.total_seconds() <= 0:
                    st.success("✅ انتهت دورة الـ 12 ساعة!")
                    st.session_state.running = False
                    break

                metrics_col1.metric("الربح المحقق", f"${st.session_state.total_profit:.2f}")
                metrics_col2.metric("الوقت المتبقي", str(time_left).split('.')[0])

                # 2. البحث عن صفقات (مسح سريع)
                for symbol in symbols:
                    if not st.session_state.running: break
                    
                    try:
                        ticker = ex.fetch_ticker(symbol)
                        # استراتيجية: قنص العملات التي بدأت تتحرك بقوة صعودية
                        if ticker['percentage'] > 2.0: 
                            status_placeholder.info(f"🔍 فحص فرصة في {symbol}...")
                            
                            price = ticker['last']
                            amount = TRADE_AMOUNT / price
                            p_amount = ex.amount_to_precision(symbol, amount)
                            
                            # تنفيذ الشراء
                            order = ex.create_market_buy_order(symbol, p_amount)
                            with log_area:
                                st.write(f"🎯 تم شراء {symbol} بسعر {price}")
                            
                            # مراقبة الصفقة (Loop داخلي سريع للبيع)
                            while True:
                                curr = ex.fetch_ticker(symbol)['last']
                                if curr >= price * TAKE_PROFIT:
                                    # بيع بربح
                                    bal = ex.fetch_balance()[symbol.split('/')]['free']
                                    ex.create_market_sell_order(symbol, ex.amount_to_precision(symbol, bal))
                                    st.session_state.total_profit += (curr - price) * amount
                                    st.toast(f"✅ ربح من {symbol}!")
                                    break
                                elif curr <= price * STOP_LOSS:
                                    # بيع بخسارة
                                    bal = ex.fetch_balance()[symbol.split('/')]['free']
                                    ex.create_market_sell_order(symbol, ex.amount_to_precision(symbol, bal))
                                    st.session_state.total_profit -= (price - curr) * amount
                                    break
                                time.sleep(1)
                            
                            if st.session_state.total_profit >= PROFIT_GOAL_USD:
                                st.balloons()
                                st.session_state.running = False
                                break
                    except:
                        continue
                
                time.sleep(5) # راحة بين دورات المسح

        except Exception as e:
            st.error(f"❌ خطأ: {e}")
            st.session_state.running = False

else:
    status_placeholder.warning("⚠️ البوت متوقف حالياً. اضغط 'تشغيل' للبدء.")
    
