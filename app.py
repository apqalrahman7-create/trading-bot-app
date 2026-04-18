import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import time

# --- 1. AI GROWTH CONFIGURATION ---
TP_TARGET = 0.04        # 4% Take Profit per trade
SL_LIMIT = -0.02        # 2% Stop Loss protection
TRADE_DURATION_MINS = 30 # Time-based exit for liquidity
ANALYSIS_TIMEFRAME = '2m' # Fast predictive analysis

st.set_page_config(page_title="AI Hyper-Growth Bot", layout="wide")
st.title("🚀 AI Autonomous Hyper-Growth Engine")
st.subheader("Dynamic Compounding | Predictive Scaling | Multi-Symbol Scan")

# State Management
if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- 2. SIDEBAR CONTROLS ---
st.sidebar.header("🔑 API Credentials")
api_key = st.sidebar.text_input("MEXC API Key", type="password")
api_secret = st.sidebar.text_input("MEXC Secret Key", type="password")

col_start, col_stop = st.sidebar.columns(2)
if col_start.button("🚀 START ENGINE"):
    if api_key and api_secret: st.session_state.running = True
if col_stop.button("🚨 EMERGENCY STOP"):
    st.session_state.running = False

# --- 3. PREDICTIVE LOGIC ---
def get_market_prediction(ex, symbol):
    try:
        # Scan 2-minute candles for momentum
        ohlcv = ex.fetch_ohlcv(symbol, timeframe=ANALYSIS_TIMEFRAME, limit=15)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        
        current_p = df['close'].iloc[-1]
        moving_avg = df['close'].mean()
        
        # PREDICTION: Determine if trend will sustain for the next 30 mins
        if current_p > moving_avg and current_p > df['open'].iloc[-1]:
            return 'buy'
        elif current_p < moving_avg and current_p < df['open'].iloc[-1]:
            return 'sell'
        return None
    except:
        return None

# --- 4. MAIN EXECUTION ENGINE ---
if st.session_state.running and api_key and api_secret:
    try:
        # Connect to MEXC Swap
        ex = ccxt.mexc({
            'apiKey': api_key, 
            'secret': api_secret, 
            'options': {'defaultType': 'swap'},
            'enableRateLimit': True
        })
        
        # A. UPDATE COMPOUNDING BASE
        balance = ex.fetch_balance()
        total_equity = balance['total'].get('USDT', 0)
        free_usdt = balance['free'].get('USDT', 0)
        
        # AUTO-SCALING LOGIC (Leverage & Trade Count increases with balance)
        if total_equity < 100:
            current_leverage = 5
            max_active_trades = 10
        elif total_equity < 1000:
            current_leverage = 10
            max_active_trades = 15
        else: # For 2000$ and above
            current_leverage = 20
            max_active_trades = 20

        # Dynamic Entry Calculation (Compound Interest Effect)
        dynamic_entry_usd = total_equity / max_active_trades

        # B. MONITOR & AUTO-EXIT (4% OR 30 MINS)
        for sym, data in list(st.session_state.positions.items()):
            try:
                ticker = ex.fetch_ticker(sym)
                current_price = ticker['last']
                
                # Real-time PNL calculation
                if data['side'] == 'buy':
                    pnl = (current_price - data['entry']) / data['entry']
                else:
                    pnl = (data['entry'] - current_price) / data['entry']
                
                mins_passed = (datetime.now() - data['start_time']).total_seconds() / 60
                
                if pnl >= TP_TARGET or pnl <= SL_LIMIT or mins_passed >= TRADE_DURATION_MINS:
                    side_to_close = 'sell' if data['side'] == 'buy' else 'buy'
                    p_idx = 2 if data['side'] == 'buy' else 1
                    ex.create_market_order(sym, side_to_close, data['amount'], params={'openType': 2, 'positionType': p_idx})
                    del st.session_state.positions[sym]
                    st.toast(f"Closed {sym} | PNL: {pnl*100:.2f}%", icon="💰")
            except: continue

        # C. PREDICTIVE ENTRY (Scan 40 Symbols)
        if len(st.session_state.positions) < max_active_trades and free_usdt > dynamic_entry_usd:
            all_tickers = ex.fetch_tickers()
            symbols = [s for s in all_tickers.keys() if s.endswith('/USDT:USDT')][:40]
            
            for s in symbols:
                if s in st.session_state.positions or len(st.session_state.positions) >= max_active_trades: break
                
                t_data = all_tickers[s]
                # Fix NoneType Error
                percentage = t_data.get('percentage')
                if percentage is None: continue
                
                prediction = get_market_prediction(ex, s)
                if prediction:
                    try:
                        # 1. Set Dynamic Leverage
                        p_idx = 1 if prediction == 'buy' else 2
                        ex.set_leverage(current_leverage, s, params={'openType': 2, 'positionType': p_idx})
                        
                        # 2. Precision & Compounding Amount
                        last_p = t_data['last']
                        raw_amt = (dynamic_entry_usd * current_leverage) / last_p
                        final_amt = float(ex.amount_to_precision(s, raw_amt))
                        
                        # 3. Market Execution
                        ex.create_market_order(s, prediction, final_amt, params={'openType': 2, 'positionType': p_idx})
                        
                        # 4. Save State
                        st.session_state.positions[s] = {
                            'side': prediction, 'entry': last_p, 'amount': final_amt,
                            'start_time': datetime.now(), 'invested': dynamic_entry_usd
                        }
                        st.info(f"🚀 AI Predicted {prediction.upper()} on {s} (${dynamic_entry_usd:.2f})")
                        break # One trade per cycle for safety
                    except: continue

        # --- LIVE DASHBOARD ---
        st.divider()
        col_eq, col_lev, col_size = st.columns(3)
        col_eq.metric("Total Equity", f"${total_equity:.2f}")
        col_lev.metric("Current Leverage", f"{current_leverage}X")
        col_size.metric("Trade Size (T) ", f"${dynamic_entry_usd:.2f}")
        
        if st.session_state.positions:
            st.write("### 📊 Active Scalping Positions")
            df_pos = pd.DataFrame(st.session_state.positions).T
            st.dataframe(df_pos[['side', 'entry', 'invested']], use_container_width=True)

        time.sleep(20) # Optimized refresh cycle
        st.rerun()

    except Exception as e:
        st.warning(f"AI Engine Scanning Markets... {e}")
        time.sleep(10)
        st.rerun()
        
