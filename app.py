import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import time

# --- AI ADVANCED CONFIGURATION ---
LEVERAGE = 5
MAX_TRADES = 10         # توزيع الرصيد على 10 صفقات للنمو التراكمي
TP_TARGET = 0.04        # هدف ربح 4%
SL_LIMIT = -0.02        # وقف خسارة 2% لحماية الرصيد
TRADE_DURATION_MINS = 30 # نافذة التوقع الزمني

st.set_page_config(page_title="AI Predictive Engine", layout="wide")
st.title("🧠 محرك التوقع والتحليل الفني الذكي")
st.subheader("تحليل المسار المستقبلي لـ 40 عملة قبل التنفيذ")

if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- SIDEBAR ---
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

if st.sidebar.button("🚀 إطلاق المحرك المحلل"):
    if api_key and api_secret: st.session_state.running = True

# --- خوارزمية التوقع الذكي (The Prediction Brain) ---
def analyze_and_predict(ex, symbol):
    try:
        # جلب بيانات الشموع (فريم الدقيقة) لتحليل المسار
        ohlcv = ex.fetch_ohlcv(symbol, timeframe='1m', limit=50)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        
        # إضافة مؤشرات التحليل الفني
        df['RSI'] = ta.rsi(df['close'], length=14)
        df['SMA'] = ta.sma(df['close'], length=20)
        
        last = df.iloc[-1]
        
        # منطق التوقع: لا دخول عشوائي
        # شراء: السعر فوق المتوسط + RSI ليس في منطقة تشبع (أقل من 70)
        if last['close'] > last['SMA'] and 45 < last['RSI'] < 65:
            return 'buy'
        # بيع: السعر تحت المتوسط + RSI ليس في قاع سحيق (أكبر من 30)
        elif last['close'] < last['SMA'] and 35 < last['RSI'] < 55:
            return 'sell'
        return None
    except: return None

# --- المحرك التنفيذي ---
if st.session_state.running and api_key and api_secret:
    try:
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        
        # الربح التراكمي: حساب الرصيد الحالي وتقسيمه آلياً
        balance = ex.fetch_balance()
        total_equity = balance['total'].get('USDT', 0)
        dynamic_entry = total_equity / MAX_TRADES

        # 1. مراقبة وإغلاق الصفقات (الهدف أو 30 دقيقة)
        for sym, data in list(st.session_state.positions.items()):
            try:
                ticker = ex.fetch_ticker(sym)
                pnl = (ticker['last'] - data['entry']) / data['entry'] if data['side'] == 'buy' else (data['entry'] - ticker['last']) / data['entry']
                mins = (datetime.now() - data['start_time']).total_seconds() / 60
                
                if pnl >= TP_TARGET or pnl <= SL_LIMIT or (mins >= TRADE_DURATION_MINS and pnl > 0):
                    ex.create_market_order(sym, 'sell' if data['side'] == 'buy' else 'buy', data['amount'], params={'openType': 2, 'positionType': (2 if data['side'] == 'buy' else 1)})
                    del st.session_state.positions[sym]
                    st.success(f"💰 تم حصد الأرباح من {sym}")
            except: continue

        # 2. تحليل 40 عملة والتوقع قبل الفتح
        if len(st.session_state.positions) < MAX_TRADES:
            tickers = ex.fetch_tickers()
            symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT')][:40]
            
            for s in symbols:
                if s in st.session_state.positions or len(st.session_state.positions) >= MAX_TRADES: break
                
                # التحليل الفني قبل القرار
                prediction = analyze_and_predict(ex, s)
                if prediction:
                    try:
                        ex.set_leverage(LEVERAGE, s)
                        last_p = tickers[s]['last']
                        amt = float(ex.amount_to_precision(s, (dynamic_entry * LEVERAGE) / last_p))
                        ex.create_market_order(s, prediction, amt, params={'openType': 2, 'positionType': (1 if prediction == 'buy' else 2)})
                        
                        st.session_state.positions[s] = {'side': prediction, 'entry': last_p, 'amount': amt, 'start_time': datetime.now()}
                        st.info(f"🔮 توقع ذكي: {prediction.upper()} في {s} (قوة اتجاه عالية)")
                        break 
                    except: continue

        # عرض الإحصائيات
        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي المحفظة", f"${total_equity:.2f}")
        c2.metric("حجم الصفقة التراكمي", f"${dynamic_entry:.2f}")
        c3.metric("الصفقات النشطة", f"{len(st.session_state.positions)}/10")

        time.sleep(20)
        st.rerun()

    except Exception as e:
        st.warning(f"جاري تحليل مسارات السوق... {e}")
        time.sleep(10)
        st.rerun()
        
