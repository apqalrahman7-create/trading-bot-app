import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime, timedelta
import time

# --- 1. SETTINGS FOR PREDICTIVE EXPERIMENT ---
LEVERAGE = 10           # رافعة 10 لاستغلال التوقعات السريعة
ENTRY_AMOUNT_USDT = 12  
TP_TARGET = 0.05        # هدف طموح 5% (توقع انفجار)
SL_LIMIT = -0.025       # وقف خسارة 2.5% لحماية رأس المال
TRADE_DURATION_MINS = 30 

st.set_page_config(page_title="AI Future Predictor - Test Lab", layout="wide")
st.title("🧪 AI Future Predictor (Experimental Mode)")
st.subheader("تحليل المسار المستقبلي بناءً على قوة الدفع والسيولة")

# --- INITIALIZE STATE ---
if 'running' not in st.session_state: st.session_state.running = False
if 'cooldowns' not in st.session_state: st.session_state.cooldowns = {}
if 'trade_logs' not in st.session_state: st.session_state.trade_logs = []

# --- SIDEBAR ---
with st.sidebar:
    st.header("Credentials")
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    st.divider()
    if st.button("🚀 تشغيل محرك التجربة"):
        if api_key and api_secret: st.session_state.running = True
    if st.button("🛑 إيقاف"):
        st.session_state.running = False

# --- PREDICTIVE ENGINE ---
if st.session_state.running:
    try:
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        balance = ex.fetch_balance()
        total_usdt = balance['total'].get('USDT', 0)
        
        all_pos = ex.fetch_positions()
        active_positions = [p for p in all_pos if p.get('contracts') and float(p['contracts']) > 0]

        # عرض البيانات الأساسية
        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("Balance", f"${total_usdt:.2f}")
        c2.metric("Active Slots", f"{len(active_positions)} / 5")
        c3.metric("Status", "Scanning & Predicting...")

        # 1. مراقبة وإغلاق الصفقات (تأمين الربح/الوقت)
        for p in active_positions:
            try:
                symbol, side = p['symbol'], p['side']
                entry_p = float(p.get('entryPrice') or 0)
                mark_p = float(p.get('markPrice') or 0)
                if entry_p <= 0: continue

                pnl = (mark_p - entry_p) / entry_p if side == 'long' else (entry_p - mark_p) / entry_p
                open_ts = datetime.fromtimestamp(p.get('timestamp', time.time()*1000) / 1000)
                mins_active = (datetime.now() - open_ts).total_seconds() / 60

                if pnl >= TP_TARGET or pnl <= SL_LIMIT or mins_active >= TRADE_DURATION_MINS:
                    ex.create_market_order(symbol, 'sell' if side == 'long' else 'buy', p['contracts'], params={'openType': 2})
                    st.session_state.cooldowns[symbol] = datetime.now() + timedelta(hours=1)
                    st.session_state.trade_logs.append(f"[{datetime.now().strftime('%H:%M')}] Closed {symbol} | PnL: {pnl*100:.2f}%")
            except: continue

        # 2. ماسح التنبؤ (فحص العملات الـ 40 الأكثر سيولة)
        if len(active_positions) < 5:
            tickers = ex.fetch_tickers()
            symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT')]
            
            for s in symbols[:40]:
                if len(active_positions) >= 5 or s in st.session_state.cooldowns: continue
                if any(ap['symbol'] == s for ap in active_positions): continue

                try:
                    # تحليل "المسار القادم" عبر شمعات الـ 5 دقائق
                    ohlcv = ex.fetch_ohlcv(s, timeframe='5m', limit=20)
                    df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                    
                    last_price = df['c'].iloc[-1]
                    # قياس "تسارع السعر" في آخر 15 دقيقة
                    price_velocity = (df['c'].iloc[-1] - df['c'].iloc[-3]) / df['c'].iloc[-3]
                    # قياس "ضغط السيولة"
                    volume_surge = df['v'].iloc[-1] / df['v'].mean()

                    trade_side = None
                    # التنبؤ: إذا كان السعر يتسارع وحجم التداول ارتفع فجأة بضعف المتوسط
                    if volume_surge > 2.0:
                        if price_velocity > 0.005: trade_side = 'buy'   # توقع استمرار الانفجار للأعلى
                        elif price_velocity < -0.005: trade_side = 'sell' # توقع استمرار الانهيار للأسفل

                    if trade_side:
                        ex.set_leverage(LEVERAGE, s, params={'openType': 2, 'positionType': (1 if trade_side=='buy' else 2)})
                        qty = (ENTRY_AMOUNT_USDT * LEVERAGE) / last_price
                        ex.create_market_order(s, trade_side, float(ex.amount_to_precision(s, qty)), 
                                              params={'openType': 2, 'positionType': (1 if trade_side=='buy' else 2), 'settle': 'USDT'})
                        
                        log_msg = f"🔮 Predicting {trade_side.upper()} on {s} (Velocity: {price_velocity:.2%}, Vol Surge: {volume_surge:.1f}x)"
                        st.session_state.trade_logs.append(f"[{datetime.now().strftime('%H:%M')}] {log_msg}")
                        st.info(log_msg)
                        break 
                except: continue

        # عرض سجل العمليات
        if st.session_state.trade_logs:
            with st.expander("📜 Trade History & Logic Logs", expanded=True):
                for log in reversed(st.session_state.trade_logs[-10:]):
                    st.write(log)

        time.sleep(30)
        st.rerun()
    except Exception as e:
        st.error(f"Waiting for network update... {e}")
        time.sleep(20)
        st.rerun()
        
