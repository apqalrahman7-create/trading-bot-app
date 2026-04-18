import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime, timedelta

# --- 🚀 الإعدادات (40 عملة) ---
SYMBOLS = [
    'ORDI/USDT:USDT', 'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'BNB/USDT:USDT',
    'XRP/USDT:USDT', 'ADA/USDT:USDT', 'AVAX/USDT:USDT', 'DOGE/USDT:USDT', 'DOT/USDT:USDT',
    'LINK/USDT:USDT', 'SUI/USDT:USDT', 'APT/USDT:USDT', 'OP/USDT:USDT', 'ARB/USDT:USDT',
    'NEAR/USDT:USDT', 'TIA/USDT:USDT', 'SEI/USDT:USDT', 'INJ/USDT:USDT', 'PEPE/USDT:USDT',
    'SHIB/USDT:USDT', 'FET/USDT:USDT', 'FIL/USDT:USDT', 'GALA/USDT:USDT', 'FTM/USDT:USDT'
]

st.set_page_config(page_title="Active Sniper Pro", layout="wide")
st.title("🎯 قناص MEXC النشط")

if "running" not in st.session_state: st.session_state.running = False
if "trade_times" not in st.session_state: st.session_state.trade_times = {}

# واجهة الدخول
with st.sidebar:
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 تشغيل"): st.session_state.running = True
    if st.button("🛑 إيقاف"): st.session_state.running = False

# المحرك (المنطق البسيط الذي كان يعمل)
if st.session_state.running and api_key and api_secret:
    try:
        # الاتصال المباشر البسيط
        mexc = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'future'}})
        
        while st.session_state.running:
            # 1. جلب الرصيد والصفقات (بأبسط الدوال)
            balance = mexc.fetch_balance()
            total_balance = float(balance['total']['USDT'])
            
            positions = mexc.fetch_positions()
            active_list = [p for p in positions if float(p['contracts']) != 0]
            current_count = len(active_list)
            
            st.write(f"💰 الرصيد: {total_balance} | الصفقات النشطة: {current_count}/4")

            # 2. فحص العملات (المنطق القديم)
            for symbol in SYMBOLS:
                clean_sym = symbol.replace('/', '').replace(':', '')
                
                # إغلاق بعد 30 دقيقة
                if any(p['symbol'] == clean_sym for p in active_list) and symbol in st.session_state.trade_times:
                    if datetime.now() >= st.session_state.trade_times[symbol] + timedelta(minutes=30):
                        mexc.create_market_order(symbol, 'sell', 0, {'reduceOnly': True}) # إغلاق مبسط
                        del st.session_state.trade_times[symbol]
                        st.success(f"✅ إغلاق {symbol}")

                # فتح صفقة جديدة (إذا لم نصل لـ 4 صفقات)
                if not any(p['symbol'] == clean_sym for p in active_list) and current_count < 4:
                    ohlcv = mexc.fetch_ohlcv(symbol, timeframe='3m', limit=20)
                    df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                    
                    # حساب RSI بسيط ومباشر
                    delta = df['c'].diff()
                    rsi = 100 - (100 / (1 + (delta.clip(lower=0).mean() / -delta.clip(upper=0).mean())))

                    if rsi <= 35 or rsi >= 65:
                        side = 'buy' if rsi <= 35 else 'sell'
                        # الربح التراكمي: الدخول بـ 15% من الرصيد
                        amount = (total_balance * 0.15 * 5) / df['c'].iloc[-1]
                        
                        mexc.create_market_order(symbol, side, amount)
                        st.session_state.trade_times[symbol] = datetime.now()
                        current_count += 1
                        st.info(f"🚀 تم فتح صفقة {symbol}")

            time.sleep(15)
    except Exception as e:
        st.error(f"خطأ: {e}")
        time.sleep(10)
        
