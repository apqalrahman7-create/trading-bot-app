import streamlit as st
import ccxt

# إعداد الواجهة لتكون بسيطة ومركزة على الهدف
st.set_page_config(page_title="أداة التصفية الفورية", layout="centered")
st.title("🚨 مركز التحكم بالطوارئ")
st.subheader("بيع كافة العملات المفتوحة وإلغاء الطلبات")

# خانات إدخال المفاتيح (مخفية ككلمة سر)
with st.expander("🔑 أدخل مفاتيح API هنا (للاستخدام لمرة واحدة فقط)", expanded=True):
    key = st.text_input("API Key", type="password", help="ضع هنا مفتاح الـ API الخاص بك")
    secret = st.text_input("Secret Key", type="password", help="ضع هنا المفتاح السري")

if st.button("🔥 تصفية المحفظة وإغلاق كافة الصفقات", use_container_width=True):
    if not key or not secret:
        st.error("⚠️ يرجى إدخال المفاتيح أولاً!")
    else:
        try:
            # الاتصال بالمنصة
            ex = ccxt.mexc({
                'apiKey': key,
                'secret': secret,
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            })
            
            # الخطوة 1: إلغاء أي طلبات معلقة (لتحرير العملات المحجوزة)
            st.info("🔄 جاري إلغاء كافة الطلبات المعلقة...")
            ex.cancel_all_orders()
            st.success("✅ تم إلغاء الطلبات.")

            # الخطوة 2: فحص الأرصدة
            st.info("🔍 جاري جرد العملات في المحفظة...")
            balance = ex.fetch_balance()
            
            # تصفية العملات التي لها رصيد (أكبر من صفر وليست USDT)
            for coin, amount in balance['total'].items():
                if amount > 0 and coin not in ['USDT', 'MX', 'BNB']: 
                    symbol = f"{coin}/USDT"
                    try:
                        # التأكد من الكمية المتاحة للبيع
                        free_bal = balance['free'].get(coin, 0)
                        if free_bal > 0:
                            st.write(f"⏳ جاري بيع {coin}...")
                            # تحويل الكمية للصيغة التي تقبلها MEXC
                            precise_amount = ex.amount_to_precision(symbol, free_bal)
                            ex.create_market_sell_order(symbol, precise_amount)
                            st.success(f"✔️ تم بيع {coin} بنجاح.")
                    except Exception as e:
                        st.error(f"❌ تعذر بيع {coin}: السعر قد يكون أقل من الحد الأدنى للبيع (5$).")
            
            st.balloons()
            st.success("🏁 اكتملت العملية. يرجى التأكد من تطبيق MEXC الآن.")
            
        except Exception as e:
            st.error(f"❌ خطأ في الاتصال: تأكد من صحة المفاتيح أو صلاحيات التداول (Spot Trading).")

st.divider()
st.caption("ملاحظة: بمجرد الانتهاء، قم بحذف المفاتيح من الخانات أعلاه أو أغلق الصفحة.")
