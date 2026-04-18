import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import time

# --- 1. STRATEGIC SETTINGS ---
LEVERAGE = 5
MAX_TRADES = 5         # Your $60 divided by 5 = $12 per trade
TP_TARGET = 0.04        # 4% Take Profit
SL_LIMIT = -0.02        # 2% Stop Loss
TRADE_DURATION_MINS = 30 

st.set_page_config(page_title="AI Active Predictor", layout="wide")
st.title("⚡ AI Active Prediction Engine")
st.subheader("Fast Execution | Compounding $60 | 5 Slots Mode")

if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- 2. CONTROLS ---
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

if st.sidebar.button("🚀 ACTIVATE ENGINE"):
    if api_key and api_secret: st.session_state.running = True
if st.sidebar.button("🚨 EMERGENCY STOP"):
    st.session_state.running = False

# --- 3. PREDICTIVE LOGIC (Fast Trend Tracking) ---
def get_quick_prediction(ex, symbol):
    try:
        # Analyze the last 10 minutes for immediate path prediction
        ohlcv = ex.fetch_ohlcv(symbol, timeframe='1m', limit=10)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        
        last_price = df['close'].iloc[-1]
        avg_price = df['close'].mean()
        
        # Prediction: If price is moving away from the 10-min average
        if last_price > avg_price: return 'buy'
        elif last_price < avg_price: return 'sell'
        return None
    except: return None

# --- 4. TRADING ENGINE ---
if st.session_state.running and api_key and api_secret:
    try:
        # MEXC specific setup for April 2026
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        
        # Balance Update for Compounding
        balance = ex.fetch_balance()
        total_equity = balance['total'].get('USDT', 0)
        # Each slot gets 20% of current equity (12$ for a 60$ wallet)
        dynamic_entry = total_equity / MAX_TRADES

        # A. Monitoring Active Trades
        for sym, data in list(st.session_state.positions.items()):
            try:
                ticker = ex.fetch_ticker(sym)
                pnl = (ticker['last'] - data['entry']) / data['entry'] if data['side'] == 'buy' else (data['entry'] - ticker['last']) / data['entry']
                mins = (datetime.now() - data['start_time']).total_seconds() / 60
                
                if pnl >= TP_TARGET or pnl <= SL_LIMIT or (mins >= TRADE_DURATION_MINS and pnl > 0):
                    side_close = 'sell' if data['side'] == 'buy' else 'buy'
                    ex.create_market_order(sym, side_close, data['amount'], params={'openType': 2, 'positionType': (2 if data['side'] == 'buy' else 1)})
                    del st.session_state.positions[sym]
                    st.success(f"Profit Realized on {sym}!")
            except: continue

        # B. Scanning 40 Symbols & Immediate Entry
        if len(st.session_state.positions) < MAX_TRADES:
            tickers = ex.fetch_tickers()
            symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT')][:40]
            
            for s in symbols:
                if s in st.session_state.positions or len(st.session_state.positions) >= MAX_TRADES: break
                
                prediction = get_quick_prediction(ex, s)
                if prediction:
                    try:
                        # 1. Set Leverage
                        p_idx = 1 if prediction == 'buy' else 2
                        ex.set_leverage(LEVERAGE, s, params={'openType': 2, 'positionType': p_idx})
                        
                        # 2. Execution with $12 (Compounding)
                        last_p = tickers[s]['last']
                        amt = float(ex.amount_to_precision(s, (dynamic_entry * LEVERAGE) / last_p))
                        ex.create_market_order(s, prediction, amt, params={'openType': 2, 'positionType': p_idx})
                        
                        st.session_state.positions[s] = {'side': prediction, 'entry': last_p, 'amount': amt, 'start_time': datetime.now()}
                        st.info(f"🚀 AI Executed: {prediction.upper()} {s} at ${dynamic_entry:.2f}")
                        break 
                    except: continue

        # Dashboard View
        st.divider()
        col1, col2 = st.columns(2)
        col1.metric("Wallet Balance (Compound)", f"${total_equity:.2f}")
        col2.metric("Trade Slot Size", f"${dynamic_entry:.2f}")
        
        if st.session_state.positions:
            st.dataframe(pd.DataFrame(st.session_state.positions).T[['side', 'entry']], use_container_width=True)

        time.sleep(15)
        st.rerun()

    except Exception as e:
        st.warning(f"Engine is active & scanning... {e}")
        time.sleep(5)
        st.rerun()
        
