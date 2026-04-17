import streamlit as st
import ccxt
import time
from datetime import datetime

# --- الإعدادات ---
LEVERAGE = 5
MAX_TRADES = 5
TP_TARGET = 0.05
MAX_TIME_MINS = 60
ENTRY_USD = 25.0

st.set_page_config(page_title="القناص الذكي Pro", layout="wide")
st.title("⏱️ بوت القناص (نظام التصفية الشاملة)")

if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- المدخلات والتحكم ---
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

col1, col2 = st.sidebar.columns(2)
if col1.button("🚀 تشغيل النظام"):
    if api_key and api_secret: st.session_state.running = True
    else: st.sidebar.error("أدخل المفاتيح أولاً!")

# --- زر الإيقاف الكلي (يغلق كل شيء فوراً) ---
if st.sidebar.button("🚨 إيقاف وتصفية الكل", type="primary", use_container_width=True):
    st.session_state.running = False
    if api_key and api_secret:
        try:
            ex_stop = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
            if st.session_state.positions:
                st.sidebar.warning("⚠️ جاري إغلاق جميع المراكز...")
                for sym, data in list(st.session_state.positions.items()):
                    side_close = 'sell' if data['side'] == 'buy' else 'buy'
                    p_type = 2 if data['side'] == 'buy' else 1
                    ex_stop.create_market_order(sym, side_close, data['amount'], params={'openType': 2, 'positionType': p_type})
                st.session_state.positions = {}
                st.sidebar.success("✅ تم إغلاق جميع الصفقات بنجاح.")
            else:
                st.sidebar.info("لا توجد صفقات مفتوحة لإغلاقها.")
        except Exception as e:
            st.sidebar.error(f"خطأ أثناء التصفية: {e}")

# --- المحرك الرئيسي ---
if st.session_state.running:
    try:
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        ex.load_markets()

        while st.session_state.running:
            # 1. مراقبة وإغلاق (الربح أو الوقت)
            for sym, data in list(st.session_state.positions.items()):
                t = ex.fetch_ticker(sym)
                pnl = (t['last'] - data['entry']) / data['entry'] if data['side'] == 'buy' else (data['entry'] - t['last']) / data['entry']
                mins = (datetime.now() - data['start_time']).total_seconds() / 60
                
                if pnl >= TP_TARGET or mins >= MAX_TIME_MINS:
                    side_close = 'sell' if data['side'] == 'buy' else 'buy'
                    p_type = 2 if data['side'] == 'buy' else 1
                    ex.create_market_order(sym, side_close, data['amount'], params={'openType': 2, 'positionType': p_type})
                    del st.session_state.positions[sym]
                    st.toast(f"تم إغلاق {sym} بنجاح.")

            # 2. فحص الرصيد والانتظار
            balance = ex.fetch_balance()
            free_usdt = balance['free'].get('USDT', 0)
            
            if free_usdt < ENTRY_USD and len(st.session_state.positions) >= MAX_TRADES:
                placeholder = st.empty()
                for i in range(180, 0, -1):
                    placeholder.warning(f"⚠️ رأس المال مشغول. انتظار {i} ثانية...")
                    time.sleep(1)
                    if not st.session_state.running: break
                st.rerun()

            # 3. فتح صفقات جديدة
            if len(st.session_state.positions) < MAX_TRADES:
                tickers = ex.fetch_tickers()
                symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT') and 'XAUT' not in s][:20]
                
                for s in symbols:
                    if s in st.session_state.positions: continue
                    t = tickers[s]
                    side = 'buy' if t['percentage'] < -1.2 else 'sell' if t['percentage'] > 1.2 else None
                    
                    if side:
                        market = ex.market(s)
                        min_amt = market['limits']['amount']['min']
                        raw_amt = (ENTRY_USD * LEVERAGE) / t['last']
                        final_amt = float(ex.amount_to_precision(s, max(raw_amt, min_amt)))

                        try:
                            pos_type = 1 if side == 'buy' else 2
                            ex.set_leverage(LEVERAGE, s, params={'openType': 2, 'positionType': pos_type})
                            ex.create_market_order(s, side, final_amt, params={'openType': 2, 'positionType': pos_type})
                            st.session_state.positions[s] = {'side': side, 'entry': t['last'], 'amount': final_amt, 'start_time': datetime.now()}
                            st.success(f"🚀 تم دخول {s} بمكان جديد.")
                            break 
                        except: continue

            if st.session_state.positions:
                st.subheader("📊 الصفقات المفتوحة حالياً")
                st.table(st.session_state.positions)

            time.sleep(15)
            st.rerun()
    except Exception as e:
        st.error(f"⚠️ خطأ: {e}")
        time.sleep(10)
        st.rerun()
        
