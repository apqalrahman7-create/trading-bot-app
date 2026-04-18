import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime, timedelta

# --- 🚀 إعدادات الرادار النشط ---
SYMBOLS = [
    'ORDI/USDT:USDT', 'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'BNB/USDT:USDT',
    'XRP/USDT:USDT', 'ADA/USDT:USDT', 'AVAX/USDT:USDT', 'DOGE/USDT:USDT', 'DOT/USDT:USDT',
    'SUI/USDT:USDT', 'APT/USDT:USDT', 'OP/USDT:USDT', 'ARB/USDT:USDT', 'NEAR/USDT:USDT'
]

MAX_TRADES = 4
LEVERAGE = 5
FIXED_ENTRY_USDT = 12 
TRADE_DURATION_MINS = 30

st.set_page_config(page_title="Active Sniper Pro", layout="wide")
st.title("🔥 قناص MEXC النشط جداً - 40 عملة")

if "running" not in st.session_state: st.session_state.running = False
if "trade_log" not in st.session_state: st.session_state.trade_log = []
if "start_times" not in st.session_state: st.session_state.start_times = {}

with st.sidebar:
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 تشغيل محرك القنص"): st.session_state.running = True
    if st.button("🛑 إيقاف"): st.session_state.running = False

status_placeholder = st.empty()

if st.session_state.running and api_key and api_secret:
    try:
        # اتصال احترافي مع ضبط معاملات MEXC
        mexc = ccxt.mexc({
            'apiKey': api_key,
            'secret': api_secret,
            'options': {'defaultType': 'future'},
            'enableRateLimit': True
        })

        while st.session_state.running:
            # 1. فحص الصفقات المفتوحة فعلياً في المنصة
            try:
                positions = mexc.fetch_positions()
                active_positions = [p for p in positions if float(p['contracts']) != 0]
                current_count = len(active_positions)
                active_symbols = [p['symbol'] for p in active_positions]
            except:
                active_symbols = []
                current_count = 0

            status_placeholder.info(f"🔎 الرادار يعمل.. صفقات نشطة: {current_count}/{MAX_TRADES}")

            # 2. مسح العملات لفتح صفقات
            for symbol in SYMBOLS:
                if not st.session_state.running: break
                
                clean_sym = symbol.replace('/', '').replace(':', '')
                
                # --- منطق الإغلاق الزمني (30 دقيقة) ---
                if clean_sym in active_symbols and symbol in st.session_state.start_times:
                    if datetime.now() >= st.session_state.start_times[symbol] + timedelta(minutes=TRADE_DURATION_MINS):
                        pos = next(p for p in active_positions if p['symbol'] == clean_sym)
                        side = 'sell' if float(pos['contracts']) > 0 else 'buy'
                        # إغلاق باستخدام Reduce Only
                        mexc.create_market_order(symbol, side, abs(float(pos['contracts'])), {'reduceOnly': True})
                        del st.session_state.start_times[symbol]
                        st.toast(f"✅ تم إغلاق {symbol} زمنياً")

                # --- منطق الدخول النشط ---
                if clean_sym not in active_symbols and current_count < MAX_TRADES:
                    try:
                        ohlcv = mexc.fetch_ohlcv(symbol, timeframe='3m', limit=20)
                        df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                        
                        # حساب RSI سريع
                        delta = df['c'].diff()
                        up = delta.clip(lower=0).rolling(14).mean()
                        down = -delta.clip(upper=0).rolling(14).mean()
                        rsi = 100 - (100 / (1 + (up / down))).iloc[-1]

                        # شروط دخول نشطة جداً (35 و 65) لضمان العمل
                        if rsi <= 35 or rsi >= 65:
                            side = 'buy' if rsi <= 35 else 'sell'
                            
                            # تنفيذ الأمر مع معاملات MEXC الإجبارية
                            amount = (FIXED_ENTRY_USDT * LEVERAGE) / df['c'].iloc[-1]
                            mexc.create_market_order(symbol, side, amount)
                            
                            st.session_state.start_times[symbol] = datetime.now()
                            current_count += 1
                            st.success(f"🎯 قنص ناجح: {symbol} | RSI: {rsi:.1f}")
                    except:
                        continue

            time.sleep(10) # فحص سريع

    except Exception as e:
        st.error(f"⚠️ خطأ: {e}")
        time.sleep(20)
        
