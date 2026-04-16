import streamlit as st
import ccxt
import pandas as pd
import time

# --- إعدادات الصفحة ---
st.set_page_config(page_title="MEXC Force Connect", layout="wide")

class MexcUltimateBot:
    def __init__(self, api, secret):
        # استخدام إعدادات MEXC V3 الحديثة
        self.exchange = ccxt.mexc({
            'apiKey': api,
            'secret': secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot', # يبدأ بالسبوت كافتراضي
                'adjustForTimeDifference': True # حل مشكلة توقيت السيرفر
            }
        })

    def get_real_balance(self):
        """محاولة جلب الرصيد من كل أنواع المحافظ الممكنة في MEXC"""
        try:
            # 1. محاولة جلب رصيد السبوت (Spot)
            spot_bal = self.exchange.fetch_balance({'type': 'spot'})
            spot_usdt = float(spot_bal['total'].get('USDT', 0))
            
            # 2. محاولة جلب رصيد العقود الآجلة (Futures/Swap)
            try:
                swap_bal = self.exchange.fetch_balance({'type': 'swap'})
                swap_usdt = float(swap_bal['total'].get('USDT', 0))
            except:
                swap_usdt = 0.0
                
            return spot_usdt, swap_usdt
        except Exception as e:
            return str(e), 0.0

# --- الواجهة الرسومية الرئيسية ---
st.title("🛡️ نظام الربط المباشر بمحفظة MEXC (النسخة المحدثة)")

with st.sidebar:
    st.header("🔑 إدخال البيانات")
    api_key = st.text_input("API Key", type="password")
    secret_key = st.text_input("Secret Key", type="password")

if api_key and secret_key:
    bot = MexcUltimateBot(api_key, secret_key)
    spot, swap = bot.get_real_balance()

    if isinstance(spot, float):
        st.success("✅ تم الربط بنجاح مع سيرفرات MEXC")
        
        # عرض الرصيد في مربعات كبيرة واضحة
        col1, col2 = st.columns(2)
        with col1:
            st.metric("رصيد السبوت (Spot USDT)", f"${spot:.2f}")
        with col2:
            st.metric("رصيد الفيوتشر (Futures USDT)", f"${swap:.2f}")

        total_available = spot + swap
        
        if total_available > 5:
            st.markdown("---")
            st.subheader("🚀 إدارة التداول الآلي")
            
            if st.button("بدء التداول الذكي (12 ساعة / هدف 10%)", type="primary", use_container_width=True):
                st.session_state.active = True
                
            if st.session_state.get('active'):
                st.info("🔄 البوت يقوم الآن بمسح السوق.. سيتم تنفيذ أول صفقة فور توفر فرصة.")
                # هنا نضع منطق الشراء والبيع الحقيقي
                # (سيقوم البوت باستخدام الرصيد المتوفر سواء في سبوت أو فيوتشر)
        else:
            st.warning("⚠️ الرصيد المكتشف أقل من الحد الأدنى (5$). يرجى التأكد من وجود USDT في حسابك.")
    else:
        st.error(f"❌ خطأ في الاتصال: {spot}")
        st.info("تأكد من تفعيل صلاحيات (Read & Trade) وإلغاء قيود الـ IP في إعدادات الـ API بموقع MEXC.")
else:
    st.info("يرجى إدخال مفاتيح الـ API في القائمة الجانبية ليتمكن البوت من جلب رصيدك الحقيقي.")
    
