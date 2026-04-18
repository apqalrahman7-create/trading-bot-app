import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime, timedelta

# --- 🚀 إعدادات الرادار القوي (تجاوز الأخطاء) ---
SYMBOLS = [
    'ORDI/USDT:USDT', 'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'BNB/USDT:USDT',
    'XRP/USDT:USDT', 'ADA/USDT:USDT', 'AVAX/USDT:USDT', 'DOGE/USDT:USDT', 'DOT/USDT:USDT',
    'SUI/USDT:USDT', 'APT/USDT:USDT', 'OP/USDT:USDT', 'ARB/USDT:USDT', 'NEAR/USDT:USDT'
]

MAX_TRADES = 4
LEVERAGE = 5
FIXED_ENTRY_USDT = 12   # مبلغ ثابت لكل صفقة لتجنب خطأ الرصيد
TRADE_DURATION_MINS = 30

st.set_page_config(page_title="MEXC Sniper Fix", layout="wide")
st.title("🎯 رادار القناص المستقر - MEXC")

if "running" not in st.session_state: st.session_state.running = False
if "trade_times" not in st.session_state: st.session_state.trade_times = {}

with st.sidebar:
    st.header("🔑 إعدادات API")
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 تشغيل الآن"): st.session_state.running = True
    if st.button("🛑 إيقاف"): st.session_state.running = False

log_area = st.empty()
status_cols = st.columns(2)

if st.session_state.running and api_key and api_secret:
    try:
        # اتصال مباشر وتجاوز الطلبات غير المدعومة
        mexc = ccxt.mexc({
            'apiKey': api_key, 'secret': api_secret,
            'options': {'defaultType': 'future'},
            'enableRateLimit': True
        })

        while st.session_state.running:
            # 1. جلب الصفقات المفتوحة (هذه الدالة تعمل دائماً)
            positions = mexc.fetch_positions()
            active_pos = [p for p in positions if float(p['contracts']) != 0]
            current_count = len(active_pos)
            active_syms = [p['symbol'] for p in active_pos]

            status_cols[0].metric("الصفقات النشطة", f"{current_count}/{MAX_TRADES}")
            status_cols[1].write(f"⏱️ آخر فحص: {datetime.now().strftime('%H:%M:%S')}")

            # 2. مسح العملات بحثاً عن صيد
            for symbol in SYMBOLS:
                clean_sym = symbol.replace('/', '').replace(':', '')
                
                # إغلاق زمني بعد 30 دقيقة
                if clean_sym in active_syms and symbol in st.session_state.trade_times:
                    if datetime.now() >= st.session_state.trade_times[symbol] + timedelta(minutes=TRADE_DURATION_MINS):
                        pos = next(p for p in active_pos if p['symbol'] == clean_sym)
                        side = 'sell' if float(pos['contracts']) > 0 else 'buy'
                        mexc.create_market_order(symbol, side, abs(float(pos['contracts'])), params={'reduceOnly': True})
                        del st.session_state.trade_times[symbol]
                        st.toast(f"✅ إغلاق {symbol}")

                # فتح صفقة جديدة
                if clean_sym not in active_syms and current_count < MAX_TRADES:
                    try:
                        ohlcv = mexc.fetch_ohlcv(symbol, timeframe='5m', limit=20)
                        df = pd.DataFrame(ohlcv, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
                        delta = df['c'].diff()
                        rsi = 100 - (100 / (1 + (delta.where(delta > 0, 0).rolling(14).mean() / -delta.where(delta < 0, 0).rolling(14).mean()))).iloc[-1]

                        if rsi <= 30 or rsi >= 70:
                            side = 'buy' if rsi <= 30 else 'sell'
                            mexc.set_leverage(LEVERAGE, symbol, {'openType': 2})
                            mexc.create_market_order(symbol, side, (FIXED_ENTRY_USDT * LEVERAGE) / df['c'].iloc[-1])
                            
                            st.session_state.trade_times[symbol] = datetime.now()
                            current_count += 1
                            st.success(f"🎯 صفقة جديدة: {symbol} (RSI: {rsi:.1f})")
                    except: continue

            time.sleep(20)

    except Exception as e:
        st.error(f"⚠️ تنبيه من المنصة: {e}")
        time.sleep(10)
        
