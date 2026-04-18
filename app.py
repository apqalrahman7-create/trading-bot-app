import streamlit as st
import ccxt
import pandas as pd
import time

# --- 🚀 إعدادات التنفيذ الفوري ---
SYMBOLS = ['BTC_USDT', 'ETH_USDT', 'ORDI_USDT', 'SOL_USDT']
ENTRY_SIZE = 10 # بالدولار

st.title("⚡ منفذ الصفقات الفوري - MEXC 2026")

with st.sidebar:
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    run = st.toggle("🚀 تشغيل التداول الحقيقي")

if run and api_key and api_secret:
    try:
        # اتصال مباشر مع تحديد الدومين الجديد لـ 2026 (api.mexc.com)
        mexc = ccxt.mexc({
            'apiKey': api_key,
            'secret': api_secret,
            'options': {'defaultType': 'swap'},
            'urls': {'api': {'public': 'https://api.mexc.com/api/v3', 'private': 'https://api.mexc.com/api/v3'}}
        })

        st.success("✅ تم الربط بالمنصة بنجاح")

        while run:
            # فحص الصفقات
            pos = mexc.fetch_positions()
            active = [p['symbol'] for p in pos if float(p.get('contracts', 0)) != 0]
            
            for symbol in SYMBOLS:
                if symbol not in active and len(active) < 4:
                    # جلب السعر الحالي
                    price = float(mexc.fetch_ticker(symbol)['last'])
                    
                    # فتح صفقة شراء فورية للتجربة (بمجرد التشغيل)
                    mexc.create_market_buy_order(symbol, ENTRY_SIZE / price)
                    st.toast(f"🎯 تم تنفيذ صفقة فورية على {symbol}")
                    break # لفتح صفقة واحدة في كل دورة
            
            time.sleep(30)
    except Exception as e:
        st.error(f"❌ خطأ: {e}")
        
