import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import time

# --- إعدادات النظام ---
LEVERAGE = 5
MAX_TRADES = 10         
TP_TARGET = 0.04        # هدف 4%
SL_LIMIT = -0.02        # حماية 2%
TRADE_DURATION_MINS = 30 
ANALYSIS_TIMEFRAME = '2m' 

st.set_page_config(page_title="AI Stable Bot", layout="wide")
st.title("🤖 AI Autonomous Bot (Stable Version)")

if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- واجهة التحكم ---
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

if st.sidebar.button("🚀 START"):
    if api_key and api_secret: st.session_state.running = True
if st.sidebar.button("🚨 STOP"):
    st.session_state.running = False

# --- دالة التحليل الذكي (بدون مكتبات خارجية) ---
def get_prediction(ex, symbol):
    try:
        ohlcv = ex.fetch_ohlcv(symbol, timeframe=ANALYSIS_TIMEFRAME, limit=10)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        
        avg_price = df['close'].mean()
        current_p = df['close'].iloc[-1]
        # تحليل اتجاه آخر 3 شموع
        is_uptrend = all(df['close'].tail(3) > df['open'].tail(3))
        is_downtrend = all(df['close'].tail(3) < df['open'].tail(3))

        if current_p > avg_price and is_uptrend:
            return 'buy'
        elif current_p < avg_price and is_downtrend:
            return 'sell'
        return None
    except:
        return None

# --- المحرك الرئيسي ---
if st.session_state.running and api_key and api_secret:
    try:
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        
        balance = ex.fetch_balance()
        total_equity = balance['total'].get('USDT', 0)
        dynamic_entry = max(10, total_equity * 0.10) # ربح تراكمي 10%

        # مراقبة الصفقات
        for sym, data in list(st.session_state.positions.items()):
            ticker = ex.fetch_ticker(sym)
            pnl = (ticker['last'] - data['entry']) / data['entry'] if data['side'] == 'buy' else (data['entry'] - ticker['last']) / data['entry']
            mins = (datetime.now() - data['start_time']).total_seconds() / 60
            
            if pnl >= TP_TARGET or pnl <= SL_LIMIT or mins >= TRADE_DURATION_MINS:
                side_close = 'sell' if data['side'] == 'buy' else 'buy'
                ex.create_market_order(sym, side_close, data['amount'], params={'positionType': (2 if data['side'] == 'buy' else 1)})
                del st.session_state.positions[sym]
                st.toast(f"Closed {sym}")

        # فتح صفقات جديدة (تحليل 40 عملة)
        if len(st.session_state.positions) < MAX_TRADES:
            tickers = ex.fetch_tickers()
            symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT')][:40]
            for s in symbols:
                if s in st.session_state.positions: continue
                
                prediction = get_prediction(ex, s)
                if prediction:
                    last_p = tickers[s]['last']
                    amt = float(ex.amount_to_precision(s, (dynamic_entry * LEVERAGE) / last_p))
                    ex.create_market_order(s, prediction, amt, params={'positionType': (1 if prediction == 'buy' else 2)})
                    st.session_state.positions[s] = {'side': prediction, 'entry': last_p, 'amount': amt, 'start_time': datetime.now()}
                    st.info(f"🚀 AI Predicts {prediction} for {s}")
                    break

        st.divider()
        st.metric("Portfolio Value", f"${total_equity:.2f}")
        if st.session_state.positions:
            st.dataframe(pd.DataFrame(st.session_state.positions).T[['side', 'entry']], use_container_width=True)

        time.sleep(30)
        st.rerun()

    except Exception as e:
        st.warning(f"Refreshing... {e}")
        time.sleep(10)
        st.rerun()
        
