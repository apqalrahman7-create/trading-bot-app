import streamlit as st
import ccxt
import time
import pandas as pd

st.set_page_config(page_title="MEXC Force Connection", layout="wide")

class MexcForceBot:
    def __init__(self, api, secret):
        self.exchange = ccxt.mexc({
            'apiKey': api,
            'secret': secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'} # العقود الآجلة
        })

    def force_get_balance(self):
        try:
            # محاولة جلب الرصيد بكل الطرق الممكنة في MEXC
            raw_balance = self.exchange.fetch_balance()
            
            # البحث في العقود الآجلة (USDT-M)
            futures_bal = float(raw_balance.get('total', {}).get('USDT', 0))
            
            # إذا لم يجد شيئاً، يبحث في السبوت
            if futures_bal == 0:
                spot_bal = self.exchange.fetch_balance({'type': 'spot'})
                return float(spot_bal.get('total', {}).get('USDT', 0)), "سوق فوري (Spot)"
            
            return futures_bal, "عقود آجلة (Futures)"
        except Exception as e:
            return str(e), "خطأ في الاتصال"

# --- الواجهة الرئيسية ---
st.title("🛡️ نظام الربط الإجباري بمحفظة MEXC")

with st.sidebar:
    api = st.text_input("API Key", type="password")
    sec = st.text_input("Secret Key", type="password")

if api and sec:
    bot = MexcForceBot(api, sec)
    balance, wallet_type = bot.force_get_balance()

    if isinstance(balance, float):
        st.success(f"✅ تم الاتصال بنجاح! نوع المحفظة المكتشفة: {wallet_type}")
        st.metric("الرصيد الحقيقي المتاح للتداول", f"${balance:.2f}")
        
        if balance > 5:
            if st.button("🚀 ابدأ التداول التلقائي الفوري"):
                st.info("جاري تحليل السوق وتنفيذ الصفقات...")
                # (أوامر التداول المباشرة هنا)
        else:
            st.warning("⚠️ الرصيد المكتشف أقل من الحد الأدنى (5$). يرجى شحن المحفظة.")
    else:
        st.error(f"❌ فشل الاتصال. الرسالة من MEXC: {balance}")
        st.info("تأكد من تفعيل صلاحيات الـ API (Read & Trade) في إعدادات المنصة.")
        
