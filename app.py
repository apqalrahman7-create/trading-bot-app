import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import time

# --- الإعدادات الإستراتيجية ---
LEVERAGE = 5            # الرافعة المالية
MAX_TRADES = 5          # عدد الصفقات المتزامنة (للربح التراكمي)
TP_TARGET = 0.04        # هدف الربح 4% (يعادل 20% مع الرافعة)
SL_LIMIT = -0.02        # وقف الخسارة 2% (حماية رأس المال)
TRADE_DURATION_MINS = 30 # مدة الصفقة القصوى

st.set_page_config(page_title="Autonomous AI Trader", layout="wide")
st.title("🛡️ Autonomous AI Traiding System")
st.subheader("تحليل الاختراق | ربح تراكمي | إدارة آلية")

# --- إدارة الحالة (Session State) ---
if 'running' not in st.session_state: st.session_state.running = False

# --- القائمة الجانبية لإدخال المفاتيح ---
with st.sidebar:
    st.header("إعدادات الاتصال")
    api_key = st.text_input("MEXC API Key", type="password")
    api_secret = st.text_input("MEXC Secret Key", type="password")
    if st.button("🚀 بدء تشغيل النظام"):
        if api_key and api_secret:
            st.session_state.running = True
            st.success("تم تفعيل النظام")
        else:
            st.error("يرجى إدخال المفاتيح")

# --- المحرك الرئيسي ---
if st.session_state.running:
    try:
        # الاتصال بالمنصة
        ex = ccxt.mexc({
            'apiKey': api_key,
            'secret': api_secret,
            'options': {'defaultType': 'swap'}
        })

        # 1. جلب الرصيد الإجمالي لحساب الربح التراكمي
        balance = ex.fetch_balance()
        total_usdt = balance['total'].get('USDT', 0)
        # تقسيم الرصيد الحالي على عدد الصفقات المتاحة
        dynamic_entry_size = total_usdt / MAX_TRADES

        # 2. جلب وإدارة الصفقات المفتوحة (مباشرة من المنصة)
        positions = ex.fetch_positions()
        active_positions = [p for p in positions if float(p['contracts']) > 0]
        
        st.divider()
        col1, col2, col3 = st.columns(3)
        col1.metric("إجمالي المحفظة (تراكمي)", f"${total_usdt:.2f}")
        col2.metric("الصفقات المفتوحة", f"{len(active_positions)} / {MAX_TRADES}")
        col3.metric("حجم الدخول التالي", f"${dynamic_entry_size:.2f}")

        # 3. مراقبة الإغلاق (الهدف، الخسارة، الوقت)
        for p in active_positions:
            symbol = p['symbol']
            side = p['side']
            entry_p = float(p['entryPrice'])
            mark_p = float(p['markPrice'])
            
            # حساب الربح/الخسارة غير المحقق
            pnl = (mark_p - entry_p) / entry_p if side == 'long' else (entry_p - mark_p) / entry_p
            
            # حساب وقت فتح الصفقة
            open_ts = datetime.fromtimestamp(p['timestamp'] / 1000)
            mins_elapsed = (datetime.now() - open_ts).total_seconds() / 60

            # منطق الخروج
            if pnl >= TP_TARGET or pnl <= SL_LIMIT or mins_elapsed >= TRADE_DURATION_MINS:
                order_side = 'sell' if side == 'long' else 'buy'
                ex.create_market_order(symbol, order_side, p['contracts'], params={'openType': 2})
                st.toast(f"✅ تم إغلاق {symbol} بنجاح")

        # 4. تحليل السوق وفتح صفقات جديدة (توقع الكسر)
        if len(active_positions) < MAX_TRADES:
            tickers = ex.fetch_tickers()
            # البحث في أكثر العملات سيولة
            symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT')][:50]
            
            for s in symbols:
                # التأكد من عدم فتح صفقة مكررة لنفس العملة
                if any(ap['symbol'] == s for ap in active_positions): continue
                if len(active_positions) >= MAX_TRADES: break

                # تحليل الشموع (فريم 5 دقائق للتوقع القريب)
                ohlcv = ex.fetch_ohlcv(s, timeframe='5m', limit=15)
                df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                
                curr_price = df['c'].iloc[-1]
                high_barrier = df['h'].iloc[-11:-1].max() # أعلى سعر في آخر ساعة تقريباً
                low_barrier = df['l'].iloc[-11:-1].min()  # أدنى سعر في آخر ساعة تقريباً

                # إشارة الدخول
                trade_side = None
                if curr_price > high_barrier: trade_side = 'buy'
                elif curr_price < low_barrier: trade_side = 'sell'

                if trade_side:
                    try:
                        ex.set_leverage(LEVERAGE, s)
                        # حساب الكمية بناءً على الرصيد التراكمي والرافعة
                        amount = (dynamic_entry_size * LEVERAGE) / curr_price
                        amount_prec = float(ex.amount_to_precision(s, amount))
                        
                        ex.create_market_order(s, trade_side, amount_prec, params={'openType': 2, 'positionType': (1 if trade_side == 'buy' else 2)})
                        st.info(f"🚀 صفقة جديدة: {trade_side.upper()} {s}")
                        break # فتح صفقة واحدة كل دورة للتأني
                    except Exception as e:
                        continue

        # عرض الصفقات الحالية في جدول
        if active_positions:
            df_pos = pd.DataFrame(active_positions)[['symbol', 'side', 'entryPrice', 'markPrice']]
            st.table(df_pos)

        time.sleep(30)
        st.rerun()

    except Exception as e:
        st.error(f"خطأ في النظام: {e}")
        time.sleep(10)
        st.rerun()
        
