import streamlit as st
import ccxt
import pandas as pd
import time

# --- ⚙️ إعدادات الأرباح القوية (تقليل الرسوم) ---
SYMBOLS = ['ORDI_USDT', 'BTC_USDT', 'ETH_USDT', 'SOL_USDT']
MAX_TRADES = 4           
LEVERAGE = 5             
ENTRY_AMOUNT_USDT = 15   
TP_TARGET = 0.05         # رفع الهدف لـ 5% (صافي الربح يجب أن يغطي الرسوم)
SL_TARGET = -0.03        # وقف خسارة 3%
TIMEFRAME = '15m'        # فحص شموع الـ 15 دقيقة بدلاً من الدقيقة لتقليل التداول العشوائي

st.title("🛡️ قناص الاتجاه - تقليل الرسوم")

if 'running' not in st.session_state: st.session_state.running = False

with st.sidebar:
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 تشغيل القناص الذكي"): st.session_state.running = True
    if st.button("🛑 إيقاف"): st.session_state.running = False

if st.session_state.running and api_key and api_secret:
    try:
        mexc = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'future'}})
        st.success("✅ تم التشغيل: فحص متأنٍ لتقليل الرسوم")

        while st.session_state.running:
            pos = mexc.fetch_positions()
            active_p = [p['symbol'] for p in pos if float(p.get('contracts', 0)) != 0]
            
            for symbol in SYMBOLS:
                if len(active_p) >= MAX_TRADES: break
                
                if symbol not in active_p:
                    try:
                        # جلب بيانات الـ 15 دقيقة للفحص العميق
                        ohlcv = mexc.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=100)
                        df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                        
                        # حساب المتوسط المتحرك EMA 200 لتحديد الاتجاه
                        df['ema200'] = df['c'].ewm(span=200).mean()
                        current_price = df['c'].iloc[-1]
                        ema_val = df['ema200'].iloc[-1]

                        # شرط الدخول: السعر فوق EMA (اتجاه صاعد) + RSI منخفض (تصحيح)
                        delta = df['c'].diff()
                        rsi = 100 - (100 / (1 + (delta.clip(lower=0).mean() / -delta.clip(upper=0).mean())))

                        if current_price > ema_val and rsi <= 35:
                            qty = (ENTRY_AMOUNT_USDT * LEVERAGE) / current_price
                            formatted_qty = float(mexc.amount_to_precision(symbol, qty))

                            # فتح الصفقة ووضع هدف ربح بعيد (5%) لضمان التفوق على الرسوم
                            mexc.create_market_order(symbol, 'buy', formatted_qty)
                            tp_p = current_price * (1 + TP_TARGET)
                            mexc.create_order(symbol, 'LIMIT', 'sell', formatted_qty, tp_p, {'reduceOnly': True})
                            
                            st.success(f"🎯 قنص اتجاه صاعد لـ {symbol} (هدف 5%)")
                            active_p.append(symbol)
                    except: continue

            time.sleep(60) # فحص كل دقيقة لتقليل الضغط والرسوم

    except Exception as e:
        st.error(f"⚠️ خطأ: {e}")
        time.sleep(20)
        
