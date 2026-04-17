import streamlit as st
import ccxt
import time
import pandas as pd
import pandas_ta as ta # مكتبة للتحليل الفني

# --- إعدادات الأمان الصارمة ---
LEVERAGE = 3 # تقليل الرافعة لـ 3 لزيادة الأمان
MAX_TRADES = 2
TP_TARGET = 0.03    # هدف ربح 3%
MAX_SL = -0.015     # أقصى خسارة 1.5%
TRAILING_START = 0.01 # تفعيل حماية الربح بعد تحقيق 1% صعود

st.set_page_config(page_title="القناص الآمن Pro", layout="wide")
st.title("🛡️ بوت القناص الآمن - نظام حماية رأس المال")

if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- واجهة الإعدادات ---
st.sidebar.header("🔑 إعدادات الأمان")
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

if st.sidebar.button("🚀 تشغيل النظام الآمن"):
    if api_key and api_secret: st.session_state.running = True
if st.sidebar.button("🚨 تصفية شاملة وإيقاف"):
    st.session_state.running = False

# --- وظيفة التحليل الفني لحساب RSI ---
def get_rsi(ex, symbol):
    bars = ex.fetch_ohlcv(symbol, timeframe='5m', limit=50)
    df = pd.DataFrame(bars, columns=['t', 'o', 'h', 'l', 'c', 'v'])
    rsi = ta.rsi(df['c'], length=14)
    return rsi.iloc[-1]

# --- المحرك الرئيسي ---
if st.session_state.running:
    try:
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        
        while st.session_state.running:
            # 1. إدارة الصفقات المفتوحة بحماية متغيرة
            for sym, data in list(st.session_state.positions.items()):
                t = ex.fetch_ticker(sym)
                pnl = (t['last'] - data['entry']) / data['entry'] if data['side'] == 'buy' else (data['entry'] - t['last']) / data['entry']
                
                exit_now, reason = False, ""
                
                # تحديث وقف الخسارة المتحرك (حماية الأرباح)
                if pnl >= TRAILING_START:
                    new_sl = pnl - 0.01 # جعل الوقف خلف السعر بنسبة 1%
                    data['sl_dynamic'] = max(data.get('sl_dynamic', MAX_SL), new_sl)

                if pnl >= TP_TARGET: exit_now, reason = True, "✅ هدف الربح"
                elif pnl <= data.get('sl_dynamic', MAX_SL): exit_now, reason = True, "🛡️ وقف خسارة محمي"

                if exit_now:
                    p_type = 2 if data['side'] == 'buy' else 1
                    ex.create_market_order(sym, 'sell' if data['side'] == 'buy' else 'buy', data['amount'], params={'openType': 2, 'positionType': p_type})
                    del st.session_state.positions[sym]
                    st.warning(f"{reason} على {sym}")

            # 2. البحث عن دخول آمن (فلتر RSI)
            if len(st.session_state.positions) < MAX_TRADES:
                for s in ['BTC/USDT:USDT', 'ETH/USDT:USDT']:
                    if s in st.session_state.positions: continue
                    
                    rsi_val = get_rsi(ex, s)
                    ticker = ex.fetch_ticker(s)
                    
                    side = None
                    # دخول فقط في حالة التشبع الشديد (آمن جداً)
                    if rsi_val <= 30: side = 'buy'   # شراء عند القاع
                    elif rsi_val >= 70: side = 'sell' # بيع عند القمة

                    if side:
                        pos_type = 1 if side == 'buy' else 2
                        ex.set_leverage(LEVERAGE, s, params={'openType': 2, 'positionType': pos_type})
                        amt = (20.0 * LEVERAGE) / ticker['last']
                        ex.create_market_order(s, side, amt, params={'openType': 2, 'positionType': pos_type})
                        
                        st.session_state.positions[s] = {
                            'side': side, 'entry': ticker['last'], 
                            'amount': amt, 'sl_dynamic': MAX_SL
                        }
                        st.success(f"🚀 دخول آمن: {side} {s} (RSI: {rsi_val:.2f})")

            time.sleep(20)
            st.rerun()
    except Exception as e:
        st.error(f"خطأ: {e}")
        time.sleep(10)
        st.rerun()
        
