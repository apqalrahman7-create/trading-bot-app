import streamlit as st
import ccxt
import pandas as pd
import time

# --- 🚀 قائمة الرادار النشط ---
SYMBOLS = ['ORDI_USDT', 'BTC_USDT', 'ETH_USDT', 'SOL_USDT', 'XRP_USDT', 'SUI_USDT']
MAX_TRADES = 4
LEVERAGE = 5
ENTRY_AMOUNT = 12

st.set_page_config(page_title="Active Market Sniper", layout="wide")
st.title("📡 رادار تحليل وقنص السوق - MEXC")

if 'running' not in st.session_state: st.session_state.running = False

with st.sidebar:
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 تشغيل المحرك"): st.session_state.running = True
    if st.button("🛑 إيقاف"): st.session_state.running = False

# مناطق عرض التحليل الحي
analysis_area = st.empty()
log_area = st.container()

if st.session_state.running and api_key and api_secret:
    try:
        mexc = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'future'}})
        
        while st.session_state.running:
            # جلب الصفقات الحالية
            pos = mexc.fetch_positions()
            active_list = [p['symbol'] for p in pos if float(p.get('contracts', 0)) != 0]
            
            # --- لوحة التحليل الحي ---
            with analysis_area.container():
                st.subheader("📊 تحليل العملات الحالي")
                cols = st.columns(len(SYMBOLS))
                
                for i, symbol in enumerate(SYMBOLS):
                    try:
                        ohlcv = mexc.fetch_ohlcv(symbol, timeframe='5m', limit=50)
                        df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                        
                        # الحسابات
                        current_p = df['c'].iloc[-1]
                        ema = df['c'].ewm(span=50).mean().iloc[-1] # متوسط سريع للتحليل
                        delta = df['c'].diff()
                        rsi = 100 - (100 / (1 + (delta.clip(lower=0).mean() / -delta.clip(upper=0).mean())))
                        
                        # العرض في الأعمدة
                        cols[i].write(f"**{symbol.split('_')[0]}**")
                        cols[i].metric("السعر", f"{current_p}")
                        cols[i].write(f"RSI: {rsi:.1f}")
                        cols[i].write("📈" if current_p > ema else "📉")

                        # --- منطق القنص الفوري ---
                        if symbol not in active_list and len(active_list) < MAX_TRADES:
                            if rsi <= 40: # شرط الشراء
                                qty = (ENTRY_AMOUNT * LEVERAGE) / current_p
                                mexc.create_market_order(symbol, 'buy', float(mexc.amount_to_precision(symbol, qty)))
                                st.toast(f"🎯 تم قنص شراء {symbol}")
                            elif rsi >= 60: # شرط البيع
                                qty = (ENTRY_AMOUNT * LEVERAGE) / current_p
                                mexc.create_market_order(symbol, 'sell', float(mexc.amount_to_precision(symbol, qty)))
                                st.toast(f"🎯 تم قنص بيع {symbol}")
                    except: continue

            time.sleep(15) # فحص وتحليل كل 15 ثانية

    except Exception as e:
        st.error(f"⚠️ خطأ: {e}")
        time.sleep(10)
        
