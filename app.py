import streamlit as st
import ccxt

st.title("🚨 فحص الصلاحية وإغلاق الصفقات")

key = st.text_input("API Key", type="password")
secret = st.text_input("Secret Key", type="password")

if st.button("فحص وبيع الكل"):
    try:
        ex = ccxt.mexc({'apiKey': key, 'secret': secret})
        # فحص الاتصال أولاً
        account_info = ex.fetch_balance()
        st.success("✅ المفاتيح تعمل! جاري محاولة البيع...")
        
        for coin, amount in account_info['total'].items():
            if amount > 0 and coin not in ['USDT', 'MX']:
                symbol = f"{coin}/USDT"
                free_amount = account_info['free'].get(coin, 0)
                if free_amount > 0:
                    try:
                        ex.create_market_sell_order(symbol, ex.amount_to_precision(symbol, free_amount))
                        st.write(f"✔️ تم بيع {coin}")
                    except Exception as sell_error:
                        st.error(f"❌ فشل بيع {coin}: {sell_error}")
    except Exception as e:
        st.error(f"⛔ خطأ في المفاتيح: {e}")
        st.info("تأكد من تفعيل 'Spot Trading' في إعدادات API بالمنصة.")
        
