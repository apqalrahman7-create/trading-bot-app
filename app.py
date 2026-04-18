import streamlit as st
import ccxt
import pandas as pd
import time

# --- ⚙️ إعدادات توزيع الرصيد (50 صفقة) ---
SYMBOLS = ['ORDI_USDT', 'BTC_USDT', 'ETH_USDT', 'SOL_USDT', 'XRP_USDT', 'ADA_USDT', 'SUI_USDT', 'PEPE_USDT']
MAX_TRADES = 50           # السماح بفتح حتى 50 صفقة
LEVERAGE = 5              # رافعة منخفضة للأمان
RISK_PER_TRADE = 0.02     # استخدام 2% فقط من المحفظة لكل صفقة (100% / 50 صفقة)

st.title("🎯 قناص MEXC - توزيع المحفظة (50 صفقة)")

if 'running' not in st.session_state: st.session_state.running = False

with st.sidebar:
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    run = st.toggle("🚀 تشغيل القناص")

if run and api_key and api_secret:
    try:
        mexc = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'future'}})
        
        while run:
            # 1. جلب الرصيد المتاح حالياً
            balance = mexc.fetch_balance()
            available_balance = float(balance['info']['data']['availableBalance'])
            
            # 2. جلب الصفقات النشطة
            pos = mexc.fetch_positions()
            active_p = [p for p in pos if float(p.get('contracts', 0)) != 0]
            current_count = len(active_p)

            st.write(f"💰 رصيد متاح: {available_balance:.2f} | صفقات: {current_count}/{MAX_TRADES}")

            for symbol in SYMBOLS:
                if current_count >= MAX_TRADES: break
                
                # فحص إذا كانت العملة مفتوحة
                if not any(p['symbol'] == symbol for p in active_p):
                    try:
                        ticker = mexc.fetch_ticker(symbol)
                        price = float(ticker['last'])
                        
                        # حساب الكمية (2% من الرصيد المتاح)
                        trade_amount = available_balance * RISK_PER_TRADE
                        qty = (trade_amount * LEVERAGE) / price
                        formatted_qty = float(mexc.amount_to_precision(symbol, qty))

                        # --- حل خطأ الصورة (إرسال معاملات الهامش) ---
                        # openType: 2 (Cross Margin), positionType: 1 (Long) or 2 (Short)
                        side = 'buy' # مثال للشراء، يمكنك إضافة شرط RSI هنا
                        mexc.set_leverage(LEVERAGE, symbol, {
                            'openType': 2, 
                            'positionType': 1 if side == 'buy' else 2
                        })

                        # تنفيذ الصفقة
                        mexc.create_market_order(symbol, side, formatted_qty)
                        st.success(f"✅ فتح صفقة {symbol} بـ {trade_amount:.2f}$")
                        current_count += 1
                        time.sleep(1)
                    except: continue

            time.sleep(20)
    except Exception as e:
        st.error(f"⚠️ خطأ: {e}")
        time.sleep(10)
        
