import streamlit as st
import pandas as pd
import time
from bot_engine import TradingEngine # استدعاء المحرك الذي كتبناه سابقاً
import toml

# --- إعدادات الواجهة ---
st.set_page_config(page_title="MEXC AI Bot", layout="wide")
st.title("🤖 بوت التداول الذكي - هدف 10%")

# --- قراءة البيانات السرية ---
config = toml.load("secrets.toml")
api_key = config['mexc']['api_key']
secret_key = config['mexc']['secret_key']

# تهيئة المحرك
bot = TradingEngine(api_key, secret_key)

# --- واجهة العرض (Sidebar) ---
st.sidebar.header("⚙️ الإعدادات الحالية")
st.sidebar.write(f"🎯 الهدف: {config['trading_settings']['target_profit']*100}%")
st.sidebar.write(f"💰 المبلغ: {config['trading_settings']['order_amount']} USDT")

# --- عرض الرصيد المباشر ---
col1, col2 = st.columns(2)
with col1:
    try:
        balance = bot.exchange.fetch_balance()['total']['USDT']
        st.metric("رصيد USDT المتاح", f"{balance:.2f} $")
    except:
        st.error("خطأ في الربط! تأكد من مفاتيح API")

# --- زر التشغيل ---
if st.button("🚀 ابدأ البحث عن فرص (10% ربح)"):
    st.info("جاري فحص السوق الآن.. لا تغلق الصفحة")
    
    # مكان عرض التحديثات المباشرة
    status = st.empty()
    log_area = st.empty()
    
    while True:
        symbol, price = bot.get_signal()
        if symbol:
            status.success(f"✅ تم اكتشاف فرصة في {symbol} بسعر {price}")
            # تنفيذ الصفقة
            success = bot.execute_trade(symbol, config['trading_settings']['order_amount'])
            if success:
                st.balloons() # احتفال عند تحقيق الربح
                st.write(f"💰 مبروك! تم تحقيق هدف الـ 10% في عملة {symbol}")
        else:
            status.warning("😴 لا توجد فرص قوية حالياً.. إعادة الفحص بعد 30 ثانية")
        
        time.sleep(30)
        
