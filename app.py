import streamlit as st
import ccxt
import pandas as pd
import time

# --- إعدادات الصفحة ---
st.set_page_config(page_title="MEXC AI Bot", layout="wide")

class MexcPowerBot:
    def __init__(self, api, secret):
        self.exchange = ccxt.mexc({
            'apiKey': api,
            'secret': secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'} # لضمان الدخول لمحفظة العقود الآجلة
        })

    def get_real_balance(self):
        """طريقة إجبارية لجلب الرصيد الحقيقي من MEXC"""
        try:
            # 1. تحديث التوقيت مع السيرفر لمنع رفض الطلب
            self.exchange.load_markets()
            
            # 2. طلب الرصيد الخاص بالعقود الآجلة تحديداً
            balance_data = self.exchange.fetch_balance({'type': 'swap'})
            
            # 3. البحث عن USDT في جميع مستويات الاستجابة
            total_usdt = 0.0
            if 'USDT' in balance_data:
                total_usdt = float(balance_data['USDT'].get('total', 0))
            
            # إذا ظل صفراً، نجرب الطريقة البديلة (البحث في القائمة الشاملة)
            if total_usdt == 0:
                for b in balance_data.get('info', []):
                    if b.get('asset') == 'USDT':
                        total_usdt = float(b.get('total', 0))
                        break
            
            return total_usdt
        except Exception as e:
            return f"Error: {str(e)}"

# --- الواجهة الرئيسية ---
st.title("🤖 بوت MEXC المطور (حل مشكلة الرصيد الصفر)")

with st.sidebar:
    api_key = st.text_input("API Key", type="password")
    secret_key = st.text_input("Secret Key", type="password")

if api_key and secret_key:
    bot = MexcPowerBot(api_key, secret_key)
    # استدعاء الرصيد بالطريقة الجديدة
    balance = bot.get_real_balance()

    if isinstance(balance, float):
        st.metric("الرصيد المكتشف في المحفظة", f"${balance:.2f} USDT")
        
        if balance > 0:
            st.success("✅ تم اكتشاف الرصيد بنجاح! البوت جاهز للتداول.")
            # هنا تضع زر التشغيل ومنطق التداول الذي أعطيتك إياه سابقاً
        else:
            st.warning("⚠️ الرصيد يظهر 0.00. تأكد من تحويل USDT إلى محفظة Futures داخل MEXC.")
    else:
        st.error(f"❌ خطأ في الاتصال: {balance}")
else:
    st.info("بانتظار إدخال المفاتيح...")
    
