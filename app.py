import streamlit as st
import ccxt
import time
from datetime import datetime
import pandas as pd
import pandas_ta as ta

# --- CONFIGURATION ---
LEVERAGE = 5
MAX_TRADES = 10         
TP_TARGET = 0.04        # 4% Take Profit
SL_LIMIT = -0.02        # 2% Stop Loss
TRADE_DURATION_MINS = 30 
ANALYSIS_TIMEFRAME = '2m' # 2-Minute Analysis as requested

st.set_page_config(page_title="AI 2Min Predictor", layout="wide")
st.title("⚡ AI 2-Minute Fast Analysis Bot")
st.subheader("Scanning 40 Symbols | 2m Chart Prediction | Compounding")

if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- SIDEBAR ---
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

if st.sidebar.button("🚀 START FAST ANALYSIS"):
    if api_key and api_secret: st.session_state.running = True

if st.sidebar.button("🚨 STOP & LIQUIDATE"):
    st.session_state.running = False

# --- PREDICTION LOGIC (2-MINUTE FOCUS) ---
def get_fast_prediction(ex, symbol):
    try:
        # Fetch last 20 candles of 2-minute timeframe
        ohlcv = ex.fetch_ohlcv(symbol, timeframe=ANALYSIS_TIMEFRAME, limit=20)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        
        # Fast Indicators: EMA 9 and RSI 7 for quick response
        df['RSI'] = ta.rsi(df['close'], length=7)
        df['EMA_FAST'] = ta.ema(df['close'], length=9)
        
        last = df.iloc[-1]
        
        # Prediction: Price crossing EMA Fast with RSI momentum
        if last['close'] > last['EMA_FAST'] and 50 < last['RSI'] < 75:
            return 'buy'
        elif last['close'] < last['EMA_FAST'] and 25 < last['RSI'] < 50:
            return 'sell'
        return None
    except:
        return None

# --- MAIN ENGINE ---
if st.session_state.running:
    try:
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        
        while st.session_state.running:
            balance = ex.fetch_balance()
            total_equity = balance['total'].get('USDT', 0)
            free_usdt = balance['free'].get('USDT', 0)
            # Compounding Rule: 10% of Total Equity
            dynamic_entry = max(10, total_equity * 0.10) 

            # 1. Monitor Positions
            for sym, data in list(st.session_state.positions.items()):
                ticker = ex.fetch_ticker(sym)
                pnl = (ticker['last'] - data['entry']) / data['entry'] if data['side'] == 'buy' else (data['entry'] - ticker['last']) / data['entry']
                mins_passed = (datetime.now() - data['start_time']).total_seconds() / 60
                
                if pnl >= TP_TARGET or pnl <= SL_LIMIT or mins_passed >= TRADE_DURATION_MINS:
                    side_close = 'sell' if data['side'] == 'buy' else 'buy'
                    p_idx = 2 if data['side'] == 'buy' else 1
                    ex.create_market_order(sym, side_close, data['amount'], params={'positionType': p_idx})
                    del st.session_state.positions[sym]
                    st.toast(f"Closed {sym} | PNL: {pnl*100:.2f}%")

            # 2. Fast Analysis & Entry (40 Symbols)
            if len(st.session_state.positions) < MAX_TRADES and free_usdt > dynamic_entry:
                tickers = ex.fetch_tickers()
                symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT')][:40]
                
                for s in symbols:
                    if s in st.session_state.positions: continue
                    if len(st.session_state.positions) >= MAX_TRADES: break
                    
                    prediction = get_fast_prediction(ex, s)
                    if prediction:
                        try:
                            last_p = tickers[s]['last']
                            raw_amt = (dynamic_entry * LEVERAGE) / last_p
                            final_amt = float(ex.amount_to_precision(s, raw_amt))
                            
                            p_idx = 1 if prediction == 'buy' else 2
                            ex.set_leverage(LEVERAGE, s, params={'positionType': p_idx})
                            ex.create_market_order(s, prediction, final_amt, params={'positionType': p_idx})
                            
                            st.session_state.positions[s] = {
                                'side': prediction, 'entry': last_p, 'amount': final_amt,
                                'start_time': datetime.now(), 'capital': dynamic_entry
                            }
                            st.success(f"⚡ 2m Analysis: Predicted {prediction.upper()} for {s}")
                            break 
                        except: continue

            # UI Update
            st.sidebar.metric("Portfolio Value", f"${total_equity:.2f}")
            st.sidebar.metric("Compound Trade Size", f"${dynamic_entry:.2f}")
            time.sleep(15)
            st.rerun()

    except Exception as e:
        st.error(f"Engine Alert: {e}")
        time.sleep(10)
        st.rerun()
        
