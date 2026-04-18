import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import time

# --- AI GROWTH SETTINGS ---
TP_TARGET = 0.04        # 4% Take Profit
SL_LIMIT = -0.02        # 2% Stop Loss
TRADE_DURATION_MINS = 30 
ANALYSIS_TIMEFRAME = '1m' 

st.set_page_config(page_title="AI Active Engine", layout="wide")
st.title("⚡ AI Autonomous Execution (60$ Mode)")
st.subheader("Dividing Balance by 5 Trades for Guaranteed Entry")

if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- SIDEBAR ---
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

if st.sidebar.button("🚀 ACTIVATE ENGINE"):
    if api_key and api_secret: st.session_state.running = True
if st.sidebar.button("🚨 STOP"):
    st.session_state.running = False

# --- CORE EXECUTION ---
if st.session_state.running and api_key and api_secret:
    try:
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        
        # 1. Update Portfolio & Compounding
        balance = ex.fetch_balance()
        total_equity = balance['total'].get('USDT', 0)
        
        # التعديل الجديد: التقسيم على 5 صفقات لضمان أن مبلغ الدخول (12$) مقبول لدى MEXC
        max_trades = 5
        current_leverage = 5
        dynamic_entry = total_equity / max_trades

        # 2. Monitor Positions
        for sym, data in list(st.session_state.positions.items()):
            try:
                ticker = ex.fetch_ticker(sym)
                pnl = (ticker['last'] - data['entry']) / data['entry'] if data['side'] == 'buy' else (data['entry'] - ticker['last']) / data['entry']
                mins = (datetime.now() - data['start_time']).total_seconds() / 60
                
                if pnl >= TP_TARGET or pnl <= SL_LIMIT or mins >= TRADE_DURATION_MINS:
                    side_close = 'sell' if data['side'] == 'buy' else 'buy'
                    ex.create_market_order(sym, side_close, data['amount'], params={'openType': 2, 'positionType': (2 if data['side'] == 'buy' else 1)})
                    del st.session_state.positions[sym]
                    st.toast(f"Closed {sym}")
            except: continue

        # 3. Scanning & Entry (Ensuring min 10$ entry)
        if len(st.session_state.positions) < max_trades:
            tickers = ex.fetch_tickers()
            symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT')][:40]
            
            for s in symbols:
                if s in st.session_state.positions or len(st.session_state.positions) >= max_trades: break
                
                t = tickers[s]
                percentage = t.get('percentage', 0)
                if percentage is None: continue
                
                # إشارة دخول نشطة
                side = 'buy' if percentage > 0.2 else 'sell' if percentage < -0.2 else None
                
                if side:
                    try:
                        p_idx = 1 if side == 'buy' else 2
                        ex.set_leverage(current_leverage, s)
                        # حساب الكمية بناءً على 12$ (في حال كان الرصيد 60$)
                        amt = float(ex.amount_to_precision(s, (dynamic_entry * current_leverage) / t['last']))
                        ex.create_market_order(s, side, amt, params={'openType': 2, 'positionType': p_idx})
                        
                        st.session_state.positions[s] = {'side': side, 'entry': t['last'], 'amount': amt, 'start_time': datetime.now(), 'cost': dynamic_entry}
                        st.info(f"🚀 AI Executed: {side.upper()} {s} (${dynamic_entry:.2f})")
                        break 
                    except: continue

        # Dashboard
        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("Equity", f"${total_equity:.2f}")
        c2.metric("Trade Size", f"${dynamic_entry:.2f}")
        c3.metric("Max Trades", max_trades)
        
        if st.session_state.positions:
            st.dataframe(pd.DataFrame(st.session_state.positions).T[['side', 'entry', 'cost']], use_container_width=True)

        time.sleep(15)
        st.rerun()

    except Exception as e:
        st.warning(f"Scanning for opportunities... {e}")
        time.sleep(10)
        st.rerun()
        
