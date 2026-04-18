import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import time

# --- 1. STRATEGIC SETTINGS (Fast Profit Strategy) ---
LEVERAGE = 10           # Increased to 10x for better 30-min returns
ENTRY_AMOUNT_USDT = 12  
TP_TARGET = 0.03        # 3% price move (30% with 10x leverage)
SL_LIMIT = -0.015       # 1.5% price move safety
TRADE_DURATION_MINS = 30 

st.set_page_config(page_title="AI Future-Sense Trader", layout="wide")
st.title("🤖 AI Future-Sense (30-Min High Momentum)")

if 'running' not in st.session_state: st.session_state.running = False

with st.sidebar:
    st.header("🔑 Exchange Keys")
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    st.divider()
    if st.button("🚀 Start System"): st.session_state.running = True
    if st.button("🛑 Stop System"): st.session_state.running = False

# Helper for RSI (Momentum Analysis)
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1, + rs))

if st.session_state.running:
    try:
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        
        balance = ex.fetch_balance()
        total_usdt = balance['total'].get('USDT', 0)
        max_slots = int((total_usdt * 0.9) / ENTRY_AMOUNT_USDT)

        all_pos = ex.fetch_positions()
        active_positions = [p for p in all_pos if p.get('contracts') and float(p['contracts']) > 0]
        
        st.metric("Portfolio Balance", f"${total_usdt:.2f}")
        st.write(f"Active Slots: {len(active_positions)} / {max_slots}")

        # --- 2. FAST EXIT MONITOR (30-Min Limit) ---
        for p in active_positions:
            try:
                symbol, side = p['symbol'], p['side']
                entry_p = float(p.get('entryPrice') or 0)
                mark_p = float(p.get('markPrice') or 0)
                if entry_p <= 0: continue

                pnl = (mark_p - entry_p) / entry_p if side == 'long' else (entry_p - mark_p) / entry_p
                
                # Time limit logic
                open_ts = datetime.fromtimestamp(p.get('timestamp', time.time()*1000) / 1000)
                mins_active = (datetime.now() - open_ts).total_seconds() / 60

                if pnl >= TP_TARGET or pnl <= SL_LIMIT or mins_active >= TRADE_DURATION_MINS:
                    order_side = 'sell' if side == 'long' else 'buy'
                    ex.create_market_order(symbol, order_side, p['contracts'], params={'openType': 2})
                    st.success(f"30-Min Target/Limit reached for {symbol}")
            except: continue

        # --- 3. FUTURE-SENSE ENTRY (Finding the strongest move) ---
        if len(active_positions) < max_slots:
            tickers = ex.fetch_tickers()
            symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT')]
            
            for s in symbols[:40]: # Scan the requested 40 pairs
                if any(ap['symbol'] == s for ap in active_positions): continue
                if len(active_positions) >= max_slots: break

                ohlcv = ex.fetch_ohlcv(s, timeframe='5m', limit=30)
                df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                
                # Check for "High Volume" (Future indication of big move)
                avg_vol = df['v'].mean()
                curr_vol = df['v'].iloc[-1]
                
                last_price = df['c'].iloc[-1]
                high_barrier = df['h'].iloc[-15:-1].max()
                low_barrier = df['l'].iloc[-11:-1].min()

                # Entry only if there is a breakout AND high volume
                if curr_vol > avg_vol * 1.5: # Volume must be 50% higher than average
                    trade_side = 'buy' if last_price > high_barrier else 'sell' if last_price < low_barrier else None
                    
                    if trade_side:
                        try:
                            pos_type = 1 if trade_side == 'buy' else 2
                            ex.set_leverage(LEVERAGE, s, params={'openType': 2, 'positionType': pos_type})
                            qty = (ENTRY_AMOUNT_USDT * LEVERAGE) / last_price
                            qty_prec = float(ex.amount_to_precision(s, qty))
                            
                            ex.create_market_order(s, trade_side, qty_prec, params={'openType': 2, 'positionType': pos_type, 'settle': 'USDT'})
                            st.info(f"🚀 High Volume Breakout: {trade_side.upper()} {s}")
                            break
                        except: continue

        time.sleep(30)
        st.rerun()
    except Exception as e:
        time.sleep(20)
        st.rerun()
        
