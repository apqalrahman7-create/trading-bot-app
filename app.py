import streamlit as st
import ccxt
import pandas as pd
import time

# --- 🚀 إعدادات الربح التراكمي (Compound) ---
SYMBOLS = ['ORDI_USDT', 'BTC_USDT', 'ETH_USDT', 'SOL_USDT']
MAX_TRADES = 4
LEVERAGE = 5
RISK_PERCENT = 0.15 # الدخول بـ 15% من الرصيد المتاح

st.set_page_config(page_title="MEXC Sniper Fix", layout="wide")
st.title("🎯 قناص MEXC - النسخة المصححة للهاتف")

if 'running' not in st.session_state: st.session_state.running = False

with st.sidebar:
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 تشغيل المحرك"): st.session_state.running = True
    if st.button("🛑 إيقاف"): st.session_state.running = False

if st.session_state.running and api_key and api_secret:
    try:
        # الاتصال بنظام الـ Swap (العقود الآجلة في MEXC)
        mexc = ccxt.mexc({
            'apiKey': api_key,
            'secret': api_secret,
            'options': {'defaultType': 'swap'}, # ضروري جداً لـ MEXC
            'enableRateLimit': True
        })

        st.info("🔄 جاري الاتصال المباشر بالرصيد...")

        while st.session_state.running:
            # 1. جلب الرصيد بطريقة الـ Swap الصحيحة (تجاوز خطأ Self Method)
            balance = mexc.fetch_balance()
            # استخراج الرصيد المتاح من بيانات الـ Swap
            try:
                available_bal = float(balance['info']['data']['availableBalance'])
            except:
                available_bal = float(balance['USDT']['free'])

            # 2. فحص الصفقات النشطة
            pos = mexc.fetch_positions()
            active_p = [p for p in pos if float(p.get('contracts', 0)) != 0]
            current_count = len(active_p)
            active_names = [p['symbol'] for p in active_p]

            st.write(f"💰 الرصيد المتاح: **{available_bal:.2f} USDT**")
            st.write(f"📊 الصفقات: {current_count}/{MAX_TRADES}")

            # 3. منطق التداول التراكمي
            for symbol in SYMBOLS:
                if current_count >= MAX_TRADES: break
                
                if symbol not in active_names:
                    try:
                        ticker = mexc.fetch_ticker(symbol)
                        price = ticker['last']
                        
                        # حساب الكمية (تراكمي)
                        trade_value = available_bal * RISK_PERCENT
                        qty = (trade_value * LEVERAGE) / price
                        
                        # تنفيذ الأمر (بصيغة MEXC الصحيحة)
                        mexc.create_market_order(symbol, 'buy', qty)
                        st.success(f"🎯 تم قنص {symbol} بمبلغ {trade_value:.2f}$")
                        current_count += 1
                    except: continue

            time.sleep(20)

    except Exception as e:
        st.error(f"❌ خطأ في الاتصال: {str(e)}")
        st.session_state.running = False
        
