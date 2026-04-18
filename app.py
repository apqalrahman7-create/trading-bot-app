import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime

# --- 1. إعدادات القناص (Sniper Settings) ---
LEVERAGE = 5            # رافعة مالية معتدلة لتقليل نسبة المخاطرة
ENTRY_AMOUNT_USDT = 15  # المبلغ المخصص لكل صفقة
TP_TARGET = 0.008       # هدف الربح: 0.8% (مع الرافعة يصبح 4% ربح)
SL_LIMIT = -0.006       # وقف الخسارة: 0.6% (لحماية سريعة من الانعكاس)
VOL_MULTIPLIER = 1.5    # يدخل فقط إذا كان حجم التداول الحالي 1.5 ضعف المتوسط

st.set_page_config(page_title="Sniper Profit Bot", layout="wide")
st.title("🎯 Sniper Profit Bot - ORDI/USDT")

# --- تهيئة حالة الجلسة ---
if 'running' not in st.session_state: st.session_state.running = False
if 'logs' not in st.session_state: st.session_state.logs = []

# --- الواجهة الجانبية (Sidebar) ---
with st.sidebar:
    st.header("🔑 إعدادات الوصول")
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    st.divider()
    if st.button("🚀 تشغيل البوت"):
        if api_key and api_secret:
            st.session_state.running = True
            st.success("تم تشغيل محرك القنص!")
        else:
            st.error("يرجى إدخال المفاتيح أولاً")
    if st.button("🛑 إيقاف"):
        st.session_state.running = False

# --- المحرك الرئيسي ---
if st.session_state.running:
    try:
        # الاتصال بمنصة بينانس (العقود الآجلة)
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'options': {'defaultType': 'future'},
            'enableRateLimit': True
        })

        symbol = "ORDI/USDT"
        log_placeholder = st.empty()

        while st.session_state.running:
            # 1. جلب بيانات السوق (شمعة الـ 5 دقائق)
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=20)
            df = pd.DataFrame(ohlcv, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
            
            current_price = df['c'].iloc[-1]
            last_vol = df['v'].iloc[-1]
            avg_vol = df['v'].mean()
            price_change = (df['c'].iloc[-1] - df['c'].iloc[-2]) / df['c'].iloc[-2]

            # 2. التحقق من وجود صفقات مفتوحة لتجنب التكرار
            positions = exchange.fetch_positions([symbol])
            has_position = float(positions[0]['contracts']) > 0

            # 3. منطق القنص (Sniper Logic)
            if not has_position:
                # شرط الشراء (Long): هبوط حاد + انفجار سيولة (توقع ارتداد)
                if price_change < -0.01 and last_vol > (avg_vol * VOL_MULTIPLIER):
                    st.toast(f"🎯 قنص صفقة شراء عند {current_price}")
                    exchange.set_leverage(LEVERAGE, symbol)
                    order = exchange.create_market_buy_order(symbol, ENTRY_AMOUNT_USDT / current_price)
                    # إعداد أوامر جني الربح ووقف الخسارة
                    exchange.create_order(symbol, 'LIMIT', 'sell', (ENTRY_AMOUNT_USDT / current_price), current_price * (1 + TP_TARGET), {'reduceOnly': True})
                    exchange.create_order(symbol, 'STOP_MARKET', 'sell', (ENTRY_AMOUNT_USDT / current_price), None, {'stopPrice': current_price * (1 + SL_LIMIT), 'reduceOnly': True})
                
                # شرط البيع (Short): صعود حاد + انفجار سيولة (توقع تصحيح)
                elif price_change > 0.01 and last_vol > (avg_vol * VOL_MULTIPLIER):
                    st.toast(f"🎯 قنص صفقة بيع عند {current_price}")
                    exchange.set_leverage(LEVERAGE, symbol)
                    order = exchange.create_market_sell_order(symbol, ENTRY_AMOUNT_USDT / current_price)
                    # إعداد أوامر جني الربح ووقف الخسارة
                    exchange.create_order(symbol, 'LIMIT', 'buy', (ENTRY_AMOUNT_USDT / current_price), current_price * (1 - TP_TARGET), {'reduceOnly': True})
                    exchange.create_order(symbol, 'STOP_MARKET', 'buy', (ENTRY_AMOUNT_USDT / current_price), None, {'stopPrice': current_price * (1 - SL_LIMIT), 'reduceOnly': True})

            # تحديث الواجهة
            with log_placeholder.container():
                st.write(f"⏱️ آخر تحديث: {datetime.now().strftime('%H:%M:%S')}")
                st.metric("السعر الحالي", f"{current_price} USDT", f"{price_change:.2%}")
                st.info(f"حجم التداول الحالي: {last_vol:.2f} (المتوسط: {avg_vol:.2f})")

            time.sleep(10) # فحص كل 10 ثوانٍ

    except Exception as e:
        st.error(f"حدث خطأ: {e}")
        st.session_state.running = False
        
