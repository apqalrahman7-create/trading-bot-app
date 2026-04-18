import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import time

# --- إعدادات النظام ---
LEVERAGE = 5
MAX_TRADES = 5         
TP_TARGET = 0.04        # 4% ربح
SL_LIMIT = -0.02        # 2% خسارة
# رفع الحد الأدنى للدخول لضمان قبول المنصة للصفقة
MIN_ENTRY_USD = 15.0   

st.set_page_config(page_title="AI Hyper Bot", layout="wide")
st.title("⚡ AI Hyper-Active Executor")

if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- واجهة التحكم ---
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

if st.sidebar.button("🚀 تشغيل البوت الآن"):
    if api_key and api_secret: st.session_state.running = True
if st.sidebar.button("🚨 إيقاف"):
    st.session_state.running = False

# --- المحرك الرئيسي ---
if st.session_state.running and api_key and api_secret:
    try:
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        
        balance = ex.fetch_balance()
        total_equity = balance['total'].get('USDT', 0)
        # حساب مبلغ الدخول التراكمي (15% أو الحد الأدنى 15 دولار)
        dynamic_entry = max(MIN_ENTRY_USD, total_equity * 0.15) 

        # 1. مراقبة وإغلاق الصفقات
        for sym, data in list(st.session_state.positions.items()):
            ticker = ex.fetch_ticker(sym)
            pnl = (ticker['last'] - data['entry']) / data['entry'] if data['side'] == 'buy' else (data['entry'] - ticker['last']) / data['entry']
            
            if pnl >= TP_TARGET or pnl <= SL_LIMIT:
                side_close = 'sell' if data['side'] == 'buy' else 'buy'
                ex.create_market_order(sym, side_close, data['amount'], params={'openType': 2, 'positionType': (2 if data['side'] == 'buy' else 1)})
                del st.session_state.positions[sym]
                st.success(f"Done! Closed {sym}")

        # 2. البحث المكثف وفتح صفقات فورية
        if len(st.session_state.positions) < MAX_TRADES:
            tickers = ex.fetch_tickers()
            # مسح الـ 40 عملة الأكثر حركة
            symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT')][:40]
            
            for s in symbols:
                if s in st.session_state.positions or len(st.session_state.positions) >= MAX_TRADES: break
                
                t = tickers[s]
                # شرط دخول فائق النشاط: أي حركة (صعود أو هبوط) سيفتح فيها البوت صفقة فوراً
                side = 'buy' if t['percentage'] > 0 else 'sell' if t['percentage'] < 0 else None
                
                if side:
                    try:
                        p_idx = 1 if side == 'buy' else 2
                        # محاولة ضبط الرافعة
                        try: ex.set_leverage(LEVERAGE, s)
                        except: pass
                        
                        # حساب الكمية
                        amt = float(ex.amount_to_precision(s, (dynamic_entry * LEVERAGE) / t['last']))
                        # تنفيذ الأمر
                        ex.create_market_order(s, side, amt, params={'openType': 2, 'positionType': p_idx})
                        
                        st.session_state.positions[s] = {'side': side, 'entry': t['last'], 'amount': amt, 'start_time': datetime.now()}
                        st.info(f"🔥 AI Executed: {side.upper()} {s}")
                        break 
                    except: continue

        # عرض البيانات
        st.divider()
        st.metric("Total Balance", f"${total_equity:.2f}")
        if st.session_state.positions:
            st.dataframe(pd.DataFrame(st.session_state.positions).T[['side', 'entry']], use_container_width=True)

        time.sleep(10) # تحديث سريع جداً
        st.rerun()

    except Exception as e:
        st.warning(f"Scanning... {e}")
        time.sleep(5)
        st.rerun()
        
