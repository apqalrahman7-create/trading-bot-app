import streamlit as st
import ccxt
import time
import pandas as pd

# --- الإعدادات الأساسية ---
LEVERAGE = 3
MAX_TRADES = 2
TP_TARGET = 0.03
SL_TARGET = -0.015

st.set_page_config(page_title="القناص الذكي Pro", layout="wide")
st.title("🛡️ بوت القناص مع نظام التصفية الجذرية")

if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- وظائف المساعدة ---
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

# --- الواجهة الجانبية والتحكم ---
st.sidebar.header("🔑 إعدادات الحساب")
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

# ربط المنصة للعمليات السريعة
ex = None
if api_key and api_secret:
    ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})

col1, col2 = st.sidebar.columns(2)
if col1.button("🚀 تشغيل"):
    st.session_state.running = True

# --- زر الإيقاف الجذري (التصفية الفورية) ---
if col2.button("🛑 إيقاف جذري"):
    st.session_state.running = False
    if ex and st.session_state.positions:
        st.sidebar.warning("⚠️ جاري تصفية جميع المراكز...")
        for sym, data in list(st.session_state.positions.items()):
            try:
                side_close = 'sell' if data['side'] == 'buy' else 'buy'
                p_type = 2 if data['side'] == 'buy' else 1
                ex.create_market_order(sym, side_close, data['amount'], params={'openType': 2, 'positionType': p_type})
                st.sidebar.success(f"تم إغلاق {sym}")
            except Exception as e:
                st.sidebar.error(f"فشل إغلاق {sym}: {e}")
        st.session_state.positions = {}
    else:
        st.sidebar.info("البوت متوقف ولا توجد صفقات مفتوحة.")

# --- واجهة المراقبة ---
monitor = st.empty()

if st.session_state.running and ex:
    try:
        while st.session_state.running:
            with monitor.container():
                st.write(f"🟢 البوت يعمل... آخر تحديث: {time.strftime('%H:%M:%S')}")
                
                # 1. مراقبة وإغلاق (TP/SL)
                for sym, data in list(st.session_state.positions.items()):
                    ticker = ex.fetch_ticker(sym)
                    pnl = (ticker['last'] - data['entry']) / data['entry'] if data['side'] == 'buy' else (data['entry'] - ticker['last']) / data['entry']
                    
                    if pnl >= TP_TARGET or pnl <= SL_TARGET:
                        side_close = 'sell' if data['side'] == 'buy' else 'buy'
                        p_type = 2 if data['side'] == 'buy' else 1
                        ex.create_market_order(sym, side_close, data['amount'], params={'openType': 2, 'positionType': p_type})
                        del st.session_state.positions[sym]
                        st.toast(f"تمت تصفية {sym} آلياً")

                # 2. البحث عن صفقات (RSI Filter)
                if len(st.session_state.positions) < MAX_TRADES:
                    for s in ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']:
                        if s in st.session_state.positions: continue
                        
                        rsi_val = get_rsi(ex, s)
                        if rsi_val <= 30 or rsi_val >= 70:
                            side = 'buy' if rsi_val <= 30 else 'sell'
                            pos_type = 1 if side == 'buy' else 2
                            ex.set_leverage(LEVERAGE, s, params={'openType': 2, 'positionType': pos_type})
                            ticker = ex.fetch_ticker(s)
                            amt = (20.0 * LEVERAGE) / ticker['last']
                            ex.create_market_order(s, side, amt, params={'openType': 2, 'positionType': pos_type})
                            st.session_state.positions[s] = {'side': side, 'entry': ticker['last'], 'amount': amt, 'rsi': rsi_val}
                
                if st.session_state.positions:
                    st.table(st.session_state.positions)
                else:
                    st.info("لا توجد صفقات مفتوحة. في انتظار الإشارة...")

            time.sleep(15)
            st.rerun()
            
    except Exception as e:
        st.error(f"خطأ في المحرك: {e}")
        time.sleep(10)
        st.rerun()
        
