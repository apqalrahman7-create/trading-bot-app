import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import time

# --- 1. SETTINGS & RULES ---
LEVERAGE = 5
MAX_TRADES = 10         
TP_TARGET = 0.04        # 4% Target Profit
SL_LIMIT = -0.02        # 2% Stop Loss protection
TRADE_DURATION_MINS = 30 
ANALYSIS_TIMEFRAME = '2m' # Analysis interval

st.set_page_config(page_title="AI Trading Pro", layout="wide")
st.title("🤖 AI Autonomous Execution Engine")
st.subheader("Fast 2m Analysis | Auto-Compounding | 40 Symbol Scanner")

# State Management
if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- 2. SIDEBAR CONTROLS ---
st.sidebar.header("🔑 API Credentials")
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

if st.sidebar.button("🚀 START TRADING"):
    if api_key and api_secret: st.session_state.running = True
if st.sidebar.button("🚨 STOP & LIQUIDATE"):
    st.session_state.running = False

# --- 3. PREDICTIVE ANALYSIS (THE BRAIN) ---
def analyze_and_predict(ex, symbol):
    try:
        # Fetch last 15 candles for the 2-minute timeframe
        ohlcv = ex.fetch_ohlcv(symbol, timeframe=ANALYSIS_TIMEFRAME, limit=15)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        
        # Calculate momentum: Current price vs Average of last 15 candles
        current_p = df['close'].iloc[-1]
        moving_avg = df['close'].mean()
        
        # Determine direction based on price strength
        # BUY if price is above average and trending up
        if current_p > moving_avg and current_p > df['close'].iloc[-2]:
            return 'buy'
        # SELL if price is below average and trending down
        elif current_p < moving_avg and current_p < df['close'].iloc[-2]:
            return 'sell'
        return None
    except:
        return None

# --- 4. EXECUTION ENGINE ---
if st.session_state.running and api_key and api_secret:
    try:
        # Initialize Exchange (MEXC Swap)
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        
        # Fetch Balance & Calculate Compounding Amount
        balance = ex.fetch_balance()
        total_equity = balance['total'].get('USDT', 0)
        # Risk Management: Use 15% of total equity per trade
        dynamic_entry = max(11, total_equity * 0.15) 

        # A. Position Monitoring & Auto-Exit
        for sym, data in list(st.session_state.positions.items()):
            ticker = ex.fetch_ticker(sym)
            pnl = (ticker['last'] - data['entry']) / data['entry'] if data['side'] == 'buy' else (data['entry'] - ticker['last']) / data['entry']
            mins_passed = (datetime.now() - data['start_time']).total_seconds() / 60
            
            if pnl >= TP_TARGET or pnl <= SL_LIMIT or mins_passed >= TRADE_DURATION_MINS:
                side_to_close = 'sell' if data['side'] == 'buy' else 'buy'
                pos_idx = 2 if data['side'] == 'buy' else 1
                ex.create_market_order(sym, side_to_close, data['amount'], params={'positionType': pos_idx})
                del st.session_state.positions[sym]
                st.success(f"Position Closed: {sym} | PNL: {pnl*100:.2f}%")

        # B. Scanning Market & Executing Trades
        if len(st.session_state.positions) < MAX_TRADES:
            all_tickers = ex.fetch_tickers()
            # Scan top 40 USDT Perpetual pairs
            symbols = [s for s in all_tickers.keys() if s.endswith('/USDT:USDT')][:40]
            
            for s in symbols:
                if s in st.session_state.positions: continue
                if len(st.session_state.positions) >= MAX_TRADES: break
                
                prediction = analyze_and_predict(ex, s)
                if prediction:
                    try:
                        last_price = all_tickers[s]['last']
                        # Calculate exact amount with Leverage
                        raw_amount = (dynamic_entry * LEVERAGE) / last_price
                        final_amount = float(ex.amount_to_precision(s, raw_amount))
                        
                        # Set Leverage & Execute Market Order
                        ex.set_leverage(LEVERAGE, s)
                        p_idx = 1 if prediction == 'buy' else 2
                        ex.create_market_order(s, prediction, final_amount, params={'positionType': p_idx})
                        
                        # Save position details
                        st.session_state.positions[s] = {
                            'side': prediction, 'entry': last_price, 'amount': final_amount,
                            'start_time': datetime.now(), 'invested': dynamic_entry
                        }
                        st.info(f"🚀 AI Order Placed: {prediction.upper()} on {s}")
                        break # Process one trade per cycle
                    except Exception as e:
                        continue

        # --- 5. DASHBOARD UPDATE ---
        col1, col2, col3 = st.columns(3)
        col1.metric("Wallet Balance", f"${total_equity:.2f}")
        col2.metric("Next Entry Size", f"${dynamic_entry:.2f}")
        col3.metric("Active Trades", len(st.session_state.positions))
        
        if st.session_state.positions:
            df = pd.DataFrame(st.session_state.positions).T
            st.dataframe(df[['side', 'entry', 'invested']], use_container_width=True)

        time.sleep(20) # Refresh cycle
        st.rerun()

    except Exception as e:
        st.warning(f"Scanning Market Signals... {e}")
        time.sleep(10)
        st.rerun()
        
