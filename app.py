import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime

# --- 1. إعدادات القناص المطور لـ MEXC ---
SYMBOL = 'ORDI/USDT:USDT'  # صيغة العقود الآجلة في MEXC
LEVERAGE = 3               # رافعة منخفضة للأمان
ENTRY_AMOUNT = 12          # مبلغ الدخول (USDT)
TP_PERCENT = 0.007         # جني ربح 0.7% (سريع)
SL_PERCENT = -0.010        # وقف خسارة 1% (حماية)
RSI_PERIOD = 14
RSI_BUY_LEVEL = 35         # دخول شراء عند القاع
RSI_SELL_LEVEL = 65        # دخول بيع عند القمة

st.set_page_config(page_title="MEXC Sniper Pro", layout="wide")
st.title("🎯 قناص الأرباح لـ MEXC - ORDI")

# --- دالة حساب المؤشرات ---
def calculate_rsi(df, period=14):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- واجهة الإعدادات ---
if 'running' not in st.session_state: st.session_state.running = False

with st.sidebar:
    st.header("🔑 إعدادات MEXC API")
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 تشغيل البوت"): st.session_state.running = True
    if st.button("🛑 إيقاف"): st.session_state.running = False

# --- المحرك الرئيسي ---
if st.session_state.running:
    try:
        # الاتصال بـ MEXC (عقود آجلة)
        mexc = ccxt.mexc({
            'apiKey': api_key,
            'secret': api_secret,
            'options': {'defaultType': 'future'},
            'enableRateLimit': True
        })

        status_placeholder = st.empty()

        while st.session_state.running:
            # 1. جلب البيانات
            ohlcv = mexc.fetch_ohlcv(SYMBOL, timeframe='5m', limit=50)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['rsi'] = calculate_rsi(df, RSI_PERIOD)
            
            curr_price = df['close'].iloc[-1]
            curr_rsi = df['rsi'].iloc[-1]
            curr_vol = df['volume'].iloc[-1]
            avg_vol = df['volume'].mean()

            # 2. فحص الصفقات الحالية
            balance = mexc.fetch_balance()
            positions = balance['info']['data'] # مخصص لـ MEXC
            has_pos = any(float(p['positionAmt']) != 0 for p in positions if p['symbol'] == "ORDI_USDT")

            # 3. منطق القنص
            if not has_pos:
                # شرط الشراء (Long)
                if curr_rsi <= RSI_BUY_LEVEL and curr_vol > avg_vol:
                    st.success(f"✅ قنص قاع: RSI {curr_rsi:.2f} | شراء عند {curr_price}")
                    mexc.set_leverage(LEVERAGE, SYMBOL)
                    qty = ENTRY_AMOUNT / curr_price
                    mexc.create_market_buy_order(SYMBOL, qty)
                    # وضع أوامر الخروج فوراً
                    mexc.create_order(SYMBOL, 'LIMIT', 'sell', qty, curr_price * (1 + TP_PERCENT), {'reduceOnly': True})
                    mexc.create_order(SYMBOL, 'STOP_MARKET', 'sell', qty, None, {'stopPrice': curr_price * (1 + SL_PERCENT), 'reduceOnly': True})

                # شرط البيع (Short)
                elif curr_rsi >= RSI_SELL_LEVEL and curr_vol > avg_vol:
                    st.warning(f"✅ قنص قمة: RSI {curr_rsi:.2f} | بيع عند {curr_price}")
                    mexc.set_leverage(LEVERAGE, SYMBOL)
                    qty = ENTRY_AMOUNT / curr_price
                    mexc.create_market_sell_order(SYMBOL, qty)
                    # وضع أوامر الخروج فوراً
                    mexc.create_order(SYMBOL, 'LIMIT', 'buy', qty, curr_price * (1 - TP_PERCENT), {'reduceOnly': True})
                    mexc.create_order(SYMBOL, 'STOP_MARKET', 'buy', qty, None, {'stopPrice': curr_price * (1 - SL_PERCENT), 'reduceOnly': True})

            with status_placeholder.container():
                st.write(f"⏱️ تحديث: {datetime.now().strftime('%H:%M:%S')}")
                st.metric("السعر", f"{curr_price} USDT", f"RSI: {curr_rsi:.1f}")

            time.sleep(20)

    except Exception as e:
        st.error(f"⚠️ خطأ اتصال: {e}")
        time.sleep(30)
        
