import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import time

# --- 1. STRATEGIC SETTINGS ---
LEVERAGE = 5            
ENTRY_AMOUNT_USDT = 12  
TP_TARGET = 0.04        
SL_LIMIT = -0.02        
TRADE_DURATION_MINS = 30 

st.set_page_config(page_title="AI Multi-Trader Final", layout="wide")
st.title("🤖 AI Autonomous Multi-Trader")
st.caption("Advanced Market Analysis | Auto-Exit | Stop Function")

# --- INITIALIZE STATE ---
if 'running' not in st.session_state: 
    st.session_state.running = False

# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.header("🔑 Exchange Keys")
    api_key = st.text_input("MEXC API Key", type="password")
    api_secret = st.text_input("MEXC Secret Key", type="password")
    
    st.divider()
    # Control Buttons
    col_start, col_stop = st.columns(2)
    with col_start:
        if st.button("🚀 Start", use_container_width=True):
            if api_key and api_secret:
                st.session_state.running = True
            else:
                st.error("Missing Keys")
    with col_stop:
        if st.button("🛑 Stop", use_container_width=True):
            st.session_state.running = False
            st.warning("System Stopped")

# --- MAIN ENGINE ---
if st.session_state.running:
    try:
        ex = ccxt.mexc({
            'apiKey': api_key,
            'secret': api_secret,
            'options': {'defaultType': 'swap'}
        })

        # 1. Update Balance & Slots
        balance = ex.fetch_balance()
        total_usdt = balance['total'].get('USDT', 0)
        max_slots = int((total_usdt * 0.9) / ENTRY_AMOUNT_USDT)
        if max_slots < 1: max_slots = 1

        # 2. Sync Active Positions
        all_pos = ex.fetch_positions()
        active_positions = [p for p in all_pos if p.get('contracts') and float(p['contracts']) > 0]
        
        # Dashboard
        st.divider()
        st.success("✅ System is LIVE and Scanning...")
        m1, m2, m3 = st.columns(3)
        m1.metric("Wallet Balance", f"${total_usdt:.2f}")
        m2.metric("Active Slots", f"{len(active_positions)} / {max_slots}")
        m3.metric("Cost Per Trade", f"${ENTRY_AMOUNT_USDT:.2f}")

        # 3. EXIT MONITOR
        for p in active_positions:
            try:
                symbol = p['symbol']
                side = p['side']
                entry_p = float(p.get('entryPrice') or 0)
                mark_p = float(p.get('markPrice') or 0)
                if entry_p <= 0: continue

                pnl = (mark_p - entry_p) / entry_p if side == 'long' else (entry_p - mark_p) / entry_p
                open_ts = datetime.fromtimestamp(p.get('timestamp', time.time()*1000) / 1000)
                mins_active = (datetime.now() - open_ts).total_seconds() / 60

                if pnl >= TP_TARGET or pnl <= SL_LIMIT or mins_active >= TRADE_DURATION_MINS:
                    order_side = 'sell' if side == 'long' else 'buy'
                    ex.create_market_order(symbol, order_side, p['contracts'], params={'openType': 2})
                    st.toast(f"✅ Closed {symbol}")
            except: continue

        # 4. ENTRY SCANNER
        if len(active_positions) < max_slots:
            tickers = ex.fetch_tickers()
            symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT')]
            
            for s in symbols[:50]:
                if any(ap['symbol'] == s for ap in active_positions): continue
                if len(active_positions) >= max_slots: break

                ohlcv = ex.fetch_ohlcv(s, timeframe='5m', limit=20)
                df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                last_price = df['c'].iloc[-1]
                high_20 = df['h'].iloc[-15:-1].max()
                low_20 = df['l'].iloc[-15:-1].min()

                trade_side = 'buy' if last_price > high_20 else 'sell' if last_price < low_20 else None

                if trade_side:
                    try:
                        pos_type = 1 if trade_side == 'buy' else 2
                        ex.set_leverage(LEVERAGE, s, params={'openType': 2, 'positionType': pos_type})
                        qty = (ENTRY_AMOUNT_USDT * LEVERAGE) / last_price
                        qty_prec = float(ex.amount_to_precision(s, qty))
                        
                        if qty_prec > 0:
                            ex.create_market_order(s, trade_side, qty_prec, params={'openType': 2, 'positionType': pos_type, 'settle': 'USDT'})
                            st.info(f"🚀 New Slot: {trade_side.upper()} {s}")
                            break
                    except: continue

        if active_positions:
            st.subheader("Live Portfolio")
            st.dataframe(pd.DataFrame(active_positions)[['symbol', 'side', 'entryPrice', 'markPrice', 'unrealizedPnl']], use_container_width=True)

        time.sleep(30)
        st.rerun()

    except Exception as e:
        st.warning(f"Engine refreshing... {e}")
        time.sleep(20)
        st.rerun()
else:
    st.info("System is currently Idle. Press 'Start' to begin trading.")
    
