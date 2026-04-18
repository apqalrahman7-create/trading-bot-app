import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import time

# --- 1. SETTINGS ---
LEVERAGE = 5
MAX_TRADES = 10         # يوزع الرصيد على 10 صفقات للنمو التراكمي
TP_TARGET = 0.04        # هدف 4%
SL_LIMIT = -0.02        # حماية 2%
TRADE_DURATION_MINS = 30 

st.set_page_config(page_title="AI Final Bot", layout="wide")
st.title("🛡️ AI Final Autonomous Bot")
st.subheader("تحليل حقيقي | تنفيذ فوري | ربح تراكمي")

if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- SIDEBAR ---
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

if st.sidebar.button("🚀 تشغيل النظام النهائي"):
    if api_key and api_secret: st.session_state.running = True

# --- THE ENGINE ---
if st.session_state.running and api_key and api_secret:
    try:
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        
        # جلب الرصيد وحساب مبلغ الدخول التراكمي آلياً
        balance = ex.fetch_balance()
        total_equity = balance['total'].get('USDT', 0)
        dynamic_entry = total_equity / MAX_TRADES

        # 1. مراقبة وإغلاق الصفقات (الهدف، الحماية، أو الوقت)
        for sym, data in list(st.session_state.positions.items()):
            try:
                ticker = ex.fetch_ticker(sym)
                pnl = (ticker['last'] - data['entry']) / data['entry'] if data['side'] == 'buy' else (data['entry'] - ticker['last']) / data['entry']
                mins = (datetime.now() - data['start_time']).total_seconds() / 60
                
                if pnl >= TP_TARGET or pnl <= SL_LIMIT or (mins >= TRADE_DURATION_MINS and pnl > 0):
                    ex.create_market_order(sym, 'sell' if data['side'] == 'buy' else 'buy', data['amount'], params={'openType': 2, 'positionType': (2 if data['side'] == 'buy' else 1)})
                    del st.session_state.positions[sym]
                    st.success(f"Profit Closed: {sym}")
            except: continue

        # 2. تحليل السوق وفتح صفقات جديدة (توقع مبني على الزخم)
        if len(st.session_state.positions) < MAX_TRADES:
            tickers = ex.fetch_tickers()
            symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT')][:40]
            
            for s in symbols:
                if s in st.session_state.positions or len(st.session_state.positions) >= MAX_TRADES: break
                
                # التحليل: ننظر لآخر 15 دقيقة (توقع المسار)
                ohlcv = ex.fetch_ohlcv(s, timeframe='1m', limit=15)
                df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
                curr_p = df['close'].iloc[-1]
                avg_p = df['close'].mean()
                
                # شرط الدخول: زخم صاعد أو هابط حقيقي
                side = 'buy' if curr_p > avg_p * 1.002 else 'sell' if curr_p < avg_p * 0.998 else None
                
                if side:
                    try:
                        ex.set_leverage(LEVERAGE, s)
                        amt = float(ex.amount_to_precision(s, (dynamic_entry * LEVERAGE) / curr_p))
                        ex.create_market_order(s, side, amt, params={'openType': 2, 'positionType': (1 if side == 'buy' else 2)})
                        st.session_state.positions[s] = {'side': side, 'entry': curr_p, 'amount': amt, 'start_time': datetime.now()}
                        st.info(f"🚀 AI Found Opportunity: {side.upper()} {s}")
                        break 
                    except: continue

        # عرض الإحصائيات المحدثة
        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("إجمالي المحفظة (تراكمي)", f"${total_equity:.2f}")
        c2.metric("حجم كل صفقة حالياً", f"${dynamic_entry:.2f}")
        if st.session_state.positions:
            st.dataframe(pd.DataFrame(st.session_state.positions).T[['side', 'entry']], use_container_width=True)

        time.sleep(20)
        st.rerun()

    except Exception as e:
        st.warning(f"Engine scanning... {e}")
        time.sleep(10)
        st.rerun()
        
