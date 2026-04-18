import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime, timedelta

# --- 🚀 إعدادات الرادار والربح التراكمي ---
SYMBOLS = [
    'ORDI/USDT:USDT', 'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'BNB/USDT:USDT',
    'XRP/USDT:USDT', 'ADA/USDT:USDT', 'AVAX/USDT:USDT', 'DOGE/USDT:USDT', 'DOT/USDT:USDT',
    'LINK/USDT:USDT', 'MATIC/USDT:USDT', 'SUI/USDT:USDT', 'APT/USDT:USDT', 'OP/USDT:USDT',
    'ARB/USDT:USDT', 'LTC/USDT:USDT', 'NEAR/USDT:USDT', 'TIA/USDT:USDT', 'SEI/USDT:USDT',
    'INJ/USDT:USDT', 'STX/USDT:USDT', 'FIL/USDT:USDT', 'RNDR/USDT:USDT', 'PEPE/USDT:USDT',
    'SHIB/USDT:USDT', 'FET/USDT:USDT', 'AGIX/USDT:USDT', 'GALA/USDT:USDT', 'FTM/USDT:USDT',
    'DYDX/USDT:USDT', 'AAVE/USDT:USDT', 'IMX/USDT:USDT', 'ALGO/USDT:USDT', 'KAS/USDT:USDT',
    'BONK/USDT:USDT', 'JUP/USDT:USDT', 'PYTH/USDT:USDT', 'WIF/USDT:USDT', 'HBAR/USDT:USDT'
]

MAX_TRADES = 4
LEVERAGE = 5
RISK_PER_TRADE = 0.15 # تم تقليلها لـ 15% لزيادة الأمان مع الربح التراكمي
TRADE_DURATION_MINS = 30

st.set_page_config(page_title="Compound Radar Fix", layout="wide")
st.title("💰 رادار الربح التراكمي - النسخة المصححة")

if "running" not in st.session_state: st.session_state.running = False
if "trade_times" not in st.session_state: st.session_state.trade_times = {}

with st.sidebar:
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 تشغيل"): st.session_state.running = True
    if st.button("🛑 إيقاف"): st.session_state.running = False

metrics_area = st.columns(3)
log_area = st.empty()

if st.session_state.running and api_key and api_secret:
    try:
        mexc = ccxt.mexc({
            'apiKey': api_key, 'secret': api_secret,
            'options': {'defaultType': 'future'}, 'enableRateLimit': True
        })

        while st.session_state.running:
            # 1. جلب الرصيد بطريقة MEXC الصحيحة (تجاوز الخطأ)
            account_info = mexc.fetch_balance()
            total_usdt = float(account_info['info']['data'][0]['availableBalance'])
            
            # 2. فحص الصفقات
            positions = mexc.fetch_positions()
            active_positions = [p for p in positions if float(p['contracts']) != 0]
            current_count = len(active_positions)
            active_syms = [p['symbol'] for p in active_positions]

            metrics_area[0].metric("الرصيد المتاح", f"{total_usdt:.2f} USDT")
            metrics_area[1].metric("الصفقات النشطة", f"{current_count}/{MAX_TRADES}")

            # 3. مسح العملات
            for symbol in SYMBOLS:
                clean_sym = symbol.replace('/', '').replace(':', '')
                
                # إغلاق زمني
                if clean_sym in active_syms and symbol in st.session_state.trade_times:
                    if datetime.now() >= st.session_state.trade_times[symbol] + timedelta(minutes=TRADE_DURATION_MINS):
                        pos = next(p for p in active_positions if p['symbol'] == clean_sym)
                        side = 'sell' if float(pos['contracts']) > 0 else 'buy'
                        mexc.create_market_order(symbol, side, abs(float(pos['contracts'])), params={'reduceOnly': True})
                        del st.session_state.trade_times[symbol]
                        st.toast(f"✅ تم جني ربح {symbol}")

                # فتح صفقة تراكمية
                if clean_sym not in active_syms and current_count < MAX_TRADES:
                    try:
                        ohlcv = mexc.fetch_ohlcv(symbol, timeframe='5m', limit=20)
                        df = pd.DataFrame(ohlcv, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
                        delta = df['c'].diff()
                        rsi = 100 - (100 / (1 + (delta.where(delta > 0, 0).rolling(14).mean() / -delta.where(delta < 0, 0).rolling(14).mean()))).iloc[-1]

                        if rsi <= 30 or rsi >= 70:
                            side = 'buy' if rsi <= 30 else 'sell'
                            trade_size = (total_usdt * RISK_PER_TRADE) * LEVERAGE
                            
                            mexc.set_leverage(LEVERAGE, symbol, {'openType': 2})
                            mexc.create_market_order(symbol, side, trade_size / df['c'].iloc[-1])
                            
                            st.session_state.trade_times[symbol] = datetime.now()
                            current_count += 1
                            st.success(f"🎯 قنص تراكمي لـ {symbol}")
                    except: continue

            time.sleep(20)
    except Exception as e:
        st.error(f"خطأ: {e}")
        time.sleep(10)
        
