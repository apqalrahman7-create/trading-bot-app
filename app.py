import streamlit as st
import ccxt
import time
from datetime import datetime
import pandas as pd
import pandas_ta as ta

# --- 1. SYSTEM CONFIGURATION ---
LEVERAGE = 5
MAX_TRADES = 10         
TP_TARGET = 0.04        # 4% Take Profit per trade
SL_LIMIT = -0.02        # 2% Stop Loss
TRADE_DURATION_MINS = 30 # Time prediction window
ANALYSIS_TIMEFRAME = '2m' # Analysis on 2-minute candles

st.set_page_config(page_title="AI 2Min Predictor", layout="wide")
st.title("⚡ AI 2-Minute Predictive Engine")
st.subheader("Autonomous Trading | Dynamic Compounding | Smooth UI")

# Initialize Session States
if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- 2. SIDEBAR CONTROLS ---
st.sidebar.header("🔑 API Configuration")
api_key = st.sidebar.text_input("MEXC API Key", type="password")
api_secret = st.sidebar.text_input("MEXC Secret Key", type="password")

if st.sidebar.button("🚀 START AI ENGINE"):
    if api_key and api_secret: 
        st.session_state.running = True
        st.sidebar.success("Engine Started Successfully!")

if st.sidebar.button("🚨 EMERGENCY STOP"):
    st.session_state.running = False
    st.sidebar.warning("Engine Stopped. Manual control required.")

# --- 3. FAST PREDICTION LOGIC (2-Minute Focus) ---
def get_market_prediction(ex, symbol):
    try:
        # Fetch 20 candles of 2m timeframe for trend analysis
        ohlcv = ex.fetch_ohlcv(symbol, timeframe=ANALYSIS_TIMEFRAME, limit=20)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        
        # Predictive Indicators
        df['RSI'] = ta.rsi(df['close'], length=7)
        df['EMA_FAST'] = ta.ema(df['close'], length=9)
        
        last = df.iloc[-1]
        
        # Logic: Price strength + RSI momentum
        if last['close'] > last['EMA_FAST'] and 50 < last['RSI'] < 75:
            return 'buy'
        elif last['close'] < last['EMA_FAST'] and 25 < last['RSI'] < 50:
            return 'sell'
        return None
    except:
        return None

# --- 4. MAIN TRADING ENGINE ---
if st.session_state.running:
    try:
        # Initialize Exchange
        ex = ccxt.mexc({
            'apiKey': api_key, 
            'secret': api_secret, 
            'options': {'defaultType': 'swap'},
            'enableRateLimit': True
        })
        ex.load_markets()

        # UI Placeholder to prevent 'removeChild' browser errors
        data_placeholder = st.empty()

        while st.session_state.running:
            # A. Compounding & Wallet Balance
            balance = ex.fetch_balance()
            total_equity = balance['total'].get('USDT', 0)
            free_usdt = balance['free'].get('USDT', 0)
            
            # Dynamic Entry: 10% of total portfolio (Growth effect)
            dynamic_entry_usd = max(10, total_equity * 0.10) 

            # B. Monitor Active Positions
            for sym, data in list(st.session_state.positions.items()):
                ticker = ex.fetch_ticker(sym)
                current_p = ticker['last']
                
                # Real-time PNL calculation
                if data['side'] == 'buy':
                    pnl = (current_p - data['entry']) / data['entry']
                else:
                    pnl = (data['entry'] - current_p) / data['entry']
                
                mins_passed = (datetime.now() - data['start_time']).total_seconds() / 60
                
                # Exit Management
                if pnl >= TP_TARGET or pnl <= SL_LIMIT or mins_passed >= TRADE_DURATION_MINS:
                    side_to_close = 'sell' if data['side'] == 'buy' else 'buy'
                    p_idx = 2 if data['side'] == 'buy' else 1
                    try:
                        ex.create_market_order(sym, side_to_close, data['amount'], params={'positionType': p_idx})
                        del st.session_state.positions[sym]
                        st.toast(f"Closed {sym} | Profit: {pnl*100:.2f}%")
                    except: pass

            # C. Market Scan & 2m Prediction (40 Symbols)
            if len(st.session_state.positions) < MAX_TRADES and free_usdt > dynamic_entry_usd:
                all_tickers = ex.fetch_tickers()
                symbols = [s for s in all_tickers.keys() if s.endswith('/USDT:USDT')][:40]
                
                for s in symbols:
                    if s in st.session_state.positions: continue
                    if len(st.session_state.positions) >= MAX_TRADES: break
                    
                    prediction = get_market_prediction(ex, s)
                    if prediction:
                        try:
                            last_price = all_tickers[s]['last']
                            raw_amt = (dynamic_entry_usd * LEVERAGE) / last_price
                            final_amt = float(ex.amount_to_precision(s, raw_amt))
                            
                            p_idx = 1 if prediction == 'buy' else 2
                            ex.set_leverage(LEVERAGE, s, params={'positionType': p_idx})
                            ex.create_market_order(s, prediction, final_amt, params={'positionType': p_idx})
                            
                            st.session_state.positions[s] = {
                                'side': prediction, 
                                'entry': last_price, 
                                'amount': final_amt,
                                'start_time': datetime.now(),
                                'compounded_capital': dynamic_entry_usd
                            }
                            st.info(f"⚡ 2m Prediction: {prediction.upper()} for {s}")
                            break # Open one position per cycle for safety
                        except: continue

            # D. Dashboard Refresh (Using Container for Stability)
            with data_placeholder.container():
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Equity", f"${total_equity:.2f}")
                c2.metric("Next Trade Size", f"${dynamic_entry_usd:.2f}")
                c3.metric("Active Trades", len(st.session_state.positions))
                
                if st.session_state.positions:
                    st.write("### 📈 Live Compounding Positions")
                    df = pd.DataFrame(st.session_state.positions).T
                    st.dataframe(df[['side', 'entry', 'start_time', 'compounded_capital']], use_container_width=True)

            time.sleep(25) # Optimized refresh rate
            st.rerun()

    except Exception as e:
        st.error(f"⚠️ System Error: {e}")
        time.sleep(10)
        st.rerun()
        
