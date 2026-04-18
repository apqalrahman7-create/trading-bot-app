import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime

# --- 🚀 إعدادات الربح التراكمي (توزيع ذكي) ---
SYMBOLS = ['ORDI_USDT', 'BTC_USDT', 'ETH_USDT', 'SOL_USDT', 'SUI_USDT']
MAX_TRADES = 4
LEVERAGE = 5
RISK_PER_TRADE = 0.15  # الدخول بـ 15% من الرصيد المتاح لكل صفقة
TP_TARGET = 0.015      # هدف الربح 1.5% (7.5% مع الرافعة)

st.set_page_config(page_title="MEXC Compounding Sniper", layout="wide")
st.title("💰 قناص الربح التراكمي (النسخة المستقرة)")

if 'running' not in st.session_state: st.session_state.running = False

with st.sidebar:
    st.header("🔑 إعدادات API")
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 تشغيل المحرك"): st.session_state.running = True
    if st.button("🛑 إيقاف"): st.session_state.running = False

# منطقة عرض البيانات
status_area = st.empty()

if st.session_state.running and api_key and api_secret:
    try:
        # اتصال احترافي بـ MEXC
        mexc = ccxt.mexc({
            'apiKey': api_key,
            'secret': api_secret,
            'options': {'defaultType': 'future'},
            'enableRateLimit': True
        })

        while st.session_state.running:
            # 1. حل مشكلة "الطريقة الذاتية": جلب الرصيد المتاح بطريقة بديلة
            balance_info = mexc.fetch_balance()
            # قراءة مباشرة من البيانات الخام لـ MEXC لتجاوز الحظر
            available_balance = float(balance_info['info']['data']['availableBalance'])
            
            # 2. فحص الصفقات المفتوحة
            pos = mexc.fetch_positions()
            active_p = [p for p in pos if float(p.get('contracts', 0)) != 0]
            current_count = len(active_p)
            active_symbols = [p['symbol'] for p in active_p]

            with status_area.container():
                st.info(f"💵 الرصيد المتاح للتراكم: {available_balance:.2f} USDT")
                st.write(f"📊 الصفقات المفتوحة: {current_count}/{MAX_TRADES}")

            # 3. محرك القنص التراكمي
            for symbol in SYMBOLS:
                if current_count >= MAX_TRADES: break
                
                if symbol not in active_symbols:
                    try:
                        ticker = mexc.fetch_ticker(symbol)
                        price = float(ticker['last'])
                        
                        # حساب حجم الصفقة التراكمي (15% من الرصيد الحالي)
                        trade_value = available_balance * RISK_PER_TRADE
                        amount = (trade_value * LEVERAGE) / price
                        
                        # تقريب الكمية حسب قوانين المنصة
                        formatted_qty = float(mexc.amount_to_precision(symbol, amount))

                        if formatted_qty > 0:
                            # تنفيذ الصفقة مع ضبط الرافعة والمعاملات
                            try: mexc.set_leverage(LEVERAGE, symbol, {'openType': 2})
                            except: pass
                            
                            mexc.create_market_order(symbol, 'buy', formatted_qty)
                            
                            # وضع أمر جني الربح فوراً في المنصة (اقتناص الربح)
                            tp_price = price * (1 + TP_TARGET)
                            mexc.create_order(symbol, 'LIMIT', 'sell', formatted_qty, tp_price, {'reduceOnly': True})
                            
                            st.success(f"🎯 قنص تراكمي: {symbol} بمبلغ {trade_value:.2f}$")
                            current_count += 1
                            active_symbols.append(symbol)
                    except: continue

            time.sleep(20) # مهلة كافية لضمان استقرار الاتصال من الهاتف

    except Exception as e:
        st.error(f"⚠️ تنبيه فني: تأكد من تفعيل صلاحيات الـ API في MEXC")
        st.write(f"التفاصيل: {str(e)}")
        time.sleep(15)
        
