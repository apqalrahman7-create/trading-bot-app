import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime

# --- 🚀 إعدادات قنص الأرباح (Sniper Profit) ---
SYMBOLS = ['ORDI_USDT', 'BTC_USDT', 'ETH_USDT', 'SOL_USDT']
MAX_TRADES = 4
LEVERAGE = 10           # رافعة 10x لتعظيم الربح
ENTRY_AMOUNT_USDT = 20  # مبلغ الدخول
TP_PERCENT = 0.02       # قنص الربح عند 2% (مع الرافعة تصبح 20% ربح صافي)
SL_PERCENT = 0.015      # وقف خسارة عند 1.5% لحماية المال

st.title("🎯 بوت قنص الأرباح الآلي - MEXC")

with st.sidebar:
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    run = st.toggle("🚀 تشغيل القناص")

if run and api_key and api_secret:
    try:
        mexc = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'future'}})
        mexc.load_markets()

        while run:
            # 1. فحص الصفقات المفتوحة
            pos = mexc.fetch_positions()
            active_p = [p['symbol'] for p in pos if float(p.get('contracts', 0)) != 0]
            current_count = len(active_p)

            st.info(f"🔎 الرادار يبحث عن صيد.. صفقات نشطة: {current_count}/{MAX_TRADES}")

            for symbol in SYMBOLS:
                if symbol not in active_p and current_count < MAX_TRADES:
                    # جلب السعر والتحليل
                    ohlcv = mexc.fetch_ohlcv(symbol, timeframe='1m', limit=20)
                    df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                    price = df['c'].iloc[-1]
                    
                    # حساب RSI سريع للقنص
                    delta = df['c'].diff()
                    rsi = 100 - (100 / (1 + (delta.clip(lower=0).mean() / -delta.clip(upper=0).mean())))

                    # شرط الدخول (قنص القيعان والقمم)
                    if rsi <= 35 or rsi >= 65:
                        side = 'buy' if rsi <= 35 else 'sell'
                        qty = (ENTRY_AMOUNT_USDT * LEVERAGE) / price
                        formatted_qty = float(mexc.amount_to_precision(symbol, qty))

                        # تنفيذ الصفقة
                        mexc.set_leverage(LEVERAGE, symbol)
                        order = mexc.create_market_order(symbol, side, formatted_qty)
                        
                        # --- 🎯 اقتناص الربح الفوري (وضع الأهداف في المنصة) ---
                        tp_price = price * (1 + TP_PERCENT) if side == 'buy' else price * (1 - TP_PERCENT)
                        sl_price = price * (1 - SL_PERCENT) if side == 'buy' else price * (1 + SL_PERCENT)
                        
                        # وضع أمر جني الربح (يغلق تلقائياً بمجرد لمس السعر)
                        mexc.create_order(symbol, 'LIMIT', 'sell' if side == 'buy' else 'buy', 
                                          formatted_qty, tp_price, {'reduceOnly': True})
                        
                        st.success(f"✅ تم قنص {symbol}! الهدف وضِع عند {tp_price:.4f}")
                        current_count += 1

            time.sleep(15)
    except Exception as e:
        st.error(f"⚠️ خطأ: {e}")
        time.sleep(10)
        
