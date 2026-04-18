import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import time

# --- 1. STRATEGIC CONFIGURATION ---
LEVERAGE = 5
MAX_TRADES = 5         # Fixed at 5 trades for your $60 balance ($12 each)
TP_TARGET = 0.04        # 4% Target Profit
SL_LIMIT = -0.015       # 1.5% Strict Stop Loss
TRADE_DURATION_MINS = 30 # Predictive Window

st.set_page_config(page_title="AI 5-Trade Predictor", layout="wide")
st.title("🤖 AI 5-Trade Predictive Engine")
st.subheader("Compounding $60 into $12 slots with 30-min trend forecasting")

# Session States
if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- 2. CONTROLS ---
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

if st.sidebar.button("🚀 Start Strategic Engine"):
    if api_key and api_secret: st.session_state.running = True
if st.sidebar.button("🚨 Emergency Stop"):
    st.session_state.running = False

# --- 3. PREDICTIVE BRAIN (Analyzing the Path) ---
def predict_next_move(ex, symbol):
    try:
        # Looking at the last 30 minutes to predict the next 30
        ohlcv = ex.fetch_ohlcv(symbol, timeframe='1m', limit=30)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        
        current_p = df['close'].iloc[-1]
        old_p = df['close'].iloc[0]
        
        # Trend Strength Calculation
        trend_strength = (current_p - old_p) / old_p
        
        # Forecast: If trend is strong and volume is healthy, enter
        if trend_strength > 0.004 and df['vol'].iloc[-1] > df['vol'].mean():
            return 'buy'
        elif trend_strength < -0.004 and df['vol'].iloc[-1] > df['vol'].mean():
            return 'sell'
        return None
    except: return None

# --- 4. EXECUTION ENGINE ---
if st.session_state.running and api_key and api_secret:
    try:
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        
        # Calculate Compounding Balance
        balance = ex.fetch_balance()
        total_equity = balance['total'].get('USDT', 0)
        dynamic_entry = total_equity / MAX_TRADES

        # A. Monitoring & Intelligent Exit
        for sym, data in list(st.session_state.positions.items()):
            try:
                ticker = ex.fetch_ticker(sym)
                pnl = (ticker['last'] - data['entry']) / data['entry'] if data['side'] == 'buy' else (data['entry'] - ticker['last']) / data['entry']
                mins_passed = (datetime.now() - data['start_time']).total_seconds() / 60
                
                # Exit if Target hit, Stop Loss hit, or 30-min window ends while in profit
                if pnl >= TP_TARGET or pnl <= SL_LIMIT or (mins_passed >= TRADE_DURATION_MINS and pnl > 0):
                    side_close = 'sell' if data['side'] == 'buy' else 'buy'
                    ex.create_market_order(sym, side_close, data['amount'], params={'openType': 2, 'positionType': (2 if data['side'] == 'buy' else 1)})
                    del st.session_state.positions[sym]
                    st.success(f"Strategy Completed for {sym}")
            except: continue

        # B. Scanning & Predictive Entry
        if len(st.session_state.positions) < MAX_TRADES:
            tickers = ex.fetch_tickers()
            symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT')][:30]
            
            for s in symbols:
                if s in st.session_state.positions: continue
                if len(st.session_state.positions) >= MAX_TRADES: break
                
                prediction = predict_next_move(ex, s)
                if prediction:
                    try:
                        ex.set_leverage(LEVERAGE, s)
                        last_p = tickers[s]['last']
                        # Execute with $12 (Calculated from $60/5)
                        amt = float(ex.amount_to_precision(s, (dynamic_entry * LEVERAGE) / last_p))
                        ex.create_market_order(s, prediction, amt, params={'openType': 2, 'positionType': (1 if prediction == 'buy' else 2)})
                        
                        st.session_state.positions[s] = {'side': prediction, 'entry': last_p, 'amount': amt, 'start_time': datetime.now()}
                        st.info(f"🚀 AI Entry: {prediction.upper()} {s} at ${dynamic_entry:.2f}")
                        break 
                    except: continue

        # --- LIVE DASHBOARD ---
        st.divider()
        col1, col2 = st.columns(2)
        col1.metric("Equity (Current)", f"${total_equity:.2f}")
        col2.metric("Trade Slot Value", f"${dynamic_entry:.2f}")
        
        if st.session_state.positions:
            st.dataframe(pd.DataFrame(st.session_state.positions).T[['side', 'entry']], use_container_width=True)

        time.sleep(20)
        st.rerun()

    except Exception as e:
        st.warning(f"Forecasting market paths... {e}")
        time.sleep(10)
        st.rerun()
            
