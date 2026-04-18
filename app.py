import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime, timedelta

# --- 🚀 إعدادات الرادار المتأني (3 Minutes Sniper) ---
SYMBOLS = [
    'ORDI/USDT:USDT', 'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'BNB/USDT:USDT',
    'XRP/USDT:USDT', 'ADA/USDT:USDT', 'AVAX/USDT:USDT', 'DOGE/USDT:USDT', 'DOT/USDT:USDT',
    'LINK/USDT:USDT', 'SUI/USDT:USDT', 'APT/USDT:USDT', 'OP/USDT:USDT', 'ARB/USDT:USDT'
    # يمكنك إضافة بقية الـ 40 عملة هنا
]

MAX_TRADES = 4
LEVERAGE = 5
FIXED_ENTRY_USDT = 12 
TRADE_DURATION_MINS = 30
TIMEFRAME = '3m'  # تم تغيير الفحص ليكون بناءً على شمعة الـ 3 دقائق

st.set_page_config(page_title="Slow & Steady Sniper", layout="wide")
st.title("🎯 قناص الفحص المتأني (إطار 3 دقائق)")

if "running" not in st.session_state: st.session_state.running = False
if "trade_times" not in st.session_state: st.session_state.trade_times = {}

with st.sidebar:
    st.header("🔑 الإعدادات")
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 بدء الفحص المتأني"): st.session_state.running = True
    if st.button("🛑 إيقاف"): st.session_state.running = False

status_area = st.empty()

if st.session_state.running and api_key and api_secret:
    try:
        mexc = ccxt.mexc({
            'apiKey': api_key, 'secret': api_secret,
            'options': {'defaultType': 'future'}, 'enableRateLimit': True
        })

        while st.session_state.running:
            # 1. فحص الصفقات النشطة
            positions = mexc.fetch_positions()
            active_pos = [p for p in positions if float(p['contracts']) != 0]
            current_count = len(active_pos)
            active_syms = [p['symbol'] for p in active_pos]

            with status_area.container():
                st.info(f"🛰️ الرادار يمسح الآن بإطار {TIMEFRAME}.. الصفقات: {current_count}/{MAX_TRADES}")

            # 2. دورة المسح
            for symbol in SYMBOLS:
                clean_sym = symbol.replace('/', '').replace(':', '')
                
                # إغلاق زمني (30 دقيقة)
                if clean_sym in active_syms and symbol in st.session_state.trade_times:
                    if datetime.now() >= st.session_state.trade_times[symbol] + timedelta(minutes=TRADE_DURATION_MINS):
                        pos = next(p for p in active_pos if p['symbol'] == clean_sym)
                        side = 'sell' if float(pos['contracts']) > 0 else 'buy'
                        mexc.create_market_order(symbol, side, abs(float(pos['contracts'])), params={'reduceOnly': True})
                        del st.session_state.trade_times[symbol]
                        st.toast(f"✅ تم إغلاق {symbol}")

                # فتح صفقة جديدة بناءً على فحص الـ 3 دقائق
                if clean_sym not in active_syms and current_count < MAX_TRADES:
                    try:
                        # جلب شمعات الـ 3 دقائق
                        ohlcv = mexc.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=30)
                        df = pd.DataFrame(ohlcv, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
                        
                        # حساب RSI (تأكيد الاتجاه)
                        delta = df['c'].diff()
                        rsi = 100 - (100 / (1 + (delta.where(delta > 0, 0).rolling(14).mean() / -delta.where(delta < 0, 0).rolling(14).mean()))).iloc[-1]

                        # شروط دخول "متأنية"
                        if rsi <= 30 or rsi >= 70:
                            side = 'buy' if rsi <= 30 else 'sell'
                            mexc.set_leverage(LEVERAGE, symbol, {'openType': 2})
                            mexc.create_market_order(symbol, side, (FIXED_ENTRY_USDT * LEVERAGE) / df['c'].iloc[-1])
                            
                            st.session_state.trade_times[symbol] = datetime.now()
                            current_count += 1
                            st.success(f"🎯 قنص متأني (3m): {symbol} | RSI: {rsi:.1f}")
                    except: continue

            time.sleep(30) # انتظار 30 ثانية قبل دورة المسح التالية لتقليل الضغط

    except Exception as e:
        st.error(f"⚠️ تنبيه: {e}")
        time.sleep(20)
        
