import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. إعداد التحديث الهادئ (كل 30 ثانية) لمنع انهيار المتصفح ---
st_autorefresh(interval=30 * 1000, key="stable_refresh")

# --- 2. CONFIGURATION ---
LEVERAGE = 5
MAX_TRADES = 10         
TP_TARGET = 0.04        
SL_LIMIT = -0.02        
TRADE_DURATION_MINS = 30 

st.set_page_config(page_title="AI Stable Bot", layout="wide")
st.title("🛡️ AI Stable Engine (No-Crash Version)")

if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- 3. SIDEBAR CONTROLS ---
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

if st.sidebar.button("🚀 START"): st.session_state.running = True
if st.sidebar.button("🚨 STOP"): st.session_state.running = False

# --- 4. PREDICTION & TRADING ENGINE ---
if st.session_state.running and api_key and api_secret:
    try:
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        
        # A. WALLET & COMPOUNDING
        balance = ex.fetch_balance()
        total_equity = balance['total'].get('USDT', 0)
        dynamic_entry = max(10, total_equity * 0.10)

        # B. MONITOR POSITIONS
        for sym, data in list(st.session_state.positions.items()):
            ticker = ex.fetch_ticker(sym)
            pnl = (ticker['last'] - data['entry']) / data['entry'] if data['side'] == 'buy' else (data['entry'] - ticker['last']) / data['entry']
            mins_passed = (datetime.now() - data['start_time']).total_seconds() / 60
            
            if pnl >= TP_TARGET or pnl <= SL_LIMIT or mins_passed >= TRADE_DURATION_MINS:
                side_close = 'sell' if data['side'] == 'buy' else 'buy'
                ex.create_market_order(sym, side_close, data['amount'], params={'positionType': (2 if data['side'] == 'buy' else 1)})
                del st.session_state.positions[sym]
                st.toast(f"Closed {sym}")

        # C. SCAN & PREDICT (2m Timeframe)
        if len(st.session_state.positions) < MAX_TRADES:
            tickers = ex.fetch_tickers()
            symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT')][:40]
            for s in symbols:
                if s in st.session_state.positions or len(st.session_state.positions) >= MAX_TRADES: break
                
                # Fast Analysis
                ohlcv = ex.fetch_ohlcv(s, timeframe='2m', limit=20)
                df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
                df['RSI'] = ta.rsi(df['close'], length=7)
                df['EMA'] = ta.ema(df['close'], length=9)
                
                last = df.iloc[-1]
                side = 'buy' if last['close'] > last['EMA'] and 50 < last['RSI'] < 75 else 'sell' if last['close'] < last['EMA'] and 25 < last['RSI'] < 50 else None
                
                if side:
                    ex.set_leverage(LEVERAGE, s)
                    amt = float(ex.amount_to_precision(s, (dynamic_entry * LEVERAGE) / last['close']))
                    ex.create_market_order(s, side, amt, params={'positionType': (1 if side == 'buy' else 2)})
                    st.session_state.positions[s] = {'side': side, 'entry': last['close'], 'amount': amt, 'start_time': datetime.now()}
                    break

        # --- D. STATIC DASHBOARD (NO CRASH) ---
        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("Equity", f"${total_equity:.2f}")
        c2.metric("Trade Size", f"${dynamic_entry:.2f}")
        c3.metric("Trades", len(st.session_state.positions))
        
        if st.session_state.positions:
            st.dataframe(pd.DataFrame(st.session_state.positions).T[['side', 'entry']], use_container_width=True)

    except Exception as e:
        st.warning(f"Connecting to Market... {e}")

st.caption("Auto-refreshing every 30s. Please disable Browser Translation for this page.")
