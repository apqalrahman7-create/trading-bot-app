import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime

# --- إعدادات القوة والمنطق (2026 Settings) ---
SYMBOLS = ['ORDI_USDT', 'BTC_USDT', 'SOL_USDT', 'ETH_USDT']
MAX_TRADES = 4
LEVERAGE = 3             # تقليل الرافعة المالية لـ 3x لزيادة الأمان
ENTRY_USDT = 10 
TP = 0.015               # هدف ربح 1.5%
SL = -0.012              # وقف خسارة صارم 1.2%

st.title("🛡️ Professional Sniper - Safe Mode 2026")

def get_data(mexc, symbol, tf='5m'):
    ohlcv = mexc.fetch_ohlcv(symbol, timeframe=tf, limit=200)
    df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
    # إضافة مؤشرات القوة
    df['ema200'] = df['c'].ewm(span=200).mean()
    delta = df['c'].diff()
    up = delta.clip(lower=0).rolling(14).mean()
    down = -delta.clip(upper=0).rolling(14).mean()
    df['rsi'] = 100 - (100 / (1 + (up / down)))
    return df

# واجهة التحكم
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")
run = st.sidebar.toggle("تشغيل المحرك المحترف")

if run and api_key and api_secret:
    try:
        mexc = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'swap'}})
        while run:
            pos = mexc.fetch_positions()
            active_list = [p['symbol'] for p in pos if float(p.get('contracts', 0)) != 0]
            
            for symbol in SYMBOLS:
                if len(active_list) >= MAX_TRADES: break
                if symbol in active_list: continue

                df = get_data(mexc, symbol)
                price = df['c'].iloc[-1]
                rsi = df['rsi'].iloc[-1]
                ema = df['ema200'].iloc[-1]
                vol = df['v'].iloc[-1]
                avg_vol = df['v'].mean()

                # --- شروط الدخول الاحترافية (بوابة المنطق) ---
                # الشراء: السعر فوق EMA (ترند صاعد) + RSI منخفض + انفجار سيولة
                if price > ema and rsi <= 35 and vol > (avg_vol * 1.5):
                    mexc.create_market_buy_order(symbol, ENTRY_USDT/price)
                    st.success(f"🎯 قنص شراء آمن: {symbol}")
                
                # البيع: السعر تحت EMA (ترند هابط) + RSI مرتفع + انفجار سيولة
                elif price < ema and rsi >= 65 and vol > (avg_vol * 1.5):
                    mexc.create_market_sell_order(symbol, ENTRY_AMOUNT/price)
                    st.warning(f"🎯 قنص بيع آمن: {symbol}")

            time.sleep(20)
    except Exception as e:
        st.error(f"خطأ: {e}")
        
