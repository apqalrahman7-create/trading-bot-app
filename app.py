import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime, timedelta
import time

# --- 1. STRATEGIC SETTINGS ---
LEVERAGE = 10           
ENTRY_AMOUNT_USDT = 12  
TP_TARGET = 0.04        # الهدف الأساسي 4%
SL_LIMIT = -0.02        # وقف الخسارة 2%
MIN_PROFIT_TO_LOCK = 0.015 # بمجرد وصول الربح لـ 1.5% يبدأ البوت بتأمين الصفقة
TRADE_DURATION_MINS = 30 

st.set_page_config(page_title="AI Smart Secure Trader", layout="wide")
st.title("🛡️ AI Smart Secure Trader (Profit Protector)")

if 'running' not in st.session_state: st.session_state.running = False
if 'cooldowns' not in st.session_state: st.session_state.cooldowns = {}

with st.sidebar:
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 تشغيل النظام الذكي"): st.session_state.running = True
    if st.button("🛑 إيقاف الطوارئ"): st.session_state.running = False

if st.session_state.running:
    try:
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        
        balance = ex.fetch_balance()
        total_usdt = balance['total'].get('USDT', 0)
        max_slots = int((total_usdt * 0.9) / ENTRY_AMOUNT_USDT)

        all_pos = ex.fetch_positions()
        active_positions = [p for p in all_pos if p.get('contracts') and float(p['contracts']) > 0]
        
        st.metric("Total Equity", f"${total_usdt:.2f}")
        st.write(f"Active Slots: {len(active_positions)}/{max_slots}")

        # --- 1. EXIT & PROFIT PROTECTION MONITOR ---
        for p in active_positions:
            try:
                symbol, side = p['symbol'], p['side']
                entry_p, mark_p = float(p.get('entryPrice') or 0), float(p.get('markPrice') or 0)
                if entry_p <= 0: continue

                pnl = (mark_p - entry_p) / entry_p if side == 'long' else (entry_p - mark_p) / entry_p
                open_ts = datetime.fromtimestamp(p.get('timestamp', time.time()*1000) / 1000)
                mins_active = (datetime.now() - open_ts).total_seconds() / 60

                # --- منطق تأمين الربح الجديد ---
                # إذا حققت الصفقة ربحاً جيداً (أكبر من 1.5%) وبدأ السعر بالتراجع، نغلق فوراً
                # سنحتاج لمقارنة سعر العلامة بالسعر العالي للحظة (بسيط هنا عبر PNL)
                
                should_close = False
                if pnl >= TP_TARGET: should_close = True # وصل للهدف الكامل
                elif pnl <= SL_LIMIT: should_close = True # وصل لوقف الخسارة
                elif mins_active >= TRADE_DURATION_MINS: should_close = True # انتهى الوقت
                
                # إضافة حماية: إذا كان الربح > 1.5% والسعر بدأ ينعكس (هنا نستخدم الفريم الصغير جداً للتأكد)
                if pnl > MIN_PROFIT_TO_LOCK:
                    ohlcv_check = ex.fetch_ohlcv(symbol, timeframe='1m', limit=3)
                    last_close = ohlcv_check[-1][4]
                    prev_close = ohlcv_check[-2][4]
                    # إذا كانت الشمعة الحالية عكس اتجاهنا بقوة، نؤمن الربح
                    if (side == 'long' and last_close < prev_close) or (side == 'short' and last_close > prev_close):
                        should_close = True
                        st.toast(f"Profit Locked for {symbol}")

                if should_close:
                    ex.create_market_order(symbol, 'sell' if side == 'long' else 'buy', p['contracts'], params={'openType': 2})
                    st.session_state.cooldowns[symbol] = datetime.now() + timedelta(minutes=15)
            except: continue

        # --- 2. MULTI-ENTRY SCANNER ---
        if len(active_positions) < max_slots:
            tickers = ex.fetch_tickers()
            symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT')]
            
            for s in symbols[:60]:
                if len(active_positions) >= max_slots: break
                if s in st.session_state.cooldowns or any(ap['symbol'] == s for ap in active_positions): continue

                try:
                    ohlcv = ex.fetch_ohlcv(s, timeframe='5m', limit=20)
                    df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                    last_p = df['c'].iloc[-1]
                    high_break = df['h'].iloc[-15:-1].max()
                    low_break = df['l'].iloc[-11:-1].min()
                    curr_vol = df['v'].iloc[-1]
                    avg_vol = df['v'].mean()

                    # شرط دخول قوي: كسر مع حجم تداول مرتفع
                    if curr_vol > avg_vol * 1.3:
                        trade_side = 'buy' if last_p > high_break else 'sell' if last_p < low_break else None
                        if trade_side:
                            pos_type = 1 if trade_side == 'buy' else 2
                            ex.set_leverage(LEVERAGE, s, params={'openType': 2, 'positionType': pos_type})
                            qty = (ENTRY_AMOUNT_USDT * LEVERAGE) / last_p
                            ex.create_market_order(s, trade_side, float(ex.amount_to_precision(s, qty)), 
                                                  params={'openType': 2, 'positionType': pos_type, 'settle': 'USDT'})
                            active_positions.append({'symbol': s})
                            st.info(f"🔥 دخلنا فرصة جديدة: {s}")
                except: continue

        time.sleep(25)
        st.rerun()
    except Exception as e:
        time.sleep(10)
        st.rerun()
        
