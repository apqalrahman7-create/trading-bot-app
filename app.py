import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime, timedelta
import time

# --- 1. SAFE RECOVERY SETTINGS ---
LEVERAGE = 5            # تقليل الرافعة لـ 5 لتقليل سرعة الخسارة
ENTRY_AMOUNT_USDT = 12  
TP_TARGET = 0.03        # هدف واقعي 3%
SL_LIMIT = -0.02        # وقف خسارة صارم 2%
TRADE_DURATION_MINS = 30 

st.set_page_config(page_title="AI Safe Recovery", layout="wide")
st.title("🛡️ AI Safe Recovery (Anti-Bleeding Mode)")

if 'running' not in st.session_state: st.session_state.running = False
if 'blacklist' not in st.session_state: st.session_state.blacklist = {}

# --- SIDEBAR ---
with st.sidebar:
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 Start Safe Engine"): st.session_state.running = True
    if st.button("🛑 STOP ALL"): st.session_state.running = False

# --- THE LOGIC ---
if st.session_state.running:
    try:
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        balance = ex.fetch_balance()
        total_usdt = balance['total'].get('USDT', 0)
        
        # جلب الصفقات والتأكد من عدم تكرار الفتح
        all_pos = ex.fetch_positions()
        active_positions = [p for p in all_pos if p.get('contracts') and float(p['contracts']) > 0]

        # 1. إغلاق الصفقات (تأمين الربح أو وقف النزيف)
        for p in active_positions:
            try:
                symbol, side = p['symbol'], p['side']
                entry_p, mark_p = float(p.get('entryPrice') or 0), float(p.get('markPrice') or 0)
                pnl = (mark_p - entry_p) / entry_p if side == 'long' else (entry_p - mark_p) / entry_p
                
                open_ts = datetime.fromtimestamp(p.get('timestamp', time.time()*1000) / 1000)
                mins_active = (datetime.now() - open_ts).total_seconds() / 60

                if pnl >= TP_TARGET or pnl <= SL_LIMIT or mins_active >= TRADE_DURATION_MINS:
                    ex.create_market_order(symbol, 'sell' if side == 'long' else 'buy', p['contracts'], params={'openType': 2})
                    # حظر العملة فوراً لمدة ساعتين لمنع تكرار الكارثة التي في الصورة
                    st.session_state.blacklist[symbol] = datetime.now() + timedelta(hours=2)
                    st.warning(f"Safety Exit triggered for {symbol}")
            except: continue

        # 2. تحليل المسار المستقبلي (دخول ذكي فقط)
        if len(active_positions) < 5:
            tickers = ex.fetch_tickers()
            symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT')]
            
            for s in symbols[:50]:
                if s in st.session_state.blacklist or any(ap['symbol'] == s for ap in active_positions): continue
                
                # فحص الـ Blacklist لتنظيفها
                if s in st.session_state.blacklist and datetime.now() > st.session_state.blacklist[s]:
                    del st.session_state.blacklist[s]

                try:
                    ohlcv = ex.fetch_ohlcv(s, timeframe='15m', limit=30)
                    df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                    
                    # تحليل الاتجاه عبر EMA (لا تشتري أبداً والسعر تحت المتوسط)
                    ema_fast = df['c'].ewm(span=9).mean().iloc[-1]
                    ema_slow = df['c'].ewm(span=21).mean().iloc[-1]
                    current_price = df['c'].iloc[-1]

                    trade_side = None
                    # في صورتك كان يشتري والسعر يهبط.. هنا سيبيع مع الهبوط (Short) أو يشتري مع الصعود الحقيقي (Long)
                    if current_price > ema_fast > ema_slow: trade_side = 'buy'
                    elif current_price < ema_fast < ema_slow: trade_side = 'sell'

                    if trade_side:
                        ex.set_leverage(LEVERAGE, s, params={'openType': 2, 'positionType': (1 if trade_side=='buy' else 2)})
                        qty = (ENTRY_AMOUNT_USDT * LEVERAGE) / current_price
                        ex.create_market_order(s, trade_side, float(ex.amount_to_precision(s, qty)), 
                                              params={'openType': 2, 'positionType': (1 if trade_side=='buy' else 2), 'settle': 'USDT'})
                        st.info(f"🚀 Found SAFE Trend: {trade_side.upper()} on {s}")
                        break 
                except: continue

        time.sleep(30)
        st.rerun()
    except Exception as e:
        time.sleep(20)
        st.rerun()
        
