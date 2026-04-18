import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import time

# --- الإعدادات الإستراتيجية ---
LEVERAGE = 5            
MAX_TRADES = 5          
TP_TARGET = 0.04        
SL_LIMIT = -0.02        
TRADE_DURATION_MINS = 30 

st.set_page_config(page_title="AI Autonomous Trader V2", layout="wide")
st.title("🤖 AI Autonomous Trader - MEXC Edition")
st.subheader("إدارة آلية بالكامل | ربح تراكمي | توافق MEXC")

if 'running' not in st.session_state: st.session_state.running = False

# --- القائمة الجانبية ---
with st.sidebar:
    st.header("إعدادات الوصول")
    api_key = st.text_input("MEXC API Key", type="password")
    api_secret = st.text_input("MEXC Secret Key", type="password")
    if st.button("🚀 تشغيل النظام"):
        if api_key and api_secret:
            st.session_state.running = True
            st.success("تم تشغيل المحرك")
        else:
            st.error("أدخل المفاتيح أولاً")

# --- المحرك الرئيسي ---
if st.session_state.running:
    try:
        # الاتصال بمنصة MEXC مع إعدادات العقود الآجلة
        ex = ccxt.mexc({
            'apiKey': api_key,
            'secret': api_secret,
            'options': {'defaultType': 'swap'}
        })

        # 1. جلب الرصيد الإجمالي من محفظة العقود (الربح التراكمي)
        balance = ex.fetch_balance()
        total_usdt = balance['total'].get('USDT', 0)
        
        # التأكد من وجود رصيد كافٍ
        if total_usdt < 5:
            st.warning("الرصيد في محفظة Futures قليل جداً لبدء الصفقات.")
            st.stop()

        dynamic_entry_size = total_usdt / MAX_TRADES

        # 2. مراقبة الصفقات المفتوحة مباشرة من المنصة
        positions = ex.fetch_positions()
        active_positions = [p for p in positions if float(p['contracts']) > 0]
        
        # عرض الإحصائيات
        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي المحفظة", f"${total_usdt:.2f}")
        c2.metric("الصفقات النشطة", f"{len(active_positions)}")
        c3.metric("مبلغ دخول الصفقة", f"${dynamic_entry_size:.2f}")

        # 3. إدارة الخروج من الصفقات
        for p in active_positions:
            symbol = p['symbol']
            side = p['side'] # 'long' or 'short'
            entry_p = float(p['entryPrice'])
            mark_p = float(p['markPrice'])
            
            pnl = (mark_p - entry_p) / entry_p if side == 'long' else (entry_p - mark_p) / entry_p
            
            # حساب الوقت (استخدام التوقيت الحالي مقارنة بتوقيت الصفقة)
            open_ts = datetime.fromtimestamp(p['timestamp'] / 1000)
            mins_elapsed = (datetime.now() - open_ts).total_seconds() / 60

            if pnl >= TP_TARGET or pnl <= SL_LIMIT or mins_elapsed >= TRADE_DURATION_MINS:
                order_side = 'sell' if side == 'long' else 'buy'
                # إغلاق الصفقة بالكامل
                ex.create_market_order(symbol, order_side, p['contracts'], params={'openType': 2})
                st.success(f"تم إغلاق صفقة {symbol}")

        # 4. البحث عن فرص جديدة وفتح صفقات (تحليل الكسر)
        if len(active_positions) < MAX_TRADES:
            tickers = ex.fetch_tickers()
            all_symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT')]
            
            for s in all_symbols[:40]: # فحص أفضل 40 عملة
                if any(ap['symbol'] == s for ap in active_positions): continue
                if len(active_positions) >= MAX_TRADES: break

                # تحليل الشموع
                ohlcv = ex.fetch_ohlcv(s, timeframe='5m', limit=15)
                df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                curr_p = df['c'].iloc[-1]
                high_h = df['h'].iloc[-11:-1].max()
                low_l = df['l'].iloc[-11:-1].min()

                trade_side = 'buy' if curr_p > high_h else 'sell' if curr_p < low_l else None

                if trade_side:
                    try:
                        # ضبط الرافعة المالية للعملة المحددة
                        ex.set_leverage(LEVERAGE, s)
                        
                        # حساب الكمية بدقة MEXC
                        amount = (dynamic_entry_size * LEVERAGE) / curr_p
                        amount_prec = float(ex.amount_to_precision(s, amount))
                        
                        # تنفيذ الأمر مع معلمات MEXC الإضافية
                        params = {
                            'openType': 2, 
                            'positionType': (1 if trade_side == 'buy' else 2),
                            'settle': 'USDT'
                        }
                        ex.create_market_order(s, trade_side, amount_prec, params=params)
                        st.balloons()
                        st.info(f"🚀 تم فتح صفقة {trade_side.upper()} على {s}")
                        break # فتح صفقة واحدة والانتظار للدورة القادمة
                    except Exception as e:
                        st.error(f"خطأ في فتح {s}: {e}")
                        continue

        # عرض الصفقات في جدول جميل
        if active_positions:
            st.write("### الصفقات الحالية في حسابك:")
            st.dataframe(pd.DataFrame(active_positions)[['symbol', 'side', 'entryPrice', 'markPrice', 'unrealizedPnl']], use_container_width=True)

        time.sleep(30)
        st.rerun()

    except Exception as e:
        st.error(f"⚠️ فشل النظام في الاتصال: {e}")
        time.sleep(15)
        st.rerun()
        
