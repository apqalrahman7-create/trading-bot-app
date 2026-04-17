import streamlit as st
import ccxt

st.title("🚨 إغلاق الصفقات الأربعة فوراً")

api_key = st.text_input("API Key", type="password")
api_secret = st.text_input("Secret Key", type="password")

if st.button("🔥 تصفية كل العملات الآن"):
    try:
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret})
        balance = ex.fetch_balance()
        
        # جلب أي عملة رصيدها أكبر من 0 (ماعدا USDT)
        for coin, total in balance['total'].items():
            if total > 0 and coin not in ['USDT', 'MX']:
                symbol = f"{coin}/USDT"
                try:
                    # جلب الكمية المتاحة للبيع
                    amount = balance['free'][coin]
                    if amount > 0:
                        precise_amount = ex.amount_to_precision(symbol, amount)
                        ex.create_market_sell_order(symbol, precise_amount)
                        st.success(f"✅ تم بيع {symbol}")
                except:
                    st.error(f"❌ فشل بيع {coin}")
        st.balloons()
    except Exception as e:
        st.error(f"خطأ: {e}")
        
