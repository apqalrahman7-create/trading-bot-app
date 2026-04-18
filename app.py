import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime, timedelta

# --- ⚙️ الإعدادات (نظام الـ 4 صفقات) ---
SYMBOLS = ['ORDI/USDT:USDT', 'BTC/USDT:USDT', 'SOL/USDT:USDT', 'ETH/USDT:USDT']
MAX_TRADES = 4
LEVERAGE = 5
ENTRY_AMOUNT = 12
TRADE_DURATION_MINS = 30

st.set_page_config(page_title="Multi-Sniper Pro", layout="wide")
st.title("🚀 قناص MEXC الاحترافي (4 صفقات)")

if "running" not in st.session_state: st.session_state.running = False
if "trade_start_times" not in st.session_state: st.session_state.trade_start_times = {}

with st.sidebar:
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 تشغيل"): st.session_state.running = True
    if st.button("🛑 إيقاف"): st.session_state.running = False

status_placeholders = st.columns(len(SYMBOLS))

if st.session_state.running and api_key and api_secret:
    try:
        mexc = ccxt.mexc({
            'apiKey': api_key, 'secret': api_secret,
            'options': {'defaultType': 'future'}, 'enableRateLimit': True
        })

        while st.session_state.running:
            # 1. جلب الصفقات المفتوحة حالياً
            pos_data = mexc.fetch_positions()
            active_positions = [p for p in pos_data if float(p['contracts']) != 0]
            current_count = len(active_positions)

            for i, symbol in enumerate(SYMBOLS):
                # جلب البيانات وحساب RSI
                ohlcv = mexc.fetch_ohlcv(symbol, timeframe='5m', limit=50)
                df = pd.DataFrame(ohlcv, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
                delta = df['c'].diff()
                rsi = 100 - (100 / (1 + (delta.where(delta > 0, 0).rolling(14).mean() / -delta.where(delta < 0, 0).rolling(14).mean()))).iloc[-1]
                price = df['c'].iloc[-1]

                status_placeholders[i].metric(symbol.split('/')[0], f"{price}", f"RSI: {rsi:.1f}")

                # فحص إذا كانت العملة مفتوحة حالياً
                clean_symbol = symbol.replace('/', '').replace(':', '')
                is_open = any(p['symbol'] == clean_symbol for p in active_positions)

                # أ. منطق الدخول (إذا وجد فرصة والعدد أقل من 4)
                if not is_open and current_count < MAX_TRADES:
                    side = None
                    if rsi <= 32: side = 'buy'
                    elif rsi >= 68: side = 'sell'

                    if side:
                        # حل مشكلة setLeverage في MEXC (إضافة المعاملات المطلوبة)
                        try:
                            mexc.set_leverage(LEVERAGE, symbol, {'openType': 2, 'positionType': 1 if side == 'buy' else 2})
                        except: pass 
                        
                        mexc.create_market_order(symbol, side, ENTRY_AMOUNT/price)
                        st.session_state.trade_start_times[symbol] = datetime.now()
                        st.toast(f"✅ تم فتح صفقة {side} لـ {symbol}")

                # ب. منطق الخروج (بعد 30 دقيقة)
                if is_open and symbol in st.session_state.trade_start_times:
                    if datetime.now() >= st.session_state.trade_start_times[symbol] + timedelta(minutes=TRADE_DURATION_MINS):
                        pos = next(p for p in active_positions if p['symbol'] == clean_symbol)
                        exit_side = 'sell' if float(pos['contracts']) > 0 else 'buy'
                        mexc.create_market_order(symbol, exit_side, abs(float(pos['contracts'])), params={'reduceOnly': True})
                        del st.session_state.trade_start_times[symbol]
                        st.toast(f"⏰ إغلاق زمنية لـ {symbol}")

            time.sleep(20)
    except Exception as e:
        st.error(f"خطأ: {e}")
        time.sleep(10)
        
