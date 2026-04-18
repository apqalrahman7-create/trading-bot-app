import streamlit as st
import ccxt
import pandas as pd
import time

# --- 🚀 إعدادات التنفيذ الفوري (المصححة لـ MEXC) ---
SYMBOLS = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'ORDI/USDT:USDT', 'SOL/USDT:USDT']
ENTRY_USDT = 25  # رفع المبلغ لـ 25$ لضمان تجاوز الحد الأدنى للمنصة
LEVERAGE = 5 

st.title("⚡ منفذ الصفقات الفوري - MEXC 2026")

with st.sidebar:
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    run = st.toggle("🚀 تشغيل التداول الحقيقي")

if run and api_key and api_secret:
    try:
        mexc = ccxt.mexc({
            'apiKey': api_key,
            'secret': api_secret,
            'options': {'defaultType': 'future'},
            'enableRateLimit': True
        })

        st.success("✅ تم الربط بالمنصة بنجاح")

        while run:
            # 1. جلب الصفقات الحالية
            pos = mexc.fetch_positions()
            active = [p['symbol'] for p in pos if float(p.get('contracts', 0)) != 0]
            
            for symbol in SYMBOLS:
                clean_sym = symbol.replace('/', '').replace(':', '')
                if clean_sym not in active and len(active) < 4:
                    # جلب بيانات العملة لمعرفة أقل كمية مسموحة (Precision)
                    market = mexc.market(symbol)
                    price = float(mexc.fetch_ticker(symbol)['last'])
                    
                    # حساب الكمية وتقريبها حسب قوانين المنصة
                    amount = (ENTRY_USDT * LEVERAGE) / price
                    amount_precision = mexc.amount_to_precision(symbol, amount)
                    
                    # ضبط الرافعة قبل الدخول
                    try: mexc.set_leverage(LEVERAGE, symbol)
                    except: pass

                    # تنفيذ الأمر
                    mexc.create_market_buy_order(symbol, amount_precision)
                    st.toast(f"🎯 تم تنفيذ صفقة ناجحة على {symbol}")
                    st.success(f"✅ دخلت صفقة {symbol} بكمية {amount_precision}")
            
            time.sleep(30)
    except Exception as e:
        st.error(f"❌ خطأ: {e}")
        time.sleep(10)
        
