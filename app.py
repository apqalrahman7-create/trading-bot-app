import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import time

# --- إعدادات النمو الذكي ---
LEVERAGE = 5
MAX_TRADES = 5         
TP_TARGET = 0.04        # هدف 4%
SL_LIMIT = -0.02        # حماية 2%
TRADE_DURATION_MINS = 30 

st.set_page_config(page_title="AI Smart Growth", layout="wide")
st.title("🤖 AI Smart Execution Bot")
st.subheader("تحليل الاتجاه لضمان الربح خلال 30 دقيقة")

if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# واجهة التحكم
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

if st.sidebar.button("🚀 تشغيل المحرك الذكي"):
    if api_key and api_secret: st.session_state.running = True

# --- دالة "توقع المستقبل" (The Brain) ---
def predict_trend(ex, symbol):
    try:
        # جلب بيانات آخر 15 دقيقة
        ohlcv = ex.fetch_ohlcv(symbol, timeframe='1m', limit=15)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        
        avg_price = df['close'].mean()
        current_price = df['close'].iloc[-1]
        
        # التوقع: شراء فقط إذا كان السعر يبتعد صعوداً عن المتوسط وبقوة
        if current_price > avg_price * 1.002: # صعود حقيقي وليس تذبذب
            return 'buy'
        # التوقع: بيع فقط إذا كان السعر ينهار تحت المتوسط
        elif current_price < avg_price * 0.998:
            return 'sell'
        return None
    except:
        return None

# المحرك الرئيسي
if st.session_state.running and api_key and api_secret:
    try:
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        
        balance = ex.fetch_balance()
        total_equity = balance['total'].get('USDT', 0)
        dynamic_entry = total_equity / MAX_TRADES

        # مراقبة وإغلاق
        for sym, data in list(st.session_state.positions.items()):
            ticker = ex.fetch_ticker(sym)
            pnl = (ticker['last'] - data['entry']) / data['entry'] if data['side'] == 'buy' else (data['entry'] - ticker['last']) / data['entry']
            mins = (datetime.now() - data['start_time']).total_seconds() / 60
            
            if pnl >= TP_TARGET or pnl <= SL_LIMIT or mins >= TRADE_DURATION_MINS:
                side_close = 'sell' if data['side'] == 'buy' else 'buy'
                ex.create_market_order(sym, side_close, data['amount'], params={'openType': 2, 'positionType': (2 if data['side'] == 'buy' else 1)})
                del st.session_state.positions[sym]
                st.success(f"Closed {sym} | PNL: {pnl*100:.2f}%")

        # البحث والتحليل الذكي (40 عملة)
        if len(st.session_state.positions) < MAX_TRADES:
            tickers = ex.fetch_tickers()
            symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT')][:40]
            
            for s in symbols:
                if s in st.session_state.positions or len(st.session_state.positions) >= MAX_TRADES: break
                
                # استخدام دالة التوقع قبل فتح أي صفقة
                prediction = predict_trend(ex, s)
                
                if prediction:
                    try:
                        ticker = tickers[s]
                        last_p = ticker['last']
                        amt = float(ex.amount_to_precision(s, (dynamic_entry * LEVERAGE) / last_p))
                        
                        p_idx = 1 if prediction == 'buy' else 2
                        ex.create_market_order(s, prediction, amt, params={'openType': 2, 'positionType': p_idx})
                        
                        st.session_state.positions[s] = {'side': prediction, 'entry': last_p, 'amount': amt, 'start_time': datetime.now()}
                        st.info(f"✅ AI Predicted {prediction} on {s} (Target: +4%)")
                        break 
                    except: continue

        st.metric("Portfolio Value", f"${total_equity:.2f}")
        time.sleep(20)
        st.rerun()

    except Exception as e:
        st.warning(f"Engine scanning... {e}")
        time.sleep(10)
        st.rerun()
        
