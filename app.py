import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime, timedelta

# --- 🚀 القائمة العالمية (40 عملة) ---
SYMBOLS = [
    'ORDI/USDT:USDT', 'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'BNB/USDT:USDT',
    'XRP/USDT:USDT', 'ADA/USDT:USDT', 'AVAX/USDT:USDT', 'DOGE/USDT:USDT', 'DOT/USDT:USDT',
    'LINK/USDT:USDT', 'SUI/USDT:USDT', 'APT/USDT:USDT', 'OP/USDT:USDT', 'ARB/USDT:USDT',
    'NEAR/USDT:USDT', 'TIA/USDT:USDT', 'SEI/USDT:USDT', 'INJ/USDT:USDT', 'PEPE/USDT:USDT',
    'SHIB/USDT:USDT', 'FET/USDT:USDT', 'FIL/USDT:USDT', 'GALA/USDT:USDT', 'FTM/USDT:USDT',
    'AAVE/USDT:USDT', 'ALGO/USDT:USDT', 'JUP/USDT:USDT', 'WIF/USDT:USDT', 'HBAR/USDT:USDT'
]

MAX_TRADES = 4
LEVERAGE = 5
FIXED_ENTRY_USDT = 12 
TRADE_DURATION_MINS = 30

st.set_page_config(page_title="Global Sniper Work", layout="wide")
st.title("🎯 قناص MEXC النشط - 40 عملة")

if "running" not in st.session_state: st.session_state.running = False
if "trades" not in st.session_state: st.session_state.trades = {}

with st.sidebar:
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 تشغيل التداول الحقيقي"): st.session_state.running = True
    if st.button("🛑 إيقاف"): st.session_state.running = False

status_msg = st.empty()

if st.session_state.running and api_key and api_secret:
    try:
        mexc = ccxt.mexc({
            'apiKey': api_key, 'secret': api_secret,
            'options': {'defaultType': 'future'}, 'enableRateLimit': True
        })

        while st.session_state.running:
            # 1. جلب الصفقات الحالية (لتجنب التكرار)
            pos_info = mexc.fetch_positions()
            active_list = [p['symbol'] for p in pos_info if float(p['contracts']) != 0]
            current_count = len(active_list)
            
            status_msg.info(f"🔎 الرادار يفحص السوق.. الصفقات المفتوحة: {current_count}/{MAX_TRADES}")

            # 2. مسح العملات لفتح صفقات (المنطق القديم النشط)
            for symbol in SYMBOLS:
                clean_sym = symbol.replace('/', '').replace(':', '')
                
                # إغلاق زمني (العودة للفحص بعد 30 دقيقة)
                if clean_sym in active_list and symbol in st.session_state.trades:
                    if datetime.now() >= st.session_state.trades[symbol] + timedelta(minutes=TRADE_DURATION_MINS):
                        side = 'sell' if float(next(p for p in pos_info if p['symbol'] == clean_sym)['contracts']) > 0 else 'buy'
                        mexc.create_market_order(symbol, side, abs(float(next(p for p in pos_info if p['symbol'] == clean_sym)['contracts'])), {'reduceOnly': True})
                        del st.session_state.trades[symbol]
                        st.toast(f"✅ إغلاق زمني لـ {symbol}")

                # البحث عن دخول (تخفيف الشروط قليلاً ليبدأ العمل)
                if clean_sym not in active_list and current_count < MAX_TRADES:
                    try:
                        ohlcv = mexc.fetch_ohlcv(symbol, timeframe='3m', limit=20)
                        df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                        
                        # حساب RSI (المنطق الذي كان يعمل عندك)
                        delta = df['c'].diff()
                        rsi = 100 - (100 / (1 + (delta.where(delta > 0, 0).rolling(14).mean() / -delta.where(delta < 0, 0).rolling(14).mean()))).iloc[-1]

                        # شروط دخول نشطة (RSI تحت 35 أو فوق 65)
                        if rsi <= 35 or rsi >= 65:
                            side = 'buy' if rsi <= 35 else 'sell'
                            # إزالة set_leverage مؤقتاً إذا كانت تسبب خطأ واستخدام الرافعة الافتراضية
                            mexc.create_market_order(symbol, side, (FIXED_ENTRY_USDT * LEVERAGE) / df['c'].iloc[-1])
                            st.session_state.trades[symbol] = datetime.now()
                            current_count += 1
                            st.success(f"🚀 صفقة فورية: {symbol} | RSI: {rsi:.1f}")
                    except: continue

            time.sleep(10) # فحص سريع كل 10 ثوانٍ لضمان عدم فوات الفرص

    except Exception as e:
        st.error(f"⚠️ خطأ في التنفيذ: {e}")
        time.sleep(10)
        
