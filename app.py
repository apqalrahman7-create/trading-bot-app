import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime

# --- 1. إعدادات الخبير (Expert Settings) ---
# هذه الإعدادات هي سر النجاح: أهداف قريبة لضمان الخروج بربح قبل انعكاس السوق
LEVERAGE = 3             # رافعة منخفضة لتقليل المخاطر (مهم جداً!)
ENTRY_AMOUNT_USDT = 12   # مبلغ الدخول لكل صفقة
TP_TARGET = 0.007        # جني ربح عند 0.7% (مع الرافعة يصبح 2.1% صافي)
SL_LIMIT = -0.010        # وقف خسارة عند 1% لحماية الحساب من الانهيارات
RSI_PERIOD = 14
RSI_BUY_LEVEL = 35       # يشتري فقط عندما يكون السعر "رخيص جداً" (قاع)
RSI_SELL_LEVEL = 65      # يبيع فقط عندما يكون السعر "متضخم جداً" (قمة)

st.set_page_config(page_title="PRO Profit Sniper", layout="wide")
st.title("💰 PRO Profit Sniper - ORDI/USDT")

# --- دالة حساب RSI الاحترافية ---
def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- تهيئة الجلسة ---
if 'running' not in st.session_state: st.session_state.running = False

with st.sidebar:
    st.header("🔑 Keys")
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 تشغيل محرك الأرباح"):
        st.session_state.running = True
    if st.button("🛑 إيقاف آمن"):
        st.session_state.running = False

if st.session_state.running:
    try:
        exchange = ccxt.binance({
            'apiKey': api_key, 'secret': api_secret,
            'options': {'defaultType': 'future'}, 'enableRateLimit': True
        })
        symbol = "ORDI/USDT"
        status_box = st.empty()

        while st.session_state.running:
            # 1. جلب البيانات وتحليلها
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=50)
            df = pd.DataFrame(ohlcv, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
            df['rsi'] = calculate_rsi(df['c'], RSI_PERIOD)
            
            current_price = df['c'].iloc[-1]
            current_rsi = df['rsi'].iloc[-1]
            last_vol = df['v'].iloc[-1]
            avg_vol = df['v'].mean()

            # 2. فحص الصفقات المفتوحة
            pos = exchange.fetch_balance()['info']['positions']
            position = next((p for p in pos if p['symbol'] == "ORDIUSDT"), None)
            has_position = float(position['positionAmt']) != 0 if position else False

            # 3. منطق "القناص" (Sniper Logic)
            if not has_position:
                # إشارة شراء (Long): السعر في القاع (RSI < 35) + سيولة أعلى من المتوسط
                if current_rsi <= RSI_BUY_LEVEL and last_vol > avg_vol:
                    st.success(f"🎯 قنص قاع! دخول شراء عند {current_price} (RSI: {current_rsi:.2f})")
                    exchange.set_leverage(LEVERAGE, symbol)
                    amount = ENTRY_AMOUNT_USDT / current_price
                    exchange.create_market_buy_order(symbol, amount)
                    # أوامر الخروج التلقائية (مهمة جداً لضمان الربح)
                    exchange.create_order(symbol, 'LIMIT', 'sell', amount, current_price * (1 + TP_TARGET), {'reduceOnly': True})
                    exchange.create_order(symbol, 'STOP_MARKET', 'sell', amount, None, {'stopPrice': current_price * (1 + SL_LIMIT), 'reduceOnly': True})

                # إشارة بيع (Short): السعر في القمة (RSI > 65) + سيولة عالية
                elif current_rsi >= RSI_SELL_LEVEL and last_vol > avg_vol:
                    st.warning(f"🎯 قنص قمة! دخول بيع عند {current_price} (RSI: {current_rsi:.2f})")
                    exchange.set_leverage(LEVERAGE, symbol)
                    amount = ENTRY_AMOUNT_USDT / current_price
                    exchange.create_market_sell_order(symbol, amount)
                    # أوامر الخروج التلقائية
                    exchange.create_order(symbol, 'LIMIT', 'buy', amount, current_price * (1 - TP_TARGET), {'reduceOnly': True})
                    exchange.create_order(symbol, 'STOP_MARKET', 'buy', amount, None, {'stopPrice': current_price * (1 - SL_LIMIT), 'reduceOnly': True})

            with status_box.container():
                st.info(f"📊 السعر: {current_price} | RSI: {current_rsi:.2f} | السيولة: {'عالية' if last_vol > avg_vol else 'هادئة'}")
            
            time.sleep(15) # انتظر 15 ثانية قبل الفحص التالي

    except Exception as e:
        st.error(f"⚠️ تنبيه: {e}")
        time.sleep(30)
        
