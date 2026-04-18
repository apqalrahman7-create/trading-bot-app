import streamlit as st
import ccxt
import pandas as pd
import time

# --- 🚀 إعدادات التنفيذ الاحترافي ---
SYMBOLS = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'ORDI/USDT:USDT', 'SOL/USDT:USDT']
ENTRY_USDT = 30  # مبلغ الدخول (يفضل 30$ لضمان تجاوز الحد الأدنى للعقود)
LEVERAGE = 5 

st.set_page_config(page_title="MEXC Sniper Fix", layout="wide")
st.title("⚡ منفذ الصفقات الفوري - نسخة العقود الصحيحة")

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

        st.success("✅ متصل بالمنصة.. جاري تنفيذ الأوامر")

        while run:
            # 1. جلب الصفقات المفتوحة
            pos = mexc.fetch_positions()
            active_list = [p['symbol'] for p in pos if float(p.get('contracts', 0)) != 0]
            
            for symbol in SYMBOLS:
                # تحويل اسم العملة للصيغة التي تفهمها MEXC في العقود
                clean_sym = symbol.replace('/', '').replace(':', '')
                
                if clean_sym not in active_list and len(active_list) < 4:
                    # جلب السعر الحالي
                    ticker = mexc.fetch_ticker(symbol)
                    price = float(ticker['last'])
                    
                    # --- الحسبة السحرية لتجاوز الخطأ ---
                    # تحويل المبلغ إلى "عدد عقود" صحيح (Integer)
                    amount_in_contracts = int((ENTRY_USDT * LEVERAGE) / price)
                    
                    if amount_in_contracts < 1:
                        amount_in_contracts = 1 # ضمان أقل كمية هي عقد واحد
                    
                    # ضبط الرافعة
                    try: mexc.set_leverage(LEVERAGE, symbol)
                    except: pass

                    # تنفيذ الأمر باستخدام عدد العقود الصحيح
                    mexc.create_market_buy_order(symbol, amount_in_contracts)
                    
                    st.toast(f"🎯 تم تنفيذ صفقة: {symbol}")
                    st.success(f"✅ دخلت صفقة {symbol} بـ {amount_in_contracts} عقد")
                    time.sleep(2) # مهلة بين الصفقات
            
            time.sleep(30)
    except Exception as e:
        st.error(f"❌ تنبيه من المنصة: {str(e)}")
        time.sleep(10)
        
