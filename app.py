import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import time

# --- إعدادات ثابتة ---
LEVERAGE = 5
MAX_TRADES = 10         
TP_TARGET = 0.04        
SL_LIMIT = -0.02        
TRADE_DURATION_MINS = 30 

st.set_page_config(page_title="AI Integrated Bot", layout="wide")
st.title("🤖 روبوت ذكاء اصطناعي مستقل (إصدار مستقر)")
st.subheader("محرك متكامل (بدون ملفات خارجية)")

if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- واجهة التحكم ---
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

if st.sidebar.button("🚀 بدء المحرك"):
    if api_key and api_secret: st.session_state.running = True
if st.sidebar.button("🚨 إيقاف"):
    st.session_state.running = False

# --- المحرك الرئيسي ---
if st.session_state.running and api_key and api_secret:
    try:
        # إعداد الاتصال مع معاملات MEXC الصحيحة لتجنب Parameter Error
        ex = ccxt.mexc({
            'apiKey': api_key, 
            'secret': api_secret, 
            'options': {'defaultType': 'swap'}
        })
        
        balance = ex.fetch_balance()
        total_equity = balance['total'].get('USDT', 0)
        dynamic_entry = max(11, total_equity * 0.15) 

        # 1. مراقبة وإغلاق الصفقات
        for sym, data in list(st.session_state.positions.items()):
            t = ex.fetch_ticker(sym)
            pnl = (t['last'] - data['entry']) / data['entry'] if data['side'] == 'buy' else (data['entry'] - t['last']) / data['entry']
            mins = (datetime.now() - data['start_time']).total_seconds() / 60
            
            if pnl >= TP_TARGET or pnl <= SL_LIMIT or mins >= TRADE_DURATION_MINS:
                side_close = 'sell' if data['side'] == 'buy' else 'buy'
                # إضافة المعاملات المطلوبة لمنع الخطأ
                ex.create_market_order(sym, side_close, data['amount'], params={'openType': 2})
                del st.session_state.positions[sym]
                st.success(f"تم إغلاق {sym}")

        # 2. تحليل وفتح صفقات (تعديل معاملات الدخول)
        if len(st.session_state.positions) < MAX_TRADES:
            tickers = ex.fetch_tickers()
            symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT')][:40]
            
            for s in symbols:
                if s in st.session_state.positions: continue
                
                ohlcv = ex.fetch_ohlcv(s, timeframe='2m', limit=10)
                df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
                curr_p = df['close'].iloc[-1]
                
                # إشارة سريعة
                side = 'buy' if curr_p > df['close'].mean() else None
                
                if side:
                    try:
                        # ضبط الرافعة مع المعامل الصحيح
                        ex.set_leverage(LEVERAGE, s, params={'openType': 2})
                        amt = float(ex.amount_to_precision(s, (dynamic_entry * LEVERAGE) / curr_p))
                        
                        # فتح الصفقة مع معامل openType لـ MEXC
                        ex.create_market_order(s, side, amt, params={'openType': 2})
                        
                        st.session_state.positions[s] = {'side': side, 'entry': curr_p, 'amount': amt, 'start_time': datetime.now()}
                        st.info(f"🚀 تم فتح صفقة في {s}")
                        break 
                    except: continue

        st.divider()
        st.metric("إجمالي المحفظة", f"${total_equity:.2f}")
        time.sleep(25)
        st.rerun()

    except Exception as e:
        st.warning(f"المحرك يبحث عن إشارات... {e}")
        time.sleep(10)
        st.rerun()
        
