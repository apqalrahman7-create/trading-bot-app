import streamlit as st
import ccxt
import time
from datetime import datetime, timedelta
import pandas as pd

# --- إعدادات بوصلة الاتجاه ---
LEVERAGE = 5
MAX_TRADES = 5
TP_TARGET = 0.05    # هدف 5%
SL_LIMIT = -0.02    # حماية خسارة 2%
TRADE_DURATION_MINS = 30 # مدة المراقبة المكثفة

st.set_page_config(page_title="القناص الذكي - بوصلة الاتجاه", layout="wide")
st.title("🧭 بوت بوصلة الاتجاه (تداول متعدد | حد 30 دقيقة)")

if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- التحكم والربط ---
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

if st.sidebar.button("🚀 إطلاق البوصلة"):
    if api_key and api_secret: st.session_state.running = True
if st.sidebar.button("🚨 إيقاف وتصفية شاملة"):
    st.session_state.running = False

# --- المحرك الرئيسي ---
if st.session_state.running:
    try:
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        ex.load_markets()

        while st.session_state.running:
            # 1. مراقبة الصفقات الـ 5 المفتوحة (تحليل أين يتجه السعر)
            for sym, data in list(st.session_state.positions.items()):
                t = ex.fetch_ticker(sym)
                pnl = (t['last'] - data['entry']) / data['entry'] if data['side'] == 'buy' else (data['entry'] - t['last']) / data['entry']
                
                # حساب الوقت المنقضي
                mins_passed = (datetime.now() - data['start_time']).total_seconds() / 60
                
                exit_now = False
                # إغلاق إذا تحقق الربح أو انتهت الـ 30 دقيقة والسعر بدأ يعكس
                if pnl >= TP_TARGET: exit_now = True
                elif pnl <= SL_LIMIT: exit_now = True
                elif mins_passed >= TRADE_DURATION_MINS: exit_now = True # القاعدة الزمنية

                if exit_now:
                    p_type = 2 if data['side'] == 'buy' else 1
                    ex.create_market_order(sym, 'sell' if data['side'] == 'buy' else 'buy', data['amount'], params={'openType': 2, 'positionType': p_type})
                    del st.session_state.positions[sym]
                    st.toast(f"✅ انتهت مهمة {sym} بنجاح/حماية")

            # 2. البحث عن 5 صفقات تتبع اتجاه السوق (أعلى أو أسفل)
            if len(st.session_state.positions) < MAX_TRADES:
                tickers = ex.fetch_tickers()
                # اختيار العملات الرقمية فقط (USDT)
                symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT') and not any(x in s for x in ['OIL', 'XAUT'])][:25]
                
                for s in symbols:
                    if s in st.session_state.positions: continue
                    if len(st.session_state.positions) >= MAX_TRADES: break
                    
                    t = tickers[s]
                    change = t['percentage'] # تحليل اتجاه السوق
                    
                    # تحليل "أين يرسو السوق":
                    # إذا كان السوق صاعداً بقوة (>1.5%) ندخل شراء مع الاتجاه
                    # إذا كان السوق هابطاً بقوة (<-1.5%) ندخل بيع مع الاتجاه
                    side = 'buy' if change > 1.5 else 'sell' if change < -1.5 else None
                    
                    if side:
                        price = t['last']
                        # حساب الكمية بدقة لـ MEXC
                        amt = float(ex.amount_to_precision(s, (12.0 * LEVERAGE) / price))
                        
                        try:
                            pos_type = 1 if side == 'buy' else 2
                            ex.set_leverage(LEVERAGE, s, params={'openType': 2, 'positionType': pos_type})
                            ex.create_market_order(s, side, amt, params={'openType': 2, 'positionType': pos_type})
                            
                            st.session_state.positions[s] = {
                                'side': side, 'entry': price, 'amount': amt,
                                'start_time': datetime.now()
                            }
                            st.success(f"🎯 صفقة جديدة: {side} على {s} (تتبع اتجاه)")
                        except: continue

            # تحديث الواجهة
            if st.session_state.positions:
                st.subheader("📊 مراقبة حية لـ 5 صفقات")
                st.table(st.session_state.positions)

            time.sleep(15)
            st.rerun()

    except Exception as e:
        st.error(f"⚠️ تنبيه المحرك: {e}")
        time.sleep(10)
        st.rerun()
        
