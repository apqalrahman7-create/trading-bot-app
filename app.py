import streamlit as st
import ccxt

st.title("🚨 زر الطوارئ - إغلاق كافة الصفقات")

api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

if st.button("🔴 بيع كل شيء فوراً (Market Sell All)"):
    if not api_key or not api_secret:
        st.error("أدخل المفاتيح أولاً!")
    else:
        try:
            ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret})
            balance = ex.fetch_balance()
            
            # جلب كل العملات التي تملك منها رصيد (أكثر من صفر)
            owned_assets = {k: v for k, v in balance['total'].items() if v > 0 and k not in ['USDT', 'MX']}
            
            if not owned_assets:
                st.success("✅ لا توجد صفقات مفتوحة، الرصيد كله USDT.")
            else:
                for coin, amount in owned_assets.items():
                    symbol = f"{coin}/USDT"
                    try:
                        st.warning(f"⏳ جاري بيع {symbol}...")
                        # التأكد من الكمية المتاحة للبيع (Free balance)
                        free_bal = balance['free'].get(coin, 0)
                        if free_bal > 0:
                            p_amount = ex.amount_to_precision(symbol, free_bal)
                            ex.create_market_sell_order(symbol, p_amount)
                            st.success(f"✅ تم بيع {coin} بالكامل.")
                    except Exception as e:
                        st.error(f"❌ تعذر بيع {coin}: {e}")
                
                st.balloons()
                st.success("🏁 تمت تصفية جميع المراكز بنجاح.")
        except Exception as e:
            st.error(f"❌ خطأ في الاتصال بالمنصة: {e}")

if st.button("🚫 إلغاء كافة الطلبات المعلقة"):
    try:
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret})
        # إلغاء كافة الأوامر المفتوحة التي لم تنفذ بعد
        ex.cancel_all_orders()
        st.success("✅ تم إلغاء كافة الطلبات المعلقة بنجاح.")
    except Exception as e:
        st.error(f"❌ خطأ: {e}")
        
