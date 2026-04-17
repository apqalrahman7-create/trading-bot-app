import streamlit as st
import ccxt
import time
from datetime import datetime, timedelta

# --- إعدادات الحماية الفائقة ---
LEVERAGE = 5
MAX_TRADES = 5
TP_TARGET = 0.05    # 5% ربح
EMERGENCY_EXIT = -0.015 # هروب مبكر إذا عكست الصفقة 1.5% (قبل الوصول للـ 3%)

st.title("🧠 القناص الذكي - نظام الهروب المبكر")

if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}
if 'pnl_history' not in st.session_state: st.session_state.pnl_history = 0.0

# --- الأزرار والتحكم ---
api_key = st.sidebar.text_input("API Key (Futures)", type="password")
api_secret = st.sidebar.text_input("Secret Key (Futures)", type="password")

if st.sidebar.button("🚀 تشغيل (12 ساعة)"):
    st.session_state.running = True
    st.session_state.start_time = datetime.now()

if st.sidebar.button("🚨 طوارئ: تصفية فورية"):
    st.session_state.running = False
    # كود تصفية الصفقات المفتوحة في Futures

# --- المحرك الفني ---
if st.session_state.running:
    try:
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        
        while st.session_state.running:
            # 1. مراقبة الصفقات المفتوحة (التحليل اللحظي)
            for sym, data in list(st.session_state.positions.items()):
                t = ex.fetch_ticker(sym)
                current_price = t['last']
                
                # حساب الربح/الخسارة اللحظي
                pnl = (current_price - data['entry']) / data['entry'] if data['side'] == 'buy' else (data['entry'] - current_price) / data['entry']
                
                # --- منطق الهروب المبكر (المراقبة الذكية) ---
                # إذا وجد البوت أن السعر يعكس ضده بسرعة وبدأ يخسر 1.5%، يهرب فوراً
                exit_now = False
                reason = ""
                
                if pnl >= TP_TARGET:
                    exit_now, reason = True, "✅ تم صيد الربح (5%)"
                elif pnl <= EMERGENCY_EXIT:
                    exit_now, reason = True, "🏃 هروب مبكر (حماية من خسارة أكبر)"
                elif (datetime.now() - data['time']).total_seconds() > 3600:
                    exit_now, reason = True, "⏱️ انتهاء وقت الصفقة (ساعة)"

                if exit_now:
                    side_to_close = 'sell' if data['side'] == 'buy' else 'buy'
                    ex.create_market_order(sym, side_to_close, data['amount'])
                    st.session_state.pnl_history += (pnl * 10) # الربح التقريبي
                    del st.session_state.positions[sym]
                    st.warning(f"{reason} في {sym}")
                    st.rerun()

            # 2. التحليل لفتح صفقات جديدة (شراء/بيع)
            if len(st.session_state.positions) < MAX_TRADES:
                symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']
                for s in symbols:
                    if s in st.session_state.positions: continue
                    ticker = ex.fetch_ticker(s)
                    
                    # استراتيجية القوة النسبية:
                    if ticker['percentage'] <= -2.5: # هبوط قوي -> ارتداد صعودي (Long)
                        ex.set_leverage(LEVERAGE, s)
                        amt = (10.0 * LEVERAGE) / ticker['last']
                        ex.create_market_order(s, 'buy', amt)
                        st.session_state.positions[s] = {'side':'buy', 'entry':ticker['last'], 'amount':amt, 'time':datetime.now()}
                    
                    elif ticker['percentage'] >= 2.5: # صعود مبالغ فيه -> تصحيح هابط (Short)
                        ex.set_leverage(LEVERAGE, s)
                        amt = (10.0 * LEVERAGE) / ticker['last']
                        ex.create_market_order(s, 'sell', amt)
                        st.session_state.positions[s] = {'side':'sell', 'entry':ticker['last'], 'amount':amt, 'time':datetime.now()}
            
            time.sleep(10)

    except Exception as e:
        st.error(f"خطأ: {e}")
        time.sleep(10)

st.sidebar.metric("إجمالي الربح التقديري", f"${st.session_state.pnl_history:.2f}")
