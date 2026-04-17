import streamlit as st
import ccxt
import time
from datetime import datetime, timedelta
import pandas as pd

# --- إعدادات القناص الزمني ---
LEVERAGE = 5
MAX_TRADES = 5       # فتح 5 صفقات في أماكن مختلفة
TP_TARGET = 0.05    # هدف الربح 5%
SL_TARGET = -0.02   # وقف خسارة 2% لحماية الحساب
MAX_TIME_MINS = 60  # الحد الأقصى لعمر الصفقة (ساعة)

st.set_page_config(page_title="القناص الزمني Pro", layout="wide")
st.title("⏱️ بوت القناص الزمني (هدف 5% | حد 60 دقيقة)")

if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- إدارة الواجهة ---
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

if st.sidebar.button("🚀 تشغيل النظام"):
    if api_key and api_secret: st.session_state.running = True
if st.sidebar.button("🛑 إيقاف وتصفية شاملة"):
    st.session_state.running = False

# --- المحرك الرئيسي ---
if st.session_state.running:
    try:
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        
        while st.session_state.running:
            # 1. المراقبة اللحظية (إغلاق بناءً على الربح أو الزمن)
            for sym, data in list(st.session_state.positions.items()):
                t = ex.fetch_ticker(sym)
                pnl = (t['last'] - data['entry']) / data['entry'] if data['side'] == 'buy' else (data['entry'] - t['last']) / data['entry']
                
                # حساب الوقت المنقضي
                time_elapsed = datetime.now() - data['start_time']
                minutes_passed = time_elapsed.total_seconds() / 60
                
                exit_now, reason = False, ""
                
                if pnl >= TP_TARGET:
                    exit_now, reason = True, f"✅ تم صيد الهدف (5%) في {sym}"
                elif pnl <= SL_TARGET:
                    exit_now, reason = True, f"🛑 وقف خسارة حماية في {sym}"
                elif minutes_passed >= MAX_TIME_MINS:
                    exit_now, reason = True, f"⏱️ انتهاء الوقت (ساعة) في {sym}"

                if exit_now:
                    p_type = 2 if data['side'] == 'buy' else 1
                    ex.create_market_order(sym, 'sell' if data['side'] == 'buy' else 'buy', data['amount'], params={'openType': 2, 'positionType': p_type})
                    del st.session_state.positions[sym]
                    st.toast(reason)

            # 2. البحث عن فرص جديدة (تعدد الأماكن)
            if len(st.session_state.positions) < MAX_TRADES:
                # مسح أفضل العملات مقابل USDT
                tickers = ex.fetch_tickers()
                active_symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT')][:30]
                
                for s in active_symbols:
                    if s in st.session_state.positions: continue
                    if len(st.session_state.positions) >= MAX_TRADES: break
                    
                    # تحليل سريع للدخول (RSI)
                    bars = ex.fetch_ohlcv(s, timeframe='5m', limit=20)
                    df = pd.DataFrame(bars, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                    delta = df['c'].diff()
                    rsi = 100 - (100 / (1 + (delta.where(delta > 0, 0).mean() / -delta.where(delta < 0, 0).mean())))
                    
                    side = 'buy' if rsi <= 35 else 'sell' if rsi >= 65 else None
                    
                    if side:
                        pos_type = 1 if side == 'buy' else 2
                        ex.set_leverage(LEVERAGE, s, params={'openType': 2, 'positionType': pos_type})
                        entry_price = tickers[s]['last']
                        amt = (10.0 * LEVERAGE) / entry_price # دخول بـ 10$ لكل صفقة
                        
                        ex.create_market_order(s, side, amt, params={'openType': 2, 'positionType': pos_type})
                        st.session_state.positions[s] = {
                            'side': side, 'entry': entry_price, 'amount': amt,
                            'start_time': datetime.now(), 'pnl': 0
                        }
                        st.success(f"🎯 دخلنا {s} | الوقت المتبقي: 60 دقيقة")

            # عرض الجدول المحدث
            if st.session_state.positions:
                display_df = pd.DataFrame.from_dict(st.session_state.positions, orient='index')
                st.table(display_df[['side', 'entry', 'start_time']])
            
            time.sleep(10)
            st.rerun()

    except Exception as e:
        st.error(f"⚠️ خطأ: {e}")
        time.sleep(10)
        st.rerun()
        
