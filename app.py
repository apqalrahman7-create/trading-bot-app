import streamlit as st
import ccxt
import time
from datetime import datetime

# --- الإعدادات الفنية ---
LEVERAGE = 5
MAX_TRADES = 3
TP_TARGET = 0.05       # هدف الربح 5%
EMERGENCY_EXIT = -0.015 # وقف خسارة مبكر 1.5%

st.set_page_config(page_title="القناص الذكي Pro", layout="wide")

# --- إدارة حالة التطبيق ---
if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}
if 'pnl_history' not in st.session_state: st.session_state.pnl_history = 0.0
if 'logs' not in st.session_state: st.session_state.logs = []

def add_log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{timestamp}] {msg}")
    if len(st.session_state.logs) > 10: st.session_state.logs.pop(0)

# --- الواجهة الجانبية ---
st.sidebar.title("🛠️ التحكم بالبوت")
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

if st.sidebar.button("🚀 بدء التشغيل" if not st.session_state.running else "🔄 تحديث العمل"):
    if api_key and api_secret:
        st.session_state.running = True
        add_log("تم تفعيل البوت...")
    else:
        st.sidebar.error("يرجى إدخال مفاتيح الـ API")

if st.sidebar.button("🛑 إيقاف كلي"):
    st.session_state.running = False
    add_log("تم إيقاف البوت.")

st.sidebar.divider()
st.sidebar.metric("الربح التراكمي", f"${st.session_state.pnl_history:.2f}")

# --- عرض الصفقات والسجلات ---
col_stats, col_logs = st.columns([2, 1])

with col_stats:
    st.subheader("📊 المراكز المفتوحة")
    if st.session_state.positions:
        st.table(st.session_state.positions)
    else:
        st.info("لا توجد صفقات نشطة حالياً.")

with col_logs:
    st.subheader("📜 السجل اللحظي")
    for log in reversed(st.session_state.logs):
        st.caption(log)

# --- المحرك الرئيسي (المنطق البرمجي) ---
if st.session_state.running:
    try:
        # الربط مع MEXC Futures
        exchange = ccxt.mexc({
            'apiKey': api_key,
            'secret': api_secret,
            'options': {'defaultType': 'swap'},
            'enableRateLimit': True
        })

        # 1. تحديث ومراقبة الصفقات المفتوحة
        for sym, data in list(st.session_state.positions.items()):
            ticker = exchange.fetch_ticker(sym)
            curr_price = ticker['last']
            
            # حساب الربح/الخسارة
            diff = (curr_price - data['entry']) / data['entry']
            pnl = diff if data['side'] == 'buy' else -diff
            
            close_now = False
            msg = ""
            
            if pnl >= TP_TARGET:
                close_now, msg = True, f"✅ هدف الربح {sym}"
            elif pnl <= EMERGENCY_EXIT:
                close_now, msg = True, f"🏃 هروب اضطراري {sym}"

            if close_now:
                side_close = 'sell' if data['side'] == 'buy' else 'buy'
                exchange.create_market_order(sym, side_close, data['amount'])
                st.session_state.pnl_history += (pnl * 20) # تقديري
                del st.session_state.positions[sym]
                add_log(msg)

        # 2. البحث عن فرص جديدة
        if len(st.session_state.positions) < MAX_TRADES:
            target_symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']
            for s in target_symbols:
                if s in st.session_state.positions: continue
                
                t = exchange.fetch_ticker(s)
                change = t['percentage']
                
                # استراتيجية بسيطة: دخول عند تغير 1% (للتجربة)
                trade_side = None
                if change <= -1.0: trade_side = 'buy'
                elif change >= 1.0: trade_side = 'sell'

                if trade_side:
                    exchange.set_leverage(LEVERAGE, s)
                    # حساب كمية بسيطة (تقريباً 10$ مع الرافعة)
                    amt = (10.0 * LEVERAGE) / t['last']
                    
                    # تنفيذ الصفقة ببارامترات MEXC
                    exchange.create_market_order(s, trade_side, amt, params={'openType': 2})
                    
                    st.session_state.positions[s] = {
                        'side': trade_side,
                        'entry': t['last'],
                        'amount': amt,
                        'status': 'Active'
                    }
                    add_log(f"🚀 صفقة {trade_side} على {s}")

        # تحديث الصفحة كل 10 ثواني تلقائياً
        time.sleep(10)
        st.rerun()

    except Exception as e:
        add_log(f"⚠️ خطأ: {str(e)}")
        time.sleep(10)
        st.rerun()
                
