import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import time

# --- 1. SETTINGS & SCALPING RULES ---
LEVERAGE = 5
MAX_TRADES = 10         
TP_TARGET = 0.04        # 4% Target
SL_LIMIT = -0.02        # 2% Protection
TRADE_DURATION_MINS = 30 
ANALYSIS_TIMEFRAME = '2m' 

st.set_page_config(page_title="AI Ultra-Active Bot", layout="wide")
st.title("⚡ AI Ultra-Active Execution Engine")
st.subheader("Aggressive 2m Analysis | Instant Trading | Compounding")

if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- 2. SIDEBAR CONTROLS ---
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

if st.sidebar.button("🚀 ACTIVATE NOW"):
    if api_key and api_secret: st.session_state.running = True
if st.sidebar.button("🚨 STOP"):
    st.session_state.running = False

# --- 3. AGGRESSIVE PREDICTION ENGINE ---
def get_aggressive_prediction(ex, symbol):
    try:
        # Fetch last 10 candles for quick momentum check
        ohlcv = ex.fetch_ohlcv(symbol, timeframe=ANALYSIS_TIMEFRAME, limit=10)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        
        last_close = df['close'].iloc[-1]
        prev_close = df['close'].iloc[-2]
        avg_price = df['close'].mean()
        
        # Aggressive Logic: Enter if price is moving away from the average
        if last_close > avg_price:
            return 'buy'
        elif last_close < avg_price:
            return 'sell'
        return None
    except:
        return None

# --- 4. MAIN ENGINE ---
if st.session_state.running and api_key and api_secret:
    try:
        # Direct connection with Swap options
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        
        balance = ex.fetch_balance()
        total_equity = balance['total'].get('USDT', 0)
        # Using 15% for aggressive compounding growth
        dynamic_entry = max(11, total_equity * 0.15) 

        # A. Monitoring Active Positions
        for sym, data in list(st.session_state.positions.items()):
            ticker = ex.fetch_ticker(sym)
            pnl = (ticker['last'] - data['entry']) / data['entry'] if data['side'] == 'buy' else (data['entry'] - ticker['last']) / data['entry']
            mins_passed = (datetime.now() - data['start_time']).total_seconds() / 60
            
            if pnl >= TP_TARGET or pnl <= SL_LIMIT or mins_passed >= TRADE_DURATION_MINS:
                side_close = 'sell' if data['side'] == 'buy' else 'buy'
                ex.create_market_order(sym, side_close, data['amount'], params={'openType': 2, 'positionType': (2 if data['side'] == 'buy' else 1)})
                del st.session_state.positions[sym]
                st.toast(f"Realized Profit on {sym}")

        # B. Scanning 40 Symbols & Instant Entry
        if len(st.session_state.positions) < MAX_TRADES:
            all_tickers = ex.fetch_tickers()
            symbols = [s for s in all_tickers.keys() if s.endswith('/USDT:USDT')][:40]
            
            for s in symbols:
                if s in st.session_state.positions or len(st.session_state.positions) >= MAX_TRADES: break
                
                prediction = get_aggressive_prediction(ex, s)
                if prediction:
                    try:
                        last_p = all_tickers[s]['last']
                        # Set Leverage First
                        p_idx = 1 if prediction == 'buy' else 2
                        ex.set_leverage(LEVERAGE, s, params={'openType': 2, 'positionType': p_idx})
                        
                        # Calculate Amount & Execute
                        amt = float(ex.amount_to_precision(s, (dynamic_entry * LEVERAGE) / last_p))
                        ex.create_market_order(s, prediction, amt, params={'openType': 2, 'positionType': p_idx})
                        
                        st.session_state.positions[s] = {'side': prediction, 'entry': last_p, 'amount': amt, 'start_time': datetime.now()}
                        st.info(f"🚀 AI Order Placed: {prediction.upper()} {s}")
                        break 
                    except: continue

        # --- Dashboard ---
        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Equity", f"${total_equity:.2f}")
        c2.metric("Next Compound Trade", f"${dynamic_entry:.2f}")
        c3.metric("Open Trades", len(st.session_state.positions))
        
        if st.session_state.positions:
            st.dataframe(pd.DataFrame(st.session_state.positions).T[['side', 'entry']], use_container_width=True)

        time.sleep(15) # Faster scanning cycle
        st.rerun()

    except Exception as e:
        st.warning(f"Scanning Market... {e}")
        time.sleep(5)
        st.rerun()
        
