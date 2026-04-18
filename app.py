import streamlit as st
import ccxt
import pandas as pd
import time

# --- 🚀 إعدادات القناص المتعدد (Compound & Multi-Trade) ---
SYMBOLS = ['ORDI_USDT', 'BTC_USDT', 'ETH_USDT', 'SOL_USDT', 'SUI_USDT', 'XRP_USDT']
MAX_TRADES = 4
LEVERAGE = 5
RISK_PERCENT = 0.15 # يستخدم 15% من الرصيد لكل صفقة لضمان فتح 4 صفقات

st.set_page_config(page_title="Multi-Sniper Pro", layout="wide")
st.title("🎯 قناص MEXC المتعدد (4 صفقات)")

if 'running' not in st.session_state: st.session_state.running = False

with st.sidebar:
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 تشغيل"): st.session_state.running = True
    if st.button("🛑 إيقاف"): st.session_state.running = False

if st.session_state.running and api_key and api_secret:
    try:
        mexc = ccxt.mexc({
            'apiKey': api_key, 'secret': api_secret,
            'options': {'defaultType': 'swap'}, 'enableRateLimit': True
        })

        while st.session_state.running:
            # 1. تحديث البيانات فوراً (الرصيد والصفقات)
            balance = mexc.fetch_balance()
            try:
                available_bal = float(balance['info']['data']['availableBalance'])
            except:
                available_bal = float(balance['USDT']['free'])

            pos = mexc.fetch_positions()
            active_p = [p['symbol'] for p in pos if float(p.get('contracts', 0)) != 0]
            current_count = len(active_p)
            
            st.write(f"💰 الرصيد المتاح: **{available_bal:.2f} USDT** | صفقات نشطة: {current_count}/4")

            # 2. مسح القائمة وفتح صفقات حتى نصل لـ 4
            for symbol in SYMBOLS:
                # إذا وصلنا لـ 4 صفقات توقف عن المسح في هذه الدورة
                if current_count >= MAX_TRADES: break 
                
                # إذا كانت العملة ليست مفتوحة حالياً، افتحها
                if symbol not in active_p:
                    try:
                        ticker = mexc.fetch_ticker(symbol)
                        price = ticker['last']
                        
                        # حساب الحجم التراكمي (15% من الرصيد الحالي)
                        trade_value = available_bal * RISK_PERCENT
                        qty = (trade_value * LEVERAGE) / price
                        
                        # تنفيذ الأمر
                        mexc.create_market_order(symbol, 'buy', qty)
                        st.success(f"🚀 تم فتح صفقة {symbol} بمبلغ {trade_value:.2f}$")
                        
                        # تحديث العداد والقائمة فوراً للانتقال للعملة التالية
                        current_count += 1
                        active_p.append(symbol) 
                    except: continue

            time.sleep(15) # انتظر 15 ثانية قبل دورة المسح التالية

    except Exception as e:
        st.error(f"⚠️ خطأ: {str(e)}")
        time.sleep(10)
        
