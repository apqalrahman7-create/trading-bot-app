import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import time

# --- 1. STRATEGIC SETTINGS ---
LEVERAGE = 5            
MAX_TRADES = 5          
TP_TARGET = 0.04        # 4% Target
SL_LIMIT = -0.02        # 2% Stop Loss
TRADE_DURATION_MINS = 30 

st.set_page_config(page_title="AI Autonomous Trader", layout="wide")
st.title("🤖 AI Autonomous Trader - MEXC Global")
st.subheader("Real-time Analysis | Compound Growth | Auto-Execution")

if 'running' not in st.session_state: st.session_state.running = False

# --- SIDEBAR ---
with st.sidebar:
    st.header("API Configuration")
    api_key = st.text_input("MEXC API Key", type="password")
    api_secret = st.text_input("MEXC Secret Key", type="password")
    if st.button("🚀 Start System"):
        if api_key and api_secret:
            st.session_state.running = True
            st.success("System Engine Started")
        else:
            st.error("Please enter API credentials")

# --- MAIN ENGINE ---
if st.session_state.running:
    try:
        # Initialize MEXC Exchange
        ex = ccxt.mexc({
            'apiKey': api_key,
            'secret': api_secret,
            'options': {'defaultType': 'swap'}
        })

        # 1. Fetch Total Equity for Compounding
        balance = ex.fetch_balance()
        total_usdt = balance['total'].get('USDT', 0)
        
        if total_usdt < 5:
            st.warning("Insufficient USDT balance in Futures wallet.")
            st.stop()

        dynamic_entry_size = total_usdt / MAX_TRADES

        # 2. Monitor Active Positions
        positions = ex.fetch_positions()
        active_positions = [p for p in positions if float(p['contracts']) > 0]
        
        # Display Metrics
        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Equity", f"${total_usdt:.2f}")
        c2.metric("Active Trades", f"{len(active_positions)} / {MAX_TRADES}")
        c3.metric("Trade Size", f"${dynamic_entry_size:.2f}")

        # 3. Exit Logic (Take Profit / Stop Loss / Time)
        for p in active_positions:
            symbol = p['symbol']
            side = p['side'] # 'long' or 'short'
            entry_p = float(p['entryPrice'])
            mark_p = float(p['markPrice'])
            
            pnl = (mark_p - entry_p) / entry_p if side == 'long' else (entry_p - mark_p) / entry_p
            
            # Time calculation
            open_ts = datetime.fromtimestamp(p['timestamp'] / 1000)
            mins_elapsed = (datetime.now() - open_ts).total_seconds() / 60

            if pnl >= TP_TARGET or pnl <= SL_LIMIT or mins_elapsed >= TRADE_DURATION_MINS:
                order_side = 'sell' if side == 'long' else 'buy'
                ex.create_market_order(symbol, order_side, p['contracts'], params={'openType': 2})
                st.success(f"Closed {symbol} | PnL: {pnl*100:.2f}%")

        # 4. Market Scanning & Entry (Breakout Strategy)
        if len(active_positions) < MAX_TRADES:
            tickers = ex.fetch_tickers()
            all_symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT')]
            
            for s in all_symbols[:40]: 
                if any(ap['symbol'] == s for ap in active_positions): continue
                if len(active_positions) >= MAX_TRADES: break

                # Analysis: 5m Candle Chart
                ohlcv = ex.fetch_ohlcv(s, timeframe='5m', limit=15)
                df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                curr_p = df['c'].iloc[-1]
                high_barrier = df['h'].iloc[-11:-1].max()
                low_barrier = df['l'].iloc[-11:-1].min()

                # Entry Signal
                trade_side = 'buy' if curr_p > high_barrier else 'sell' if curr_p < low_barrier else None

                if trade_side:
                    try:
                        # Fix for MEXC setLeverage Error
                        pos_type = 1 if trade_side == 'buy' else 2
                        ex.set_leverage(LEVERAGE, s, params={'openType': 2, 'positionType': pos_type})
                        
                        # Calculate Amount with Precision
                        amount = (dynamic_entry_size * LEVERAGE) / curr_p
                        amount_prec = float(ex.amount_to_precision(s, amount))
                        
                        # Execute Market Order
                        params = {
                            'openType': 2, 
                            'positionType': pos_type,
                            'settle': 'USDT'
                        }
                        ex.create_market_order(s, trade_side, amount_prec, params=params)
                        st.info(f"🚀 New {trade_side.upper()} order placed for {s}")
                        break 
                    except Exception as e:
                        st.error(f"Failed to open {s}: {str(e)[:100]}")
                        continue

        # Display Current Positions Table
        if active_positions:
            st.write("### Current Positions")
            pos_df = pd.DataFrame(active_positions)[['symbol', 'side', 'entryPrice', 'markPrice', 'unrealizedPnl']]
            st.dataframe(pos_df, use_container_width=True)

        time.sleep(30)
        st.rerun()

    except Exception as e:
        st.error(f"System Error: {e}")
        time.sleep(20)
        st.rerun()
        
