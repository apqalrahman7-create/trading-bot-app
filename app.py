import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import time

# --- CONFIGURATION ---
LEVERAGE = 5
MAX_TRADES = 5         
TP_TARGET = 0.04        
SL_LIMIT = -0.02        
ANALYSIS_TIMEFRAME = '1m'

st.set_page_config(page_title="AI Active Trader", layout="wide")
st.title("⚡ AI Guaranteed Execution Bot")

if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- SIDEBAR ---
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

if st.sidebar.button("🚀 ACTIVATE TRADING"):
    if api_key and api_secret: st.session_state.running = True
if st.sidebar.button("🚨 EMERGENCY STOP"):
    st.session_state.running = False

# --- ENGINE ---
if st.session_state.running and api_key and api_secret:
    try:
        # الربط مع MEXC مع تفعيل الخيارات المتقدمة
        ex = ccxt.mexc({
            'apiKey': api_key, 
            'secret': api_secret, 
            'options': {'defaultType': 'swap', 'recvWindow': 10000},
            'enableRateLimit': True
        })
        
        balance = ex.fetch_balance()
        total_equity = balance['total'].get('USDT', 0)
        # ميزانية الدخول التراكمي (15% من المحفظة)
        dynamic_entry = max(11, total_equity * 0.15) 

        # 1. مراقبة وإغلاق الصفقات (بشكل قسري)
        for sym, data in list(st.session_state.positions.items()):
            ticker = ex.fetch_ticker(sym)
            curr_p = ticker['last']
            pnl = (curr_p - data['entry']) / data['entry'] if data['side'] == 'buy' else (data['entry'] - curr_p) / data['entry']
            
            if pnl >= TP_TARGET or pnl <= SL_LIMIT:
                side_close = 'sell' if data['side'] == 'buy' else 'buy'
                ex.create_market_order(sym, side_close, data['amount'], params={'openType': 2, 'positionType': (2 if data['side'] == 'buy' else 1)})
                del st.session_state.positions[sym]
                st.success(f"Profit realized on {sym}")

        # 2. البحث عن صفقات وفتحها فوراً (Fast Scan)
        if len(st.session_state.positions) < MAX_TRADES:
            tickers = ex.fetch_tickers()
            symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT')][:40]
            
            for s in symbols:
                if s in st.session_state.positions or len(st.session_state.positions) >= MAX_TRADES: break
                
                # تحليل سريع (شمعة واحدة فقط للسرعة القصوى)
                ticker = tickers[s]
                last_p = ticker['last']
                
                # إشارة هجومية: إذا كان السعر يتحرك صعوداً أو هبوطاً بنسبة بسيطة
                side = 'buy' if ticker['percentage'] > 0.5 else 'sell' if ticker['percentage'] < -0.5 else None
                
                if side:
                    try:
                        # ضبط الرافعة والكمية بدقة ميكرو-برمجية
                        p_idx = 1 if side == 'buy' else 2
                        ex.set_leverage(LEVERAGE, s)
                        
                        # حساب الكمية وتدويرها لتناسب شروط المنصة
                        raw_amt = (dynamic_entry * LEVERAGE) / last_p
                        market = ex.market(s)
                        final_amt = float(ex.amount_to_precision(s, raw_amt))
                        
                        # الأمر القسري لفتح الصفقة
                        ex.create_market_order(s, side, final_amt, params={'openType': 2, 'positionType': p_idx})
                        
                        st.session_state.positions[s] = {'side': side, 'entry': last_p, 'amount': final_amt, 'start_time': datetime.now()}
                        st.balloons() # تنبيه بصري عند نجاح الصفقة
                        st.info(f"🚀 AI Executed: {side.upper()} {s}")
                        break 
                    except Exception as e:
                        continue

        # عرض لوحة التحكم
        st.divider()
        st.metric("Total Portfolio Value", f"${total_equity:.2f}")
        if st.session_state.positions:
            st.dataframe(pd.DataFrame(st.session_state.positions).T[['side', 'entry']], use_container_width=True)

        time.sleep(10) # فحص فائق السرعة كل 10 ثوانٍ
        st.rerun()

    except Exception as e:
        st.warning(f"Engine scanning market signals... {e}")
        time.sleep(5)
        st.rerun()
        
