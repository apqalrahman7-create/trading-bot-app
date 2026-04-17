import streamlit as st
import ccxt
import time
from datetime import datetime

# --- إعدادات النظام المحدثة ---
LEVERAGE = 5
MAX_TRADES = 5
TP_TARGET = 0.05
MAX_TIME_MINS = 60
ENTRY_USD = 20.0  # المبلغ المطلوب لكل صفقة

st.set_page_config(page_title="القناص الذكي - إدارة السيولة", layout="wide")
st.title("⏱️ بوت القناص (نظام انتظار السيولة 3 دقائق)")

if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- التحكم ---
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

if st.sidebar.button("🚀 تشغيل"): st.session_state.running = True
if st.sidebar.button("🛑 إيقاف"): st.session_state.running = False

# --- المحرك الرئيسي ---
if st.session_state.running:
    try:
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        ex.load_markets()

        while st.session_state.running:
            # 1. مراقبة وإغلاق الصفقات (لتحرير رأس المال)
            for sym, data in list(st.session_state.positions.items()):
                t = ex.fetch_ticker(sym)
                pnl = (t['last'] - data['entry']) / data['entry'] if data['side'] == 'buy' else (data['entry'] - t['last']) / data['entry']
                mins = (datetime.now() - data['start_time']).total_seconds() / 60
                
                if pnl >= TP_TARGET or mins >= MAX_TIME_MINS:
                    side_close = 'sell' if data['side'] == 'buy' else 'buy'
                    ex.create_market_order(sym, side_close, data['amount'], params={'openType': 2, 'positionType': 1 if data['side'] == 'sell' else 2})
                    del st.session_state.positions[sym]
                    st.success(f"🔓 تم تحرير رأس المال بإغلاق {sym}")

            # 2. فحص السيولة المتاحة قبل فتح صفقات جديدة
            balance = ex.fetch_balance()
            free_usdt = balance['free'].get('USDT', 0)
            
            if free_usdt < ENTRY_USD and len(st.session_state.positions) >= MAX_TRADES:
                st.warning(f"⚠️ رأس المال مشغول بالكامل (المتاح: {free_usdt:.2f} USDT). سأنتظر 3 دقائق...")
                time.sleep(180) # الانتظار لمدة 3 دقائق كما طلبت
                st.rerun()

            # 3. فتح صفقات جديدة إذا توفرت السيولة
            if len(st.session_state.positions) < MAX_TRADES and free_usdt >= ENTRY_USD:
                tickers = ex.fetch_tickers()
                symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT') and 'XAUT' not in s][:15]
                
                for s in symbols:
                    if s in st.session_state.positions: continue
                    t = tickers[s]
                    
                    # شرط دخول سريع للتجربة (تغير 0.5%)
                    side = 'buy' if t['percentage'] < -0.5 else 'sell' if t['percentage'] > 0.5 else None
                    
                    if side:
                        price = t['last']
                        amt = float(ex.amount_to_precision(s, (ENTRY_USD * LEVERAGE) / price))
                        
                        try:
                            pos_type = 1 if side == 'buy' else 2
                            ex.set_leverage(LEVERAGE, s, params={'openType': 2, 'positionType': pos_type})
                            ex.create_market_order(s, side, amt, params={'openType': 2, 'positionType': pos_type})
                            
                            st.session_state.positions[s] = {'side': side, 'entry': price, 'amount': amt, 'start_time': datetime.now()}
                            st.info(f"🚀 تم استثمار {ENTRY_USD}$ في {s}")
                            break # فتح صفقة واحدة في كل دورة لضمان التوزيع
                        except: continue

            time.sleep(10)
            st.rerun()

    except Exception as e:
        st.error(f"⚠️ تنبيه: {e}")
        time.sleep(10)
        st.rerun()
        
