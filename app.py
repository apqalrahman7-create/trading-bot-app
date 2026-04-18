import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime, timedelta

# --- 🚀 الإعدادات النشطة (Active Trading) ---
SYMBOLS = ['ORDI_USDT', 'BTC_USDT', 'ETH_USDT', 'SOL_USDT', 'XRP_USDT', 'ADA_USDT', 'SUI_USDT', 'PEPE_USDT']
MAX_TRADES = 4
LEVERAGE = 5
FIXED_AMOUNT = 12 # مبلغ الدخول بالدولار

st.set_page_config(page_title="Active Sniper", layout="wide")
st.title("🔥 قناص MEXC النشط (فحص وتداول)")

if 'running' not in st.session_state: st.session_state.running = False
if 'trades' not in st.session_state: st.session_state.trades = {}

with st.sidebar:
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 تشغيل التداول"): st.session_state.running = True
    if st.button("🛑 إيقاف"): st.session_state.running = False

status_log = st.empty()

if st.session_state.running and api_key and api_secret:
    try:
        mexc = ccxt.mexc({
            'apiKey': api_key, 'secret': api_secret,
            'options': {'defaultType': 'swap'}, 'enableRateLimit': True
        })

        while st.session_state.running:
            # 1. فحص الصفقات المفتوحة
            pos = mexc.fetch_positions()
            active_list = [p['symbol'] for p in pos if float(p.get('contracts', 0)) != 0]
            current_count = len(active_list)
            
            status_log.info(f"🔎 جاري الفحص.. صفقات نشطة: {current_count}/{MAX_TRADES} | الوقت: {datetime.now().strftime('%H:%M:%S')}")

            for symbol in SYMBOLS:
                # أ. منطق الإغلاق (بعد 30 دقيقة)
                if symbol in active_list and symbol in st.session_state.trades:
                    if datetime.now() >= st.session_state.trades[symbol] + timedelta(minutes=30):
                        mexc.create_market_order(symbol, 'sell', 0, {'reduceOnly': True})
                        del st.session_state.trades[symbol]
                        st.toast(f"✅ تم إغلاق {symbol}")

                # ب. منطق التداول الفوري (شروط أسهل للدخول)
                if symbol not in active_list and current_count < MAX_TRADES:
                    try:
                        ohlcv = mexc.fetch_ohlcv(symbol, timeframe='1m', limit=20)
                        df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                        
                        # حساب RSI سريع (1 دقيقة) لضمان كثرة الصفقات
                        delta = df['c'].diff()
                        rsi = 100 - (100 / (1 + (delta.clip(lower=0).mean() / -delta.clip(upper=0).mean())))

                        # شروط دخول "نشطة جداً" (40 و 60) لضمان بدء التداول
                        if rsi <= 40 or rsi >= 60:
                            side = 'buy' if rsi <= 40 else 'sell'
                            price = df['c'].iloc[-1]
                            qty = (FIXED_AMOUNT * LEVERAGE) / price
                            
                            # تنفيذ أمر السوق
                            mexc.create_market_order(symbol, side, qty)
                            st.session_state.trades[symbol] = datetime.now()
                            current_count += 1
                            st.success(f"🎯 تم فتح صفقة {side} على {symbol} (RSI: {rsi:.1f})")
                    except: continue

            time.sleep(10) # فحص سريع كل 10 ثوانٍ

    except Exception as e:
        st.error(f"⚠️ خطأ: {e}")
        time.sleep(10)
        
