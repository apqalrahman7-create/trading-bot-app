import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import time

# --- 1. SETTINGS ---
LEVERAGE = 5
MAX_TRADES = 5         
TP_TARGET = 0.04        # 4% Target
SL_LIMIT = -0.02        # 2% Stop Loss
ANALYSIS_TIMEFRAME = '1m' # Faster 1-min analysis for quick entry

st.set_page_config(page_title="AI Instant Bot", layout="wide")
st.title("⚡ AI Instant Execution Engine")

if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- 2. SIDEBAR ---
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

if st.sidebar.button("🚀 START TRADING NOW"):
    if api_key and api_secret: st.session_state.running = True
if st.sidebar.button("🚨 EMERGENCY STOP"):
    st.session_state.running = False

# --- 3. CORE ENGINE ---
if st.session_state.running and api_key and api_secret:
    try:
        # Initialize with specific MEXC configurations
        ex = ccxt.mexc({
            'apiKey': api_key, 
            'secret': api_secret, 
            'options': {'defaultType': 'swap'},
            'enableRateLimit': True
        })
        
        # Get Balance & Compounding Entry (15% of Wallet)
        balance = ex.fetch_balance()
        total_equity = balance['total'].get('USDT', 0)
        dynamic_entry = max(11, total_equity * 0.15) 

        # A. Monitoring & Auto-Exit
        for sym, data in list(st.session_state.positions.items()):
            ticker = ex.fetch_ticker(sym)
            pnl = (ticker['last'] - data['entry']) / data['entry'] if data['side'] == 'buy' else (data['entry'] - ticker['last']) / data['entry']
            
            if pnl >= TP_TARGET or pnl <= SL_LIMIT:
                side_close = 'sell' if data['side'] == 'buy' else 'buy'
                ex.create_market_order(sym, side_close, data['amount'], params={'openType': 2, 'positionType': (2 if data['side'] == 'buy' else 1)})
                del st.session_state.positions[sym]
                st.success(f"Profit Taken on {sym}")

        # B. INSTANT SCAN & EXECUTION (Top 40 Symbols)
        if len(st.session_state.positions) < MAX_TRADES:
            all_tickers = ex.fetch_tickers()
            symbols = [s for s in all_tickers.keys() if s.endswith('/USDT:USDT')][:40]
            
            for s in symbols:
                if s in st.session_state.positions or len(st.session_state.positions) >= MAX_TRADES: break
                
                # Fetch 5 fast candles
                ohlcv = ex.fetch_ohlcv(s, timeframe=ANALYSIS_TIMEFRAME, limit=5)
                df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
                last_p = df['close'].iloc[-1]
                
                # Simple Logic: Follow the immediate trend (Buy if up, Sell if down)
                side = 'buy' if last_p > df['open'].iloc[-1] else 'sell'
                
                if side:
                    try:
                        # CRITICAL: Prepare the market for entry
                        p_idx = 1 if side == 'buy' else 2
                        # Set Margin Mode to Isolated (Common for bots)
                        try: ex.set_margin_mode('ISOLATED', s, params={'leverage': LEVERAGE})
                        except: pass
                        
                        ex.set_leverage(LEVERAGE, s)
                        
                        # Calculate Amount & Execute Market Order
                        amt = float(ex.amount_to_precision(s, (dynamic_entry * LEVERAGE) / last_p))
                        ex.create_market_order(s, side, amt, params={'openType': 2, 'positionType': p_idx})
                        
                        st.session_state.positions[s] = {'side': side, 'entry': last_p, 'amount': amt, 'start_time': datetime.now()}
                        st.info(f"🚀 AI Executed: {side.upper()} {s}")
                        break 
                    except Exception as e:
                        continue

        # Dashboard Update
        st.divider()
        st.metric("Portfolio Total", f"${total_equity:.2f}")
        if st.session_state.positions:
            st.dataframe(pd.DataFrame(st.session_state.positions).T[['side', 'entry']], use_container_width=True)

        time.sleep(10) # Ultra-fast scanning every 10 seconds
        st.rerun()

    except Exception as e:
        st.warning(f"Engine is Active & Scanning... {e}")
        time.sleep(5)
        st.rerun()
        
