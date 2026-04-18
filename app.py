import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime, timedelta
import time

# --- 1. SETTINGS FOR STABLE PROFIT ---
LEVERAGE = 5            # تقليل الرافعة لـ 5 لزيادة الأمان ومنع التصفية السريعة
ENTRY_AMOUNT_USDT = 12  
TP_TARGET = 0.03        # هدف واقعي 3%
SL_LIMIT = -0.04        # وقف خسارة بعيد قليلاً لمنع الخروج بسبب التذبذب البسيط
TRADE_DURATION_MINS = 60 # زيادة الوقت لساعة ليعطي الصفقة فرصة للتحرك

st.set_page_config(page_title="AI Safe-Profit Bot", layout="wide")
st.title("🛡️ AI Safe-Profit (Anti-Loss Edition)")

if 'running' not in st.session_state: st.session_state.running = False
if 'cooldowns' not in st.session_state: st.session_state.cooldowns = {}

with st.sidebar:
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 تشغيل النظام الآمن"): st.session_state.running = True
    if st.button("🛑 إيقاف"): st.session_state.running = False

# --- THE STABLE ENGINE ---
if st.session_state.running:
    try:
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        balance = ex.fetch_balance()
        total_usdt = balance['total'].get('USDT', 0)
        max_slots = 5 # تثبيت عدد الصفقات عند 5 لتركيز السيولة

        all_pos = ex.fetch_positions()
        active_positions = [p for p in all_pos if p.get('contracts') and float(p['contracts']) > 0]

        st.metric("Total Balance", f"${total_usdt:.2f}")
        st.write(f"Active Slots: {len(active_positions)}/5")

        # --- 1. SMART MONITOR (Profit Protection) ---
        for p in active_positions:
            try:
                symbol, side = p['symbol'], p['side']
                entry_p, mark_p = float(p.get('entryPrice') or 0), float(p.get('markPrice') or 0)
                if entry_p <= 0: continue
                pnl = (mark_p - entry_p) / entry_p if side == 'long' else (entry_p - mark_p) / entry_p
                
                open_ts = datetime.fromtimestamp(p.get('timestamp', time.time()*1000) / 1000)
                mins_active = (datetime.now() - open_ts).total_seconds() / 60

                # الإغلاق فقط عند الهدف أو الوقف أو انتهاء الساعة
                if pnl >= TP_TARGET or pnl <= SL_LIMIT or mins_active >= TRADE_DURATION_MINS:
                    ex.create_market_order(symbol, 'sell' if side == 'long' else 'buy', p['contracts'], params={'openType': 2})
                    st.session_state.cooldowns[symbol] = datetime.now() + timedelta(minutes=60) # حظر العملة ساعة كاملة
            except: continue

        # --- 2. HIGH-QUALITY SCANNER (Bollinger Band Strategy) ---
        if len(active_positions) < max_slots:
            tickers = ex.fetch_tickers()
            symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT')]
            
            for s in symbols[:50]:
                if len(active_positions) >= max_slots: break
                if s in st.session_state.cooldowns or any(ap['symbol'] == s for ap in active_positions): continue

                try:
                    # نستخدم فريم 15 دقيقة لتحليل أعمق وأكثر صدقاً
                    ohlcv = ex.fetch_ohlcv(s, timeframe='15m', limit=30)
                    df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                    
                    last_p = df['c'].iloc[-1]
                    sma = df['c'].rolling(20).mean().iloc[-1]
                    std = df['c'].rolling(20).std().iloc[-1]
                    upper_band = sma + (2 * std)
                    lower_band = sma - (2 * std)

                    # استراتيجية الارتداد: الشراء من القاع والبيع من القمة
                    # شراء إذا لمس السعر النطاق السفلي (تشبع بيع)
                    # بيع إذا لمس السعر النطاق العلوي (تشبع شراء)
                    trade_side = None
                    if last_p <= lower_band: trade_side = 'buy'
                    elif last_p >= upper_barrier: trade_side = 'sell'

                    if trade_side:
                        # تأكيد إضافي بحجم التداول
                        if df['v'].iloc[-1] > df['v'].mean():
                            ex.set_leverage(LEVERAGE, s, params={'openType': 2, 'positionType': (1 if trade_side=='buy' else 2)})
                            qty = (ENTRY_AMOUNT_USDT * LEVERAGE) / last_p
                            ex.create_market_order(s, trade_side, float(ex.amount_to_precision(s, qty)), 
                                                  params={'openType': 2, 'positionType': (1 if trade_side=='buy' else 2), 'settle': 'USDT'})
                            st.success(f"💎 Quality Entry: {trade_side.upper()} {s}")
                            break
                except: continue

        time.sleep(30)
        st.rerun()
    except Exception as e:
        time.sleep(15)
        st.rerun()
        
