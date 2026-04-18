import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime, timedelta

# --- 🚀 القائمة النشطة ---
SYMBOLS = ['ORDI/USDT:USDT', 'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'LTC/USDT:USDT', 'XRP/USDT:USDT']
MAX_TRADES = 4
FIXED_ENTRY_USDT = 12 

st.set_page_config(page_title="MEXC Force Sniper", layout="wide")
st.title("⚡ قناص MEXC الهجومي - تداول فوري")

if "running" not in st.session_state: st.session_state.running = False
if "trades" not in st.session_state: st.session_state.trades = {}

with st.sidebar:
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 تشغيل إجباري"): st.session_state.running = True
    if st.button("🛑 إيقاف"): st.session_state.running = False

status = st.empty()

if st.session_state.running and api_key and api_secret:
    try:
        # اتصال مباشر بدون قيود
        exchange = ccxt.mexc({
            'apiKey': api_key,
            'secret': api_secret,
            'options': {'defaultType': 'future'},
            'enableRateLimit': True
        })

        while st.session_state.running:
            # 1. فحص الاتصال الفعلي بالمنصة
            balance = exchange.fetch_free_balance()
            status.info(f"🟢 متصل بالمنصة | الرصيد المتاح: {balance.get('USDT', 0)} USDT")

            # 2. فحص الصفقات المفتوحة
            pos = exchange.fetch_positions()
            active_list = [p['symbol'] for p in pos if float(p['contracts']) != 0]
            current_count = len(active_list)

            # 3. مسح سريع جداً للفرص
            for symbol in SYMBOLS:
                if current_count >= MAX_TRADES: break
                
                clean_sym = symbol.replace('/', '').replace(':', '')
                if clean_sym in active_list: continue

                try:
                    ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=20)
                    df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                    
                    # حساب RSI هجومي (أسرع)
                    delta = df['c'].diff()
                    rsi = 100 - (100 / (1 + (delta.clip(lower=0).mean() / -delta.clip(upper=0).mean())))

                    # شروط دخول واسعة جداً لضمان بدء العمل (40 و 60)
                    if rsi <= 40 or rsi >= 60:
                        side = 'buy' if rsi <= 40 else 'sell'
                        price = df['c'].iloc[-1]
                        # فتح الصفقة بأمر سوق مباشر
                        exchange.create_market_order(symbol, side, FIXED_ENTRY_USDT / price)
                        st.success(f"🔥 تم تنفيذ صفقة {side} على {symbol} | RSI: {rsi:.1f}")
                        current_count += 1
                        time.sleep(1) # مهلة بسيطة بين العمليات
                except:
                    continue

            time.sleep(5) # فحص كل 5 ثوانٍ فقط ليكون سريعاً جداً

    except Exception as e:
        st.error(f"❌ خطأ اتصال: {e}")
        st.info("تأكد من تفعيل (Futures Trading) في إعدادات API بموقع MEXC")
        st.session_state.running = False
        
