import streamlit as st
import ccxt
import time
from datetime import datetime
import pandas as pd

# --- 1. CONFIGURATION ---
LEVERAGE = 5
MAX_TRADES = 10         
TP_TARGET = 0.04        # 4% Take Profit
SL_LIMIT = -0.02        # 2% Stop Loss
TRADE_DURATION_MINS = 30 

st.set_page_config(page_title="AI Compound Manager", layout="wide")
st.title("🤖 AI Autonomous Compound Manager")
st.subheader("Real-time Analysis | Dynamic Compounding | 30-Min Exit")

# Initialize Session States
if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- 2. SIDEBAR CONTROLS ---
st.sidebar.header("🔑 API Settings")
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

# START BUTTON
if st.sidebar.button("🚀 START ENGINE"):
    if api_key and api_secret: 
        st.session_state.running = True
        st.sidebar.success("Engine is Running...")

# STOP & CLOSE ALL BUTTON
if st.sidebar.button("🚨 STOP & CLOSE ALL"):
    st.session_state.running = False
    st.sidebar.warning("Engine Stopping... Closing Positions.")

# --- 3. TRADING ENGINE ---
if st.session_state.running:
    try:
        ex = ccxt.mexc({
            'apiKey': api_key, 
            'secret': api_secret, 
            'options': {'defaultType': 'swap'},
            'enableRateLimit': True
        })
        ex.load_markets()

        while st.session_state.running:
            # A. WALLET & COMPOUNDING CALCULATION
            balance = ex.fetch_balance()
            total_equity = balance['total'].get('USDT', 0)
            free_usdt = balance['free'].get('USDT', 0)
            
            # Compounding: Entry = 10% of Total Portfolio (Balance + Profits)
            dynamic_entry_usd = max(10, total_equity * 0.10) 

            # B. MONITOR POSITIONS
            for sym, data in list(st.session_state.positions.items()):
                ticker = ex.fetch_ticker(sym)
                current_p = ticker['last']
                
                if data['side'] == 'buy':
                    pnl = (current_p - data['entry']) / data['entry']
                else:
                    pnl = (data['entry'] - current_p) / data['entry']
                
                mins_passed = (datetime.now() - data['start_time']).total_seconds() / 60
                
                # Check Exit Conditions
                if pnl >= TP_TARGET or pnl <= SL_LIMIT or mins_passed >= TRADE_DURATION_MINS:
                    side_to_close = 'sell' if data['side'] == 'buy' else 'buy'
                    pos_type = 2 if data['side'] == 'buy' else 1
                    ex.create_market_order(sym, side_to_close, data['amount'], params={'openType': 2, 'positionType': pos_type})
                    del st.session_state.positions[sym]
                    st.toast(f"Closed {sym} at {pnl*100:.2f}%", icon="✅")

            # C. MARKET SCAN & ENTRY (40 Symbols)
            if len(st.session_state.positions) < MAX_TRADES and free_usdt > dynamic_entry_usd:
                all_tickers = ex.fetch_tickers()
                symbols = [s for s in all_tickers.keys() if s.endswith('/USDT:USDT')][:40]
                
                for s in symbols:
                    if s in st.session_state.positions: continue
                    if len(st.session_state.positions) >= MAX_TRADES: break
                    
                    t_data = all_tickers[s]
                    change = t_data['percentage']
                    
                    # Entry Logic based on Momentum
                    side = 'buy' if change > 1.5 else 'sell' if change < -1.5 else None
                    
                    if side:
                        try:
                            pos_type = 1 if side == 'buy' else 2
                            ex.set_leverage(LEVERAGE, s, params={'openType': 2, 'positionType': pos_type})
                            
                            last_price = t_data['last']
                            raw_amt = (dynamic_entry_usd * LEVERAGE) / last_price
                            final_amt = float(ex.amount_to_precision(s, raw_amt))
                            
                            ex.create_market_order(s, side, final_amt, params={'openType': 2, 'positionType': pos_type})
                            
                            st.session_state.positions[s] = {
                                'side': side, 'entry': last_price, 'amount': final_amt,
                                'start_time': datetime.now(), 'value': dynamic_entry_usd
                            }
                            st.info(f"🚀 AI Entered {side.upper()} {s}")
                            break 
                        except: continue

            # D. LIVE DASHBOARD
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Portfolio (Compounded)", f"${total_equity:.2f}")
            col2.metric("Next Trade Capital", f"${dynamic_entry_usd:.2f}")
            col3.metric("Active Trades", len(st.session_state.positions))
            
            if st.session_state.positions:
                st.table(pd.DataFrame(st.session_state.positions).T[['side', 'entry', 'value']])

            time.sleep(15)
            st.rerun()

        # Shutdown sequence (if loop breaks)
        for sym, data in list(st.session_state.positions.items()):
            side_to_close = 'sell' if data['side'] == 'buy' else 'buy'
            ex.create_market_order(sym, side_to_close, data['amount'])
        st.session_state.positions = {}

    except Exception as e:
        st.error(f"Engine Error: {e}")
        time.sleep(10)
        st.rerun()
        
