import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime, timedelta

# --- 🚀 إعدادات الهاتف (40 عملة) ---
SYMBOLS = [
    'ORDI/USDT:USDT', 'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'BNB/USDT:USDT',
    'XRP/USDT:USDT', 'ADA/USDT:USDT', 'AVAX/USDT:USDT', 'DOGE/USDT:USDT', 'DOT/USDT:USDT',
    'SUI/USDT:USDT', 'APT/USDT:USDT', 'OP/USDT:USDT', 'ARB/USDT:USDT', 'NEAR/USDT:USDT'
]

MAX_TRADES = 4
LEVERAGE = 5
RISK_PERCENT = 0.15  # الربح التراكمي (15% من الرصيد)
TRADE_DURATION = 30  # مدة الصفقة

st.set_page_config(page_title="Mobile Sniper", layout="wide")
st.title("📱 قناص MEXC للهواتف")

# --- إدارة الجلسة (Session State) ---
if 'running' not in st.session_state: st.session_state.running = False
if 'trades' not in st.session_state: st.session_state.trades = {}

# --- القائمة الجانبية ---
with st.sidebar:
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 تشغيل"): st.session_state.running = True
    if st.button("🛑 إيقاف"): st.session_state.running = False

# --- المحرك الرئيسي ---
if st.session_state.running and api_key and api_secret:
    try:
        # اتصال مبسط لضمان عدم الفصل من الهاتف
        mexc = ccxt.mexc({
            'apiKey': api_key,
            'secret': api_secret,
            'options': {'defaultType': 'future'}
        })

        while st.session_state.running:
            # 1. جلب الرصيد (الربح التراكمي)
            balance = mexc.fetch_balance()
            total_bal = float(balance['total']['USDT'])
            
            # 2. فحص الصفقات
            pos = mexc.fetch_positions()
            active_p = [p for p in pos if float(p['contracts']) != 0]
            current_count = len(active_p)
            active_names = [p['symbol'] for p in active_p]

            st.write(f"💰 الرصيد: {total_bal:.2f} | صفقات نشطة: {current_count}/4")

            for symbol in SYMBOLS:
                clean = symbol.replace('/', '').replace(':', '')
                
                # إغلاق بعد 30 دقيقة
                if clean in active_names and symbol in st.session_state.trades:
                    if datetime.now() >= st.session_state.trades[symbol] + timedelta(minutes=TRADE_DURATION):
                        mexc.create_market_order(symbol, 'sell', 0, {'reduceOnly': True})
                        del st.session_state.trades[symbol]
                        st.toast(f"✅ تم جني ربح {symbol}")

                # فتح صفقة جديدة
                if clean not in active_names and current_count < MAX_TRADES:
                    ohlcv = mexc.fetch_ohlcv(symbol, timeframe='3m', limit=20)
                    df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                    
                    # حساب RSI (الفحص قبل أخذ الصفقة)
                    delta = df['c'].diff()
                    rsi = 100 - (100 / (1 + (delta.clip(lower=0).mean() / -delta.clip(upper=0).mean())))

                    if rsi <= 35 or rsi >= 65:
                        side = 'buy' if rsi <= 35 else 'sell'
                        # حساب حجم الصفقة (ربح تراكمي)
                        qty = (total_bal * RISK_PERCENT * LEVERAGE) / df['c'].iloc[-1]
                        
                        mexc.create_market_order(symbol, side, qty)
                        st.session_state.trades[symbol] = datetime.now()
                        current_count += 1
                        st.success(f"🎯 قنص صفقة {symbol}")

            time.sleep(20) # مهلة كافية لمتصفح الهاتف

    except Exception as e:
        st.error(f"⚠️ خطأ اتصال: {e}")
        time.sleep(15)
        
