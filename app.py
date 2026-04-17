import streamlit as st
import ccxt
import time
from datetime import datetime
import pandas as pd

# --- إعدادات النظام التراكمي ---
LEVERAGE = 5
MAX_TRADES = 5       # فتح 5 صفقات متوزعة
TP_TARGET = 0.05    # هدف 5%
SL_LIMIT = -0.02    # حماية 2%
TRADE_DURATION_MINS = 30 # حد 30 دقيقة

st.set_page_config(page_title="القناص التراكمي Pro", layout="wide")
st.title("🔄 بوت الاستثمار التراكمي (استخدام الرصيد + الأرباح)")

if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- التحكم ---
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

if st.sidebar.button("🚀 بدء الاستثمار التراكمي"):
    if api_key and api_secret: st.session_state.running = True
if st.sidebar.button("🚨 إيقاف وتصفية شاملة"):
    st.session_state.running = False

# --- المحرك الرئيسي ---
if st.session_state.running:
    try:
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        ex.load_markets()

        while st.session_state.running:
            # 1. جلب الرصيد الحالي (المحفظة + الأرباح المحققة)
            balance = ex.fetch_balance()
            total_usdt = balance['total'].get('USDT', 0)
            free_usdt = balance['free'].get('USDT', 0)
            
            # حساب مبلغ الدخول لكل صفقة بناءً على الرصيد الحالي (توزيع 20% لكل صفقة)
            dynamic_entry_usd = total_usdt / MAX_TRADES

            # 2. مراقبة وإغلاق الصفقات
            for sym, data in list(st.session_state.positions.items()):
                t = ex.fetch_ticker(sym)
                pnl = (t['last'] - data['entry']) / data['entry'] if data['side'] == 'buy' else (data['entry'] - t['last']) / data['entry']
                mins_passed = (datetime.now() - data['start_time']).total_seconds() / 60
                
                if pnl >= TP_TARGET or pnl <= SL_LIMIT or mins_passed >= TRADE_DURATION_MINS:
                    p_type = 2 if data['side'] == 'buy' else 1
                    ex.create_market_order(sym, 'sell' if data['side'] == 'buy' else 'buy', data['amount'], params={'openType': 2, 'positionType': p_type})
                    del st.session_state.positions[sym]
                    st.success(f"🔓 تم إغلاق {sym} وتحرير السيولة مع الأرباح.")

            # 3. فتح صفقات جديدة باستخدام الرصيد المحدث (تراكمي)
            if len(st.session_state.positions) < MAX_TRADES and free_usdt > 10:
                tickers = ex.fetch_tickers()
                forbidden = ['SILVER', 'GOLD', 'OIL', 'BRENT', 'WTI', 'XAUT']
                symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT') and not any(x in s for x in forbidden)][:30]
                
                for s in symbols:
                    if s in st.session_state.positions: continue
                    if len(st.session_state.positions) >= MAX_TRADES: break
                    
                    t = tickers[s]
                    change = t['percentage']
                    side = 'buy' if change > 1.2 else 'sell' if change < -1.2 else None
                    
                    if side:
                        try:
                            # حساب الكمية بناءً على الرصيد المتوفر حالياً (تراكمي)
                            market = ex.market(s)
                            min_amt = market['limits']['amount']['min']
                            # نستخدم dynamic_entry_usd الذي يكبر كلما زاد الرصيد
                            raw_amt = (dynamic_entry_usd * LEVERAGE) / t['last']
                            final_amt = float(ex.amount_to_precision(s, max(raw_amt, min_amt)))

                            pos_type = 1 if side == 'buy' else 2
                            ex.set_leverage(LEVERAGE, s, params={'openType': 2, 'positionType': pos_type})
                            ex.create_market_order(s, side, final_amt, params={'openType': 2, 'positionType': pos_type})
                            
                            st.session_state.positions[s] = {
                                'side': side, 'entry': t['last'], 'amount': final_amt,
                                'start_time': datetime.now(), 'invested': dynamic_entry_usd
                            }
                            st.info(f"🚀 استثمار تراكمي في {s} بمبلغ {dynamic_entry_usd:.2f}$")
                            break 
                        except: continue

            # عرض الإحصائيات
            st.sidebar.metric("إجمالي الرصيد الحالي", f"${total_usdt:.2f}")
            if st.session_state.positions:
                st.table(st.session_state.positions)

            time.sleep(15)
            st.rerun()

    except Exception as e:
        st.error(f"⚠️ تنبيه المحرك: {e}")
        time.sleep(10)
        st.rerun()
        
