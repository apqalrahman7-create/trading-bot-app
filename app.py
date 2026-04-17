import streamlit as st
import ccxt
import time
import pandas as pd

# --- الإعدادات ---
LEVERAGE = 3
MAX_TRADES = 2
TP_TARGET = 0.03
SL_TARGET = -0.015

st.set_page_config(page_title="القناص المستقر", layout="wide")
st.title("🛡️ بوت التداول المستقر (حماية من الانهيار)")

if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- وظيفة حساب RSI يدوياً (بدون مكتبات إضافية) ---
def get_rsi(ex, symbol):
    try:
        bars = ex.fetch_ohlcv(symbol, timeframe='5m', limit=30)
        df = pd.DataFrame(bars, columns=['t', 'o', 'h', 'l', 'c', 'v'])
        delta = df['c'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs)).iloc[-1]
    except: return 50

# --- الواجهة ---
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

if st.sidebar.button("🚀 تشغيل"): st.session_state.running = True
if st.sidebar.button("🛑 إيقاف"): st.session_state.running = Falseif st.sidebar.button("🛑 إيقاف وتصفية الكل"):
    st.session_state.running = False
    # كود لإغلاق أي صفقة مفتوحة في الحساب فوراً
    for sym, data in list(st.session_state.positions.items()):
        try:
            side_close = 'sell' if data['side'] == 'buy' else 'buy'
            p_type = 2 if data['side'] == 'buy' else 1
            ex.create_market_order(sym, side_close, data['amount'], params={'openType': 2, 'positionType': p_type})
            st.toast(f"تم تصفية {sym}")
        except: pass
    st.session_state.positions = {}
    st.success("تم إيقاف البوت وإغلاق جميع المراكز.")
# حاويات التحديث (تمنع خطأ removeChild)
monitor = st.empty()
logs = st.empty()

if st.session_state.running:
    try:
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        
        while st.session_state.running:
            with monitor.container():
                st.write(f"⏱️ آخر تحديث: {time.strftime('%H:%M:%S')}")
                # 1. مراقبة الصفقات
                for sym, data in list(st.session_state.positions.items()):
                    t = ex.fetch_ticker(sym)
                    pnl = (t['last'] - data['entry']) / data['entry'] if data['side'] == 'buy' else (data['entry'] - t['last']) / data['entry']
                    
                    if pnl >= TP_TARGET or pnl <= SL_TARGET:
                        p_type = 2 if data['side'] == 'buy' else 1
                        ex.create_market_order(sym, 'sell' if data['side'] == 'buy' else 'buy', data['amount'], params={'openType': 2, 'positionType': p_type})
                        del st.session_state.positions[sym]
                        st.toast(f"تم إغلاق صفقة {sym}")

                # 2. فحص الدخول
                if len(st.session_state.positions) < MAX_TRADES:
                    for s in ['BTC/USDT:USDT', 'ETH/USDT:USDT']:
                        rsi_val = get_rsi(ex, s)
                        if rsi_val <= 30 or rsi_val >= 70:
                            side = 'buy' if rsi_val <= 30 else 'sell'
                            pos_type = 1 if side == 'buy' else 2
                            ex.set_leverage(LEVERAGE, s, params={'openType': 2, 'positionType': pos_type})
                            ticker = ex.fetch_ticker(s)
                            amt = (15.0 * LEVERAGE) / ticker['last']
                            ex.create_market_order(s, side, amt, params={'openType': 2, 'positionType': pos_type})
                            st.session_state.positions[s] = {'side': side, 'entry': ticker['last'], 'amount': amt}
                
                if st.session_state.positions:
                    st.table(st.session_state.positions)

            time.sleep(10) # انتظار كافٍ لمنع أخطاء الواجهة
            
    except Exception as e:
        st.error(f"⚠️ حدث خطأ: {e}")
        time.sleep(5)
        
