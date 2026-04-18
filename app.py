import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import time

# --- 1. SYSTEM RULES ---
LEVERAGE = 5
MAX_TRADES = 10         
TP_TARGET = 0.04        # 4% Target
SL_LIMIT = -0.02        # 2% Stop Loss
TRADE_DURATION_MINS = 30 
ANALYSIS_TIMEFRAME = '2m' # Fast 2-min analysis

st.set_page_config(page_title="AI Integrated Engine", layout="wide")
st.title("🤖 AI Autonomous Integrated Bot")
st.subheader("All-in-One Engine (No External Files)")

# Session State for stability
if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- 2. SIDEBAR CONTROLS ---
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

if st.sidebar.button("🚀 START ENGINE"):
    if api_key and api_secret: st.session_state.running = True
if st.sidebar.button("🚨 EMERGENCY STOP"):
    st.session_state.running = False

# --- 3. THE INTEGRATED CORE (The Engine) ---
if st.session_state.running and api_key and api_secret:
    try:
        # Direct connection to MEXC
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        
        # Balance & Compound Logic
        balance = ex.fetch_balance()
        total_equity = balance['total'].get('USDT', 0)
        # Compounding trade size (15% of total wallet)
        dynamic_entry = max(11, total_equity * 0.15) 

        # A. MONITOR & EXIT LOGIC (Integrated)
        for sym, data in list(st.session_state.positions.items()):
            ticker = ex.fetch_ticker(sym)
            pnl = (ticker['last'] - data['entry']) / data['entry'] if data['side'] == 'buy' else (data['entry'] - ticker['last']) / data['entry']
            mins_passed = (datetime.now() - data['start_time']).total_seconds() / 60
            
            if pnl >= TP_TARGET or pnl <= SL_LIMIT or mins_passed >= TRADE_DURATION_MINS:
                side_close = 'sell' if data['side'] == 'buy' else 'buy'
                ex.create_market_order(sym, side_close, data['amount'], params={'positionType': (2 if data['side'] == 'buy' else 1)})
                del st.session_state.positions[sym]
                st.toast(f"Closed {sym} | PNL: {pnl*100:.2f}%")

        # B. PREDICTIVE ANALYSIS & ENTRY (Integrated)
        if len(st.session_state.positions) < MAX_TRADES:
            all_tickers = ex.fetch_tickers()
            symbols = [s for s in all_tickers.keys() if s.endswith('/USDT:USDT')][:40]
            
            for s in symbols:
                if s in st.session_state.positions: continue
                if len(st.session_state.positions) >= MAX_TRADES: break
                
                # Fast 2m Analysis
                ohlcv = ex.fetch_ohlcv(s, timeframe=ANALYSIS_TIMEFRAME, limit=10)
                df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
                curr_p = df['close'].iloc[-1]
                avg_p = df['close'].mean()
                
                # Signal: Price momentum + Trend
                side = 'buy' if curr_p > avg_p and curr_p > df['open'].iloc[-1] else 'sell' if curr_p < avg_p and curr_p < df['open'].iloc[-1] else None
                
                if side:
                    try:
                        amt = float(ex.amount_to_precision(s, (dynamic_entry * LEVERAGE) / curr_p))
                        ex.set_leverage(LEVERAGE, s)
                        ex.create_market_order(s, side, amt, params={'positionType': (1 if side == 'buy' else 2)})
                        st.session_state.positions[s] = {'side': side, 'entry': curr_p, 'amount': amt, 'start_time': datetime.now(), 'capital': dynamic_entry}
                        st.info(f"🚀 AI Entered {side.upper()} {s}")
                        break 
                    except: continue

        # --- 4. DASHBOARD ---
        c1, c2, c3 = st.columns(3)
        c1.metric("Wallet Total", f"${total_equity:.2f}")
        c2.metric("Compound Entry", f"${dynamic_entry:.2f}")
        c3.metric("Open Trades", len(st.session_state.positions))
        
        if st.session_state.positions:
            st.dataframe(pd.DataFrame(st.session_state.positions).T[['side', 'entry', 'capital']], use_container_width=True)

        time.sleep(20)
        st.rerun()

    except Exception as e:
        st.warning(f"Engine scanning for signals... {e}")
        time.sleep(10)
        st.rerun()
        
