import streamlit as st
import ccxt
import pandas as pd
import time

# --- 🚀 إعدادات القناص (بدون دالة الرصيد) ---
SYMBOLS = ['ORDI_USDT', 'BTC_USDT', 'ETH_USDT', 'SOL_USDT', 'XRP_USDT', 'SUI_USDT']
MAX_TRADES = 5           
LEVERAGE = 5             
# حدد هنا المبلغ الذي تريد الدخول به في كل صفقة (مثلاً 12 دولار)
ENTRY_AMOUNT_USDT = 12   

st.set_page_config(page_title="MEXC No-Error Bot", layout="wide")
st.title("🎯 قناص MEXC المستقر (بدون أخطاء)")

if 'running' not in st.session_state: st.session_state.running = False

with st.sidebar:
    st.header("⚙️ الإعدادات")
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 تشغيل إجباري"): st.session_state.running = True
    if st.button("🛑 إيقاف"): st.session_state.running = False

# --- المحرك الرئيسي ---
if st.session_state.running and api_key and api_secret:
    try:
        # الاتصال المباشر
        mexc = ccxt.mexc({
            'apiKey': api_key, 
            'secret': api_secret, 
            'options': {'defaultType': 'future'},
            'enableRateLimit': True
        })

        st.success("✅ تم الاتصال بنجاح! الرادار يمسح السوق الآن..")

        while st.session_state.running:
            # 1. جلب الصفقات المفتوحة (هذه الدالة تعمل دائماً)
            pos = mexc.fetch_positions()
            active_p = [p for p in pos if float(p.get('contracts', 0)) != 0]
            current_count = len(active_p)
            active_names = [p['symbol'] for p in active_p]

            st.info(f"🔎 الصفقات النشطة: {current_count}/{MAX_TRADES}")

            for symbol in SYMBOLS:
                if current_count >= MAX_TRADES: break
                
                if symbol not in active_names:
                    try:
                        # فحص سريع لفتح الصفقة
                        ohlcv = mexc.fetch_ohlcv(symbol, timeframe='1m', limit=20)
                        df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                        price = df['c'].iloc[-1]
                        
                        # حساب RSI مبسط
                        delta = df['c'].diff()
                        rsi = 100 - (100 / (1 + (delta.clip(lower=0).mean() / -delta.clip(upper=0).mean())))

                        if rsi <= 35 or rsi >= 65:
                            side = 'buy' if rsi <= 35 else 'sell'
                            
                            # حساب الكمية بناءً على المبلغ الثابت
                            qty = (ENTRY_AMOUNT_USDT * LEVERAGE) / price
                            formatted_qty = float(mexc.amount_to_precision(symbol, qty))

                            # تنفيذ الصفقة مباشرة
                            mexc.create_market_order(symbol, side, formatted_qty)
                            st.success(f"🎯 تم قنص {symbol} بنجاح!")
                            current_count += 1
                    except: continue

            time.sleep(20) # مهلة لراحة المتصفح

    except Exception as e:
        st.error(f"⚠️ تنبيه فني: {e}")
        time.sleep(10)
        
