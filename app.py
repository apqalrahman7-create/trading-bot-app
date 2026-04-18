import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime, timedelta

# --- 🚀 إعدادات القناص العالمي (40 عملة) ---
SYMBOLS = [
    'ORDI/USDT:USDT', 'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'BNB/USDT:USDT',
    'XRP/USDT:USDT', 'ADA/USDT:USDT', 'AVAX/USDT:USDT', 'DOGE/USDT:USDT', 'DOT/USDT:USDT',
    'SUI/USDT:USDT', 'APT/USDT:USDT', 'OP/USDT:USDT', 'ARB/USDT:USDT', 'NEAR/USDT:USDT'
    # يمكنك إضافة بقية العملات هنا بنفس الصيغة
]

MAX_TRADES = 4
LEVERAGE = 5
RISK_PERCENT = 0.15 # الدخول بـ 15% من الرصيد المتاح (ربح تراكمي)
TRADE_DURATION = 30 # مدة الصفقة بالدقائق

st.set_page_config(page_title="Old Sniper Pro", layout="wide")
st.title("🎯 قناص MEXC المطور (النسخة العاملة)")

if "running" not in st.session_state: st.session_state.running = False
if "start_times" not in st.session_state: st.session_state.start_times = {}

with st.sidebar:
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 بدء التداول"): st.session_state.running = True
    if st.button("🛑 إيقاف"): st.session_state.running = False

# --- المحرك الرئيسي ---
if st.session_state.running and api_key and api_secret:
    try:
        # الاتصال التقليدي الذي كان يعمل
        mexc = ccxt.mexc({
            'apiKey': api_key,
            'secret': api_secret,
            'options': {'defaultType': 'future'}
        })

        while st.session_state.running:
            # 1. جلب الرصيد والصفقات
            balance = mexc.fetch_balance()
            # تعديل طريقة جلب الرصيد لتعمل مع MEXC وتدعم الربح التراكمي
            available_balance = float(balance['total']['USDT'])
            
            pos = mexc.fetch_positions()
            active_pos = [p for p in pos if float(p['contracts']) != 0]
            current_count = len(active_pos)
            active_symbols = [p['symbol'] for p in active_pos]

            st.write(f"💰 الرصيد الحالي: {available_balance} | الصفقات: {current_count}/{MAX_TRADES}")

            # 2. مسح العملات لفتح صفقات
            for symbol in SYMBOLS:
                clean_sym = symbol.replace('/', '').replace(':', '')
                
                # إغلاق بعد 30 دقيقة
                if clean_sym in active_symbols and symbol in st.session_state.start_times:
                    if datetime.now() >= st.session_state.start_times[symbol] + timedelta(minutes=TRADE_DURATION):
                        p_info = next(p for p in active_pos if p['symbol'] == clean_sym)
                        side = 'sell' if float(p_info['contracts']) > 0 else 'buy'
                        mexc.create_market_order(symbol, side, abs(float(p_info['contracts'])), {'reduceOnly': True})
                        del st.session_state.start_times[symbol]
                        st.success(f"⏰ تم إغلاق {symbol}")

                # فتح صفقة جديدة
                if clean_sym not in active_symbols and current_count < MAX_TRADES:
                    ohlcv = mexc.fetch_ohlcv(symbol, timeframe='3m', limit=20)
                    df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                    
                    # حساب RSI (المنطق القديم)
                    delta = df['c'].diff()
                    rsi = 100 - (100 / (1 + (delta.clip(lower=0).mean() / -delta.clip(upper=0).mean())))

                    if rsi <= 35 or rsi >= 65:
                        side = 'buy' if rsi <= 35 else 'sell'
                        # حساب حجم الصفقة للربح التراكمي
                        entry_size = (available_balance * RISK_PERCENT * LEVERAGE) / df['c'].iloc[-1]
                        
                        # تنفيذ الأمر
                        mexc.create_market_order(symbol, side, entry_size)
                        st.session_state.start_times[symbol] = datetime.now()
                        current_count += 1
                        st.info(f"🎯 قنص صفقة {side} لـ {symbol}")

            time.sleep(15)

    except Exception as e:
        st.error(f"حدث خطأ: {e}")
        time.sleep(10)
        
