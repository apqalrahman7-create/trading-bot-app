import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime, timedelta

# --- الإعدادات الفنية ---
PROFIT_GOAL_PCT = 0.10  # الهدف 10% (5$)
TRADE_AMOUNT = 12.0     # الدخول بـ 12$ في كل صفقة
TAKE_PROFIT = 1.015     # جني ربح سريع عند 1.5% (لضمان كثرة الصفقات)
STOP_LOSS = 0.985       # إيقاف خسارة عند 1.5% لحماية الـ 50$
CYCLE_HOURS = 12        # مدة الدورة

st.title("⏱️ MEXC 12h Profit Sniper")

# تهيئة الجلسة
if 'start_time' not in st.session_state:
    st.session_state.start_time = datetime.now()
if 'total_profit' not in st.session_state:
    st.session_state.total_profit = 0.0

# الربط بالمنصة
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

def get_mexc():
    return ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'enableRateLimit': True})

if st.sidebar.button("ابدأ دورة الـ 12 ساعة"):
    ex = get_mexc()
    st.session_state.start_time = datetime.now()
    end_time = st.session_state.start_time + timedelta(hours=CYCLE_HOURS)
    
    st.info(f"بدأت الدورة. تنتهي الساعة: {end_time.strftime('%H:%M:%S')}")
    
    # جلب العملات النشطة فقط (حجم تداول عالي)
    markets = ex.load_markets()
    symbols = [s for s in markets if '/USDT' in s and markets[s]['active']]
    
    while datetime.now() < end_time:
        # حساب الوقت المتبقي
        remaining = end_time - datetime.now()
        st.sidebar.metric("الوقت المتبقي", str(remaining).split('.')[0])
        st.sidebar.metric("الأرباح المحققة", f"${st.session_state.total_profit:.2f}")

        for symbol in symbols:
            try:
                # 1. تحليل سريع (قوة نسبية)
                ticker = ex.fetch_ticker(symbol)
                # فحص العملات التي بدأت تتحرك (تذبذب)
                if ticker['percentage'] > 1: # العملات الصاعدة فقط
                    ohlcv = ex.fetch_ohlcv(symbol, '1m', limit=5)
                    df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
                    
                    # شرط الشراء: ارتداد بسيط بعد صعود
                    if df['c'].iloc[-1] > df['c'].mean():
                        price = ticker['last']
                        amount = TRADE_AMOUNT / price
                        
                        st.write(f"🎯 قنص سريع: {symbol}")
                        order = ex.create_market_buy_order(symbol, ex.amount_to_precision(symbol, amount))
                        
                        # --- مراقبة اللحظة (بيع فوري) ---
                        while True:
                            live_price = ex.fetch_ticker(symbol)['last']
                            if live_price >= price * TAKE_PROFIT:
                                bal = ex.fetch_balance()[symbol.split('/')]['free']
                                ex.create_market_sell_order(symbol, ex.amount_to_precision(symbol, bal))
                                profit = (live_price - price) * amount
                                st.session_state.total_profit += profit
                                st.success(f"💰 ربح سريع من {symbol}: +${profit:.2f}")
                                break
                            elif live_price <= price * STOP_LOSS:
                                bal = ex.fetch_balance()[symbol.split('/')]['free']
                                ex.create_market_sell_order(symbol, ex.amount_to_precision(symbol, bal))
                                st.error(f"⚠️ إيقاف خسارة في {symbol}")
                                break
                            time.sleep(1)
            except: continue
        
        if st.session_state.total_profit >= 5.0:
            st.balloons()
            st.success("✅ مبروك! حققت هدف الـ 10% قبل نهاية الـ 12 ساعة.")
            break
        
        time.sleep(10)
        
