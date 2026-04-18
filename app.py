import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import time

# --- 1. STRATEGIC SETTINGS ---
LEVERAGE = 5            
ENTRY_AMOUNT_USDT = 12  # Fixed amount per trade slot
TP_TARGET = 0.04        
SL_LIMIT = -0.02        
TRADE_DURATION_MINS = 30 

st.set_page_config(page_title="AI Dynamic Multi-Trader", layout="wide")
st.title("🤖 AI Dynamic Multi-Trader")
st.subheader("Dynamic Slots | Capital Growth | Auto-Scaling")

if 'running' not in st.session_state: st.session_state.running = False

# --- SIDEBAR ---
with st.sidebar:
    st.header("API Configuration")
    api_key = st.text_input("MEXC API Key", type="password")
    api_secret = st.text_input("MEXC Secret Key", type="password")
    if st.button("🚀 Start Engine"):
        if api_key and api_secret:
            st.session_state.running = True
            st.success("Engine Running")

# --- MAIN ENGINE ---
if st.session_state.running:
    try:
        ex = ccxt.mexc({
            'apiKey': api_key, 'secret': api_secret,
            'options': {'defaultType': 'swap'}
        })

        # 1. Fetch Balance & Calculate Dynamic Slots
        balance = ex.fetch_balance()
        total_usdt = balance['total'].get('USDT', 0)
        
        # Calculate how many trades we can afford (Dynamic MAX_TRADES)
        # We use 90% of balance to be safe with margins
        max_possible_trades = int((total_usdt * 0.9) / ENTRY_AMOUNT_USDT)
        if max_possible_trades < 1: max_possible_trades = 1

        # 2. Get Active Positions
        positions = ex.fetch_positions()
        active_positions = [p for p in positions if float(p['contracts']) > 0]
        
        # Display Metrics
        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Equity", f"${total_usdt:.2f}")
        c2.metric("Active / Max Slots", f"{len(active_positions)} / {max_possible_trades}")
        c3.metric("Entry Per Slot", f"${ENTRY_AMOUNT_USDT:.2f}")

        # --- EXIT MONITOR ---
        for p in active_positions:
            symbol, side = p['symbol'], p['side']
            entry_p, mark_p = float(p['entryPrice']), float(p['markPrice'])
            pnl = (mark_p - entry_p) / entry_p if side == 'long' else (entry_p - mark_p) / entry_p
            
            open_ts = datetime.fromtimestamp(p['timestamp'] / 1000)
            mins_elapsed = (datetime.now() - open_ts).total_seconds() / 60

            if pnl >= TP_TARGET or pnl <= SL_LIMIT or mins_elapsed >= TRADE_DURATION_MINS:
                order_side = 'sell' if side == 'long' else 'buy'
                ex.create_market_order(symbol, order_side, p['contracts'], params={'openType': 2})
                st.success(f"Closed {symbol} | Profit Secured")

        # --- ENTRY SCANNER (Scales with balance) ---
        if len(active_positions) < max_possible_trades:
            tickers = ex.fetch_tickers()
            symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT')]
            
            for s in symbols[:50]: 
                if any(ap['symbol'] == s for ap in active_positions): continue
                if len(active_positions) >= max_possible_trades: break

                ohlcv = ex.fetch_ohlcv(s, timeframe='5m', limit=15)
                df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                curr_p = df['c'].iloc[-1]
                high_b = df['h'].iloc[-11:-1].max()
                low_b = df['l'].iloc[-11:-1].min()

                trade_side = 'buy' if curr_p > high_b else 'sell' if curr_p < low_b else None

                if trade_side:
                    try:
                        pos_type = 1 if trade_side == 'buy' else 2
                        ex.set_leverage(LEVERAGE, s, params={'openType': 2, 'positionType': pos_type})
                        
                        # Use the fixed entry amount (Safe compounding)
                        amount = (ENTRY_AMOUNT_USDT * LEVERAGE) / curr_p
                        amount_prec = float(ex.amount_to_precision(s, amount))
                        
                        ex.create_market_order(s, trade_side, amount_prec, params={
                            'openType': 2, 'positionType': pos_type, 'settle': 'USDT'
                        })
                        st.info(f"🚀 Slot Filled: {trade_side.upper()} {s}")
                        break # Open one per cycle for stability
                    except Exception as e:
                        continue

        time.sleep(30)
        st.rerun()

    except Exception as e:
        st.error(f"System Error: {e}")
        time.sleep(20)
        st.rerun()
        
