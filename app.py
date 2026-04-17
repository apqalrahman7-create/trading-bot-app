import streamlit as st
import ccxt
import time
from datetime import datetime
import pandas as pd

# --- الإعدادات الفنية ---
LEVERAGE = 5
MAX_TRADES = 5
TP_TARGET = 0.05
SL_LIMIT = -0.02
TRADE_DURATION_MINS = 30
ENTRY_USD = 12.0 # مبلغ دخول مناسب لرصيدك

st.set_page_config(page_title="القناص الذكي - بوصلة الاتجاه", layout="wide")
st.title("🧭 بوت بوصلة الاتجاه (عملات رقمية فقط)")

if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- التحكم ---
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

if st.sidebar.button("🚀 تشغيل البوت"):
    if api_key and api_secret: st.session_state.running = True
if st.sidebar.button("🚨 إيقاف وتصفية شاملة"):
    st.session_state.running = False

# --- المحرك الرئيسي ---
if st.session_state.running:
    try:
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        ex.load_markets()

        while st.session_state.running:
            # 1. مراقبة وإغلاق الصفقات (الربح أو مرور 30 دقيقة)
            for sym, data in list(st.session_state.positions.items()):
                t = ex.fetch_ticker(sym)
                pnl = (t['last'] - data['entry']) / data['entry'] if data['side'] == 'buy' else (data['entry'] - t['last']) / data['entry']
                mins_passed = (datetime.now() - data['start_time']).total_seconds() / 60
                
                if pnl >= TP_TARGET or pnl <= SL_LIMIT or mins_passed >= TRADE_DURATION_MINS:
                    p_type = 2 if data['side'] == 'buy' else 1
                    ex.create_market_order(sym, 'sell' if data['side'] == 'buy' else 'buy', data['amount'], params={'openType': 2, 'positionType': p_type})
                    del st.session_state.positions[sym]
                    st.toast(f"تم إغلاق {sym}")

            # 2. البحث عن صفقات (تصفية صارمة للأصول المرفوضة)
            if len(st.session_state.positions) < MAX_TRADES:
                tickers = ex.fetch_tickers()
                # فلتر: استبعاد الفضة، الذهب، النفط، وأي عملة لا تبدأ برمز عملة رقمية واضحة
                forbidden = ['SILVER', 'GOLD', 'OIL', 'BRENT', 'WTI', 'XAUT']
                symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT') and not any(x in s for x in forbidden)][:30]
                
                for s in symbols:
                    if s in st.session_state.positions: continue
                    if len(st.session_state.positions) >= MAX_TRADES: break
                    
                    t = tickers[s]
                    change = t['percentage']
                    side = 'buy' if change > 1.5 else 'sell' if change < -1.5 else None
                    
                    if side:
                        try:
                            # حساب الكمية وتعديلها لتناسب قوانين MEXC
                            market = ex.market(s)
                            min_amt = market['limits']['amount']['min']
                            raw_amt = (ENTRY_USD * LEVERAGE) / t['last']
                            final_amt = float(ex.amount_to_precision(s, max(raw_amt, min_amt)))

                            pos_type = 1 if side == 'buy' else 2
                            ex.set_leverage(LEVERAGE, s, params={'openType': 2, 'positionType': pos_type})
                            ex.create_market_order(s, side, final_amt, params={'openType': 2, 'positionType': pos_type})
                            
                            st.session_state.positions[s] = {
                                'side': side, 'entry': t['last'], 'amount': final_amt,
                                'start_time': datetime.now()
                            }
                            st.success(f"🚀 تم دخول {s} بنجاح.")
                            break # فتح صفقة واحدة كل دورة لضمان استقرار السيولة
                        except: continue

            if st.session_state.positions:
                st.table(st.session_state.positions)

            time.sleep(15)
            st.rerun()

    except Exception as e:
        st.error(f"⚠️ تنبيه: {e}")
        time.sleep(10)
        st.rerun()
        
