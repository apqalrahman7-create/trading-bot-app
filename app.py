import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime

# --- 🚀 إعدادات القوة العالمية (Global Sniper Settings) ---
SYMBOL = 'ORDI/USDT:USDT'
LEVERAGE = 5               # قوة متوسطة
ENTRY_AMOUNT = 15          # دخول بـ 15 دولار لتعظيم الربح
TP_TARGET = 0.012          # هدف ربح 1.2% (قوي جداً مع الرافعة)
SL_LIMIT = -0.008          # وقف خسارة صارم 0.8% لحماية المحفظة

st.set_page_config(page_title="Global Power Sniper", layout="wide")
st.title("🌎 Global Power Sniper - ORDI Professional")

# --- 🧠 المحرك الحسابي المتقدم ---
def get_signals(df):
    # 1. حساب RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['rsi'] = 100 - (100 / (1 + (gain / loss)))
    
    # 2. حساب MACD (لقياس قوة الاتجاه)
    df['ema12'] = df['close'].ewm(span=12).mean()
    df['ema26'] = df['close'].ewm(span=26).mean()
    df['macd'] = df['ema12'] - df['ema26']
    df['signal'] = df['macd'].ewm(span=9).mean()
    
    return df

# --- 🔐 واجهة التحكم ---
with st.sidebar:
    st.header("🔑 إعدادات الوصول الآمن")
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    mode = st.radio("وضع التداول", ["مراقبة فقط", "تداول حقيقي 🚀"])

if api_key and api_secret:
    try:
        mexc = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'future'}})
        
        while True:
            # جلب البيانات وتحليلها
            ohlcv = mexc.fetch_ohlcv(SYMBOL, timeframe='5m', limit=100)
            df = pd.DataFrame(ohlcv, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
            df = get_signals(df)
            
            p, r, m, s, v = df['close'].iloc[-1], df['rsi'].iloc[-1], df['macd'].iloc[-1], df['signal'].iloc[-1], df['vol'].iloc[-1]
            avg_v = df['vol'].mean()

            # فحص الصفقات
            pos = mexc.fetch_balance()['info']['data']
            has_pos = any(float(x['positionAmt']) != 0 for x in pos if x['symbol'] == "ORDI_USDT")

            # --- ⚡ منطق الدخول العالمي (القوة) ---
            if not has_pos and mode == "تداول حقيقي 🚀":
                # شراء قوي: السعر في قاع (RSI < 35) + تقاطع MACD إيجابي + سيولة عالية
                if r < 35 and m > s and v > avg_v:
                    amount = ENTRY_AMOUNT / p
                    mexc.set_leverage(LEVERAGE, SYMBOL)
                    mexc.create_market_buy_order(SYMBOL, amount)
                    mexc.create_order(SYMBOL, 'LIMIT', 'sell', amount, p*(1+TP_TARGET), {'reduceOnly': True})
                    mexc.create_order(SYMBOL, 'STOP_MARKET', 'sell', amount, None, {'stopPrice': p*(1+SL_LIMIT), 'reduceOnly': True})
                    st.success(f"🔥 تم قنص صفقة LONG عالمية عند {p}")

                # بيع قوي: السعر في قمة (RSI > 65) + تقاطع MACD سلبي + سيولة عالية
                elif r > 65 and m < s and v > avg_v:
                    amount = ENTRY_AMOUNT / p
                    mexc.set_leverage(LEVERAGE, SYMBOL)
                    mexc.create_market_sell_order(SYMBOL, amount)
                    mexc.create_order(SYMBOL, 'LIMIT', 'buy', amount, p*(1-TP_TARGET), {'reduceOnly': True})
                    mexc.create_order(SYMBOL, 'STOP_MARKET', 'buy', amount, None, {'stopPrice': p*(1-SL_LIMIT), 'reduceOnly': True})
                    st.warning(f"🔥 تم قنص صفقة SHORT عالمية عند {p}")

            st.write(f"📊 التحليل الحالي: RSI: {r:.2f} | MACD: {'إيجابي' if m > s else 'سلبي'} | السيولة: {'ممتازة' if v > avg_v else 'ضعيفة'}")
            time.sleep(15)

    except Exception as e:
        st.error(f"تنبيه: {e}")
        time.sleep(20)
        
