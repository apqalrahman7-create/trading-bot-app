import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime

# --- 🚀 إعدادات القوة العالمية (Global Sniper Settings) ---
SYMBOL = 'ORDI/USDT:USDT'
LEVERAGE = 5               
ENTRY_AMOUNT = 15          
TP_TARGET = 0.012          
SL_LIMIT = -0.008          

st.set_page_config(page_title="Global Power Sniper", layout="wide")
st.title("🌎 قناص عالمي محترف - ORDI Professional")

# --- 🧠 المحرك الحسابي المتقدم ---
def get_signals(df):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['rsi'] = 100 - (100 / (1 + (gain / loss)))
    df['ema12'] = df['close'].ewm(span=12).mean()
    df['ema26'] = df['close'].ewm(span=26).mean()
    df['macd'] = df['ema12'] - df['ema26']
    df['signal'] = df['macd'].ewm(span=9).mean()
    return df

# --- 🔐 واجهة التحكم ---
with st.sidebar:
    st.header("🔑 إعدادات الوصول")
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    mode = st.toggle("تفعيل التداول الحقيقي 🚀")

if api_key and api_secret:
    try:
        # إعداد الاتصال مع تجاوز مشكلة fetchBalance
        mexc = ccxt.mexc({
            'apiKey': api_key, 
            'secret': api_secret, 
            'options': {'defaultType': 'future'},
            'enableRateLimit': True
        })
        
        status_box = st.empty()

        while True:
            # 1. جلب البيانات وتحليلها
            ohlcv = mexc.fetch_ohlcv(SYMBOL, timeframe='5m', limit=100)
            df = pd.DataFrame(ohlcv, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
            df = get_signals(df)
            
            p, r, m, s, v = df['close'].iloc[-1], df['rsi'].iloc[-1], df['macd'].iloc[-1], df['signal'].iloc[-1], df['vol'].iloc[-1]
            avg_v = df['vol'].mean()

            # 2. فحص الصفقات بطريقة MEXC الصحيحة
            # بدلاً من fetchBalance الشاملة، نبحث عن الصفقات المفتوحة فقط
            positions = mexc.fetch_positions([SYMBOL])
            has_pos = False
            for pos in positions:
                if float(pos['contracts']) != 0:
                    has_pos = True
                    break

            # 3. منطق الدخول
            if not has_pos and mode:
                # شراء قوي (Long)
                if r < 35 and m > s and v > avg_v:
                    amount = ENTRY_AMOUNT / p
                    mexc.set_leverage(LEVERAGE, SYMBOL)
                    mexc.create_market_buy_order(SYMBOL, amount)
                    mexc.create_order(SYMBOL, 'LIMIT', 'sell', amount, p*(1+TP_TARGET), {'reduceOnly': True})
                    mexc.create_order(SYMBOL, 'STOP_MARKET', 'sell', amount, None, {'stopPrice': p*(1+SL_LIMIT), 'reduceOnly': True})
                    st.toast("🔥 تم فتح صفقة LONG")

                # بيع قوي (Short)
                elif r > 65 and m < s and v > avg_v:
                    amount = ENTRY_AMOUNT / p
                    mexc.set_leverage(LEVERAGE, SYMBOL)
                    mexc.create_market_sell_order(SYMBOL, amount)
                    mexc.create_order(SYMBOL, 'LIMIT', 'buy', amount, p*(1-TP_TARGET), {'reduceOnly': True})
                    mexc.create_order(SYMBOL, 'STOP_MARKET', 'buy', amount, None, {'stopPrice': p*(1-SL_LIMIT), 'reduceOnly': True})
                    st.toast("🔥 تم فتح صفقة SHORT")

            status_box.info(f"📊 السعر: {p} | RSI: {r:.2f} | السيولة: {'ممتازة' if v > avg_v else 'عادية'}")
            time.sleep(20)

    except Exception as e:
        st.error(f"تنبيه: {e}")
        time.sleep(30)
        
