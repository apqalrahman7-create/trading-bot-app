import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import time

# --- 1. SYSTEM CONFIGURATION ---
LEVERAGE = 5            # 5X Leverage
MAX_TRADES = 10         # Maximum simultaneous positions
TP_TARGET = 0.04        # 4% Take Profit Target
SL_LIMIT = -0.02        # 2% Stop Loss protection
TRADE_DURATION_MINS = 30 # Time-based exit
ANALYSIS_TIMEFRAME = '2m' # Fast 2-minute candle analysis

st.set_page_config(page_title="AI Predictive Engine", layout="wide")
st.title("🤖 AI Autonomous Predictive Engine")
st.subheader("Dynamic Compounding | Long & Short | 40 Symbol Scan")

# Initialize Session State
if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- 2. SIDEBAR CONTROLS ---
st.sidebar.header("🔑 API Credentials")
api_key = st.sidebar.text_input("MEXC API Key", type="password")
api_secret = st.sidebar.text_input("MEXC Secret Key", type="password")

col_start, col_stop = st.sidebar.columns(2)
if col_start.button("🚀 START"):
    if api_key and api_secret: st.session_state.running = True
if col_stop.button("🚨 STOP"):
    st.session_state.running = False

# --- 3. PREDICTIVE LOGIC ENGINE ---
def get_market_prediction(ex, symbol):
    try:
        # Fetch last 15 candles for 2-minute timeframe
        ohlcv = ex.fetch_ohlcv(symbol, timeframe=ANALYSIS_TIMEFRAME, limit=15)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        
        current_price = df['close'].iloc[-1]
        moving_avg = df['close'].mean()
        
        # PREDICTION: BUY if price breaks above average, SELL if below
        if current_price > moving_avg and current_price > df['open'].iloc[-1]:
            return 'buy'
        elif current_price < moving_avg and current_price < df['open'].iloc[-1]:
            return 'sell'
        return None
    except:
        return None

# --- 4. MAIN EXECUTION LOOP ---
if st.session_state.running and api_key and api_secret:
    try:
        # Initialize MEXC Swap connection
        ex = ccxt.mexc({
            'apiKey': api_key, 
            'secret': api_secret, 
            'options': {'defaultType': 'swap'},
            'enableRateLimit': True
        })
        
        # A. WALLET & COMPOUNDING LOGIC
        balance = ex.fetch_balance()
        total_equity = balance['total'].get('USDT', 0)
        free_usdt = balance['free'].get('USDT', 0)
        
        # COMPOUNDING: Entry size is 15% of your growing portfolio
        dynamic_entry = max(11, total_equity * 0.15) 

        # B. ACTIVE POSITION MONITORING
        for sym, data in list(st.session_state.positions.items()):
            ticker = ex.fetch_ticker(sym)
            current_p = ticker['last']
            
            # Real-time PNL Calculation
            if data['side'] == 'buy':
                pnl = (current_p - data['entry']) / data['entry']
            else:
                pnl = (data['entry'] - current_p) / data['entry']
            
            mins_passed = (datetime.now() - data['start_time']).total_seconds() / 60
            
            # Exit Conditions (Profit, Loss, or Time)
            if pnl >= TP_TARGET or pnl <= SL_LIMIT or mins_passed >= TRADE_DURATION_MINS:
                side_to_close = 'sell' if data['side'] == 'buy' else 'buy'
                p_idx = 2 if data['side'] == 'buy' else 1 # Position index for MEXC
                try:
                    ex.create_market_order(sym, side_to_close, data['amount'], params={'openType': 2, 'positionType': p_idx})
                    del st.session_state.positions[sym]
                    st.toast(f"✅ Closed {sym} | Profit: {pnl*100:.2f}%", icon="💰")
                except: pass

        # C. SCANNING 40 SYMBOLS & PREDICTIVE ENTRY
        if len(st.session_state.positions) < MAX_TRADES and free_usdt > dynamic_entry:
            all_tickers = ex.fetch_tickers()
            symbols = [s for s in all_tickers.keys() if s.endswith('/USDT:USDT')][:40]
            
            for s in symbols:
                if s in st.session_state.positions or len(st.session_state.positions) >= MAX_TRADES: break
                
                prediction = get_market_prediction(ex, s)
                if prediction:
                    try:
                        last_price = all_tickers[s]['last']
                        
                        # 1. Set Leverage
                        p_idx = 1 if prediction == 'buy' else 2
                        ex.set_leverage(LEVERAGE, s, params={'openType': 2, 'positionType': p_idx})
                        
                        # 2. Precision and Amount Calculation
                        raw_amount = (dynamic_entry * LEVERAGE) / last_price
                        final_amount = float(ex.amount_to_precision(s, raw_amount))
                        
                        # 3. Market Execution with necessary MEXC parameters
                        ex.create_market_order(s, prediction, final_amount, params={'openType': 2, 'positionType': p_idx})
                        
                        # 4. Save to Session
                        st.session_state.positions[s] = {
                            'side': prediction, 'entry': last_price, 'amount': final_amount,
                            'start_time': datetime.now(), 'invested_capital': dynamic_entry
                        }
                        st.success(f"🚀 AI Order: {prediction.upper()} on {s}")
                        break # One order per cycle for security
                    except: continue

        # D. LIVE DASHBOARD
        st.divider()
        c1, c2, col_trades = st.columns(3)
        c1.metric("Portfolio Total", f"${total_equity:.2f}")
        c2.metric("Next Compound Trade", f"${dynamic_entry:.2f}")
        col_trades.metric("Open Trades", len(st.session_state.positions))
        
        if st.session_state.positions:
            st.write("### 📈 Active Predictive Positions")
            df = pd.DataFrame(st.session_state.positions).T
            st.dataframe(df[['side', 'entry', 'invested_capital']], use_container_width=True)

        time.sleep(20) # Fast refresh cycle
        st.rerun()

    except Exception as e:
        st.warning(f"AI Engine Scanning... {e}")
        time.sleep(10)
        st.rerun()
        
