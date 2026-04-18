import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime, timedelta

# --- ⚙️ إعدادات القناص المتعدد (Multi-Sniper) ---
SYMBOLS = ['ORDI/USDT:USDT', 'BTC/USDT:USDT', 'SOL/USDT:USDT', 'ETH/USDT:USDT']
MAX_TRADES = 4            # الحد الأقصى للصفقات المفتوحة في وقت واحد
LEVERAGE = 5              # الرافعة المالية
ENTRY_AMOUNT_USDT = 12    # مبلغ الدخول لكل صفقة
TRADE_DURATION_MINS = 30  # مدة الصفقة قبل الإغلاق التلقائي
TP_TARGET = 0.01          # هدف الربح 1%
SL_LIMIT = -0.01          # وقف الخسارة 1%

st.set_page_config(page_title="Multi-Sniper Pro", layout="wide")
st.title("🚀 قناص الأرباح المتعدد (4 صفقات متزامنة)")

# --- تهيئة حالة البوت في الذاكرة ---
if "running" not in st.session_state: st.session_state.running = False
if "active_trades" not in st.session_state: st.session_state.active_trades = {} # لتتبع وقت دخول كل صفقة

# --- واجهة التحكم الجانبية ---
with st.sidebar:
    st.header("🔑 إعدادات الحساب")
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    st.divider()
    if st.button("🚀 تشغيل المحرك العالمي", use_container_width=True):
        st.session_state.running = True
    if st.button("🛑 إيقاف فوري", use_container_width=True):
        st.session_state.running = False

# --- منطقة العرض الحية ---
status_cols = st.columns(len(SYMBOLS))
log_area = st.empty()

# --- محرك القناص المتعدد ---
if st.session_state.running and api_key and api_secret:
    try:
        mexc = ccxt.mexc({
            'apiKey': api_key, 'secret': api_secret,
            'options': {'defaultType': 'future'}, 'enableRateLimit': True
        })

        while st.session_state.running:
            # 1. فحص الصفقات الحالية في المنصة
            positions = mexc.fetch_positions()
            open_positions = [p for p in positions if float(p['contracts']) != 0]
            current_trade_count = len(open_positions)

            # 2. حلقة فحص العملات المحددة
            for i, symbol in enumerate(SYMBOLS):
                # جلب بيانات السعر والمؤشرات
                ohlcv = mexc.fetch_ohlcv(symbol, timeframe='5m', limit=30)
                df = pd.DataFrame(ohlcv, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
                
                # حساب RSI سريع
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]
                price = df['close'].iloc[-1]

                # عرض الحالة لكل عملة
                status_cols[i].metric(symbol.split('/')[0], f"{price}", f"RSI: {rsi:.1f}")

                # أ. منطق الدخول (إذا لم نصل للحد الأقصى 4 صفقات)
                is_already_open = any(p['symbol'] == symbol.replace('/', '').replace(':', '') for p in open_positions)
                
                if not is_already_open and current_trade_count < MAX_TRADES:
                    if rsi <= 32: # فرصة شراء
                        mexc.set_leverage(LEVERAGE, symbol)
                        mexc.create_market_buy_order(symbol, ENTRY_AMOUNT_USDT/price)
                        st.session_state.active_trades[symbol] = datetime.now()
                        st.toast(f"✅ تم قنص شراء {symbol}")
                    elif rsi >= 68: # فرصة بيع
                        mexc.set_leverage(LEVERAGE, symbol)
                        mexc.create_market_sell_order(symbol, amount=ENTRY_AMOUNT_USDT/price)
                        st.session_state.active_trades[symbol] = datetime.now()
                        st.toast(f"✅ تم قنص بيع {symbol}")

                # ب. منطق الخروج (بعد 30 دقيقة)
                if is_already_open and symbol in st.session_state.active_trades:
                    entry_time = st.session_state.active_trades[symbol]
                    if datetime.now() >= entry_time + timedelta(minutes=TRADE_DURATION_MINS):
                        # إغلاق الصفقة (عكس العملية الحالية)
                        pos_info = next(p for p in open_positions if p['symbol'] == symbol.replace('/', '').replace(':', ''))
                        side = 'sell' if float(pos_info['contracts']) > 0 else 'buy'
                        mexc.create_market_order(symbol, side, abs(float(pos_info['contracts'])))
                        del st.session_state.active_trades[symbol]
                        st.toast(f"⏰ انتهت الـ 30 دقيقة: تم إغلاق {symbol}")

            time.sleep(20) # فحص كل 20 ثانية

    except Exception as e:
        st.error(f"⚠️ تنبيه: {e}")
        time.sleep(10)
else:
    log_area.warning("البوت جاهز للعمل على 4 صفقات متزامنة. اضغط 'تشغيل' للبدء.")
    
