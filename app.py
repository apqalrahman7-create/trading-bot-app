import streamlit as st
import ccxt
import pandas as pd
import time

# --- 🚀 إعدادات القناص العالمي (تراكمي) ---
SYMBOLS = ['ORDI_USDT', 'BTC_USDT', 'ETH_USDT', 'SOL_USDT']
MAX_TRADES = 4
LEVERAGE = 5
RISK_PERCENT = 0.15 # الدخول بـ 15% من الرصيد المتاح

st.set_page_config(page_title="MEXC Force Connect", layout="wide")
st.title("🛡️ قناص MEXC - الاتصال الإجباري")

if 'running' not in st.session_state: st.session_state.running = False

with st.sidebar:
    st.header("🔑 Credentials")
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 تشغيل المحرك"): st.session_state.running = True
    if st.button("🛑 إيقاف"): st.session_state.running = False

# --- المحرك الرئيسي ---
if st.session_state.running and api_key and api_secret:
    try:
        # اتصال خام (Raw Connection) لتجاوز الحظر
        mexc = ccxt.mexc({
            'apiKey': api_key,
            'secret': api_secret,
            'options': {'defaultType': 'future'},
            'enableRateLimit': True
        })

        st.success("🔄 جاري الاتصال المباشر بالمنصة...")

        while st.session_state.running:
            # 1. جلب الرصيد بطريقة "خام" لتجاوز خطأ (Self Method)
            # نستخدم fetch_balance ونأخذ البيانات من القاموس مباشرة
            bal_data = mexc.fetch_balance()
            # الوصول المباشر للرصيد المتاح من بيانات المنصة
            try:
                available_bal = float(bal_data['info']['data']['availableBalance'])
            except:
                available_bal = float(bal_data['total']['USDT'])

            # 2. جلب الصفقات بطريقة مستقرة
            pos_data = mexc.fetch_positions()
            active_p = [p for p in pos_data if float(p.get('contracts', 0)) != 0]
            current_count = len(active_p)
            active_names = [p['symbol'] for p in active_p]

            st.write(f"💰 الرصيد المتاح للتراكم: **{available_bal:.2f} USDT**")
            st.write(f"📊 الصفقات النشطة: {current_count}/{MAX_TRADES}")

            # 3. محرك التداول التراكمي
            for symbol in SYMBOLS:
                if current_count >= MAX_TRADES: break
                
                if symbol not in active_names:
                    try:
                        ticker = mexc.fetch_ticker(symbol)
                        price = ticker['last']
                        
                        # حساب حجم الصفقة (تراكمي)
                        trade_value = available_bal * RISK_PERCENT
                        qty = (trade_value * LEVERAGE) / price
                        formatted_qty = float(mexc.amount_to_precision(symbol, qty))

                        if formatted_qty > 0:
                            # فتح الصفقة
                            mexc.create_market_order(symbol, 'buy', formatted_qty)
                            st.success(f"🎯 تم قنص {symbol} بمبلغ {trade_value:.2f}$")
                            current_count += 1
                            active_names.append(symbol)
                    except: continue

            time.sleep(20) # فحص كل 20 ثانية لضمان استقرار الاتصال من الهاتف

    except Exception as e:
        st.error(f"❌ فشل الاتصال: {str(e)}")
        st.info("💡 نصيحة: إذا كنت من الهاتف، تأكد من إغلاق أي VPN وجرب التشغيل مرة أخرى.")
        st.session_state.running = False
        
