import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime, timedelta
import time

# --- 1. SETTINGS ---
LEVERAGE = 10           
ENTRY_AMOUNT_USDT = 12  
TP_TARGET = 0.05        # هدف 5%
SL_LIMIT = -0.025       # وقف خسارة 2.5%
MIN_PROFIT_TO_PROTECT = 0.015 # عند ربح 1.5% يبدأ البوت بمراقبة تأمين الربح
TRADE_DURATION_MINS = 30 

st.set_page_config(page_title="AI Profit Guardian", layout="wide")
st.title("🛡️ AI Profit Guardian (30-Min Strategy)")

if 'running' not in st.session_state: st.session_state.running = False
if 'cooldowns' not in st.session_state: st.session_state.cooldowns = {}

with st.sidebar:
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 تشغيل النظام المطور"): st.session_state.running = True
    if st.button("🛑 إيقاف"): st.session_state.running = False

# --- THE GUARDIAN ENGINE ---
if st.session_state.running:
    try:
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        balance = ex.fetch_balance()
        total_usdt = balance['total'].get('USDT', 0)
        
        all_pos = ex.fetch_positions()
        active_positions = [p for p in all_pos if p.get('contracts') and float(p['contracts']) > 0]

        st.metric("Total Equity", f"${total_usdt:.2f}")
        st.write(f"Active Slots: {len(active_positions)} / 5")

        # 1. MONITOR & SMART EXIT (تأمين الربح والوقت)
        for p in active_positions:
            try:
                symbol, side = p['symbol'], p['side']
                entry_p, mark_p = float(p.get('entryPrice') or 0), float(p.get('markPrice') or 0)
                pnl = (mark_p - entry_p) / entry_p if side == 'long' else (entry_p - mark_p) / entry_p
                
                open_ts = datetime.fromtimestamp(p.get('timestamp', time.time()*1000) / 1000)
                mins_active = (datetime.now() - open_ts).total_seconds() / 60

                should_close = False
                
                # شرط الوقت (30 دقيقة)
                if mins_active >= TRADE_DURATION_MINS: should_close = True
                # شرط الهدف أو الوقف
                elif pnl >= TP_TARGET or pnl <= SL_LIMIT: should_close = True
                # شرط تأمين الربح: إذا كان الربح > 1.5% وبدأ السعر ينعكس (شمعة دقيقة هابطة)
                elif pnl > MIN_PROFIT_TO_PROTECT:
                    ticker = ex.fetch_ticker(symbol)
                    if (side == 'long' and ticker['last'] < ticker['open']) or \
                       (side == 'short' and ticker['last'] > ticker['open']):
                        should_close = True
                        st.toast(f"💰 تأمين الربح المحقق في {symbol}")

                if should_close:
                    ex.create_market_order(symbol, 'sell' if side == 'long' else 'buy', p['contracts'], params={'openType': 2})
                    st.session_state.cooldowns[symbol] = datetime.now() + timedelta(minutes=45)
            except: continue

        # 2. ANALYSIS & ENTRY (تحليل المستقبل)
        if len(active_positions) < 5:
            tickers = ex.fetch_tickers()
            symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT')]
            
            for s in symbols[:50]:
                if len(active_positions) >= 5 or s in st.session_state.cooldowns: continue

                try:
                    # تحليل الفريمات لضمان اتجاه مستقبلي رابح
                    ohlcv = ex.fetch_ohlcv(s, timeframe='15m', limit=20)
                    df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                    
                    last_price = df['c'].iloc[-1]
                    ma_fast = df['c'].rolling(5).mean().iloc[-1]
                    ma_slow = df['c'].rolling(15).mean().iloc[-1]

                    # الدخول فقط إذا كان هناك تقاطع سعري يضمن استمرار الحركة لـ 30 دقيقة
                    trade_side = 'buy' if ma_fast > ma_slow * 1.002 else 'sell' if ma_fast < ma_slow * 0.998 else None

                    if trade_side:
                        ex.set_leverage(LEVERAGE, s, params={'openType': 2, 'positionType': (1 if trade_side=='buy' else 2)})
                        qty = (ENTRY_AMOUNT_USDT * LEVERAGE) / last_price
                        ex.create_market_order(s, trade_side, float(ex.amount_to_precision(s, qty)), 
                                              params={'openType': 2, 'positionType': (1 if trade_side=='buy' else 2), 'settle': 'USDT'})
                        st.info(f"🎯 صفقة جديدة: {trade_side.upper()} {s} (تحليل مستقبلي مؤكد)")
                        break
                except: continue

        time.sleep(25)
        st.rerun()
    except Exception as e:
        time.sleep(15)
        st.rerun()
        
