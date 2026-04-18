import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime, timedelta

# --- 🚀 إعدادات الرادار (15 عملة قوية) ---
SYMBOLS = [
    'ORDI_USDT', 'BTC_USDT', 'ETH_USDT', 'SOL_USDT', 'BNB_USDT', 'XRP_USDT',
    'ADA_USDT', 'DOGE_USDT', 'SUI_USDT', 'APT_USDT', 'OP_USDT', 'ARB_USDT',
    'LINK_USDT', 'NEAR_USDT', 'PEPE_USDT'
]

MAX_TRADES = 4
LEVERAGE = 5
FIXED_AMOUNT_USDT = 10  # دخول بمبلغ ثابت لتجنب خطأ الرصيد
TRADE_DURATION = 30 

st.set_page_config(page_title="MEXC Sniper Fix", layout="wide")
st.title("🎯 قناص MEXC المستقر")

if 'running' not in st.session_state: st.session_state.running = False
if 'trade_times' not in st.session_state: st.session_state.trade_times = {}

with st.sidebar:
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 تشغيل المحرك"): st.session_state.running = True
    if st.button("🛑 إيقاف"): st.session_state.running = False

# --- المحرك الرئيسي (بدون دالة fetchBalance) ---
if st.session_state.running and api_key and api_secret:
    try:
        mexc = ccxt.mexc({
            'apiKey': api_key,
            'secret': api_secret,
            'options': {'defaultType': 'swap'},
            'enableRateLimit': True
        })

        while st.session_state.running:
            # 1. فحص الصفقات المفتوحة (هذه الدالة تعمل دائماً)
            positions = mexc.fetch_positions()
            active_p = [p for p in positions if float(p.get('contracts', 0)) != 0]
            current_count = len(active_p)
            active_names = [p['symbol'] for p in active_p]

            st.info(f"🛰️ الرادار يفحص الآن.. الصفقات المفتوحة: {current_count}/{MAX_TRADES}")

            for symbol in SYMBOLS:
                # إغلاق زمني بعد 30 دقيقة
                if symbol in active_names and symbol in st.session_state.trade_times:
                    if datetime.now() >= st.session_state.trade_times[symbol] + timedelta(minutes=TRADE_DURATION):
                        try:
                            mexc.create_market_order(symbol, 'sell', 0, {'reduceOnly': True})
                            del st.session_state.trade_times[symbol]
                            st.toast(f"✅ تم إغلاق {symbol}")
                        except: pass

                # فتح صفقة جديدة بناءً على RSI (إطار 3 دقائق)
                if symbol not in active_names and current_count < MAX_TRADES:
                    try:
                        ohlcv = mexc.fetch_ohlcv(symbol, timeframe='3m', limit=20)
                        df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                        
                        delta = df['c'].diff()
                        rsi = 100 - (100 / (1 + (delta.clip(lower=0).mean() / -delta.clip(upper=0).mean())))

                        if rsi <= 35 or rsi >= 65:
                            side = 'buy' if rsi <= 35 else 'sell'
                            qty = (FIXED_AMOUNT_USDT * LEVERAGE) / df['c'].iloc[-1]
                            
                            mexc.create_market_order(symbol, side, qty)
                            st.session_state.trade_times[symbol] = datetime.now()
                            current_count += 1
                            st.success(f"🚀 تم قنص {symbol} بنجاح!")
                    except: continue
            
            time.sleep(15)

    except Exception as e:
        st.error(f"⚠️ خطأ: {e}")
        time.sleep(10)
        
