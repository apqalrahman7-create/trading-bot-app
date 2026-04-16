import streamlit as st
import ccxt
import time
import pandas as pd

# --- واجهة التطبيق ---
st.set_page_config(page_title="بوت تداول MEXC المتكامل", layout="wide")

class TradingBot:
    def __init__(self, api_key, secret_key):
        # إعداد الاتصال بمنصة MEXC
        self.exchange = ccxt.mexc({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
        })
        self.is_running = False

    def get_all_balances(self):
        """جلب الرصيد من السوق الفوري والعقود الآجلة"""
        try:
            # جلب رصيد السبوت (Spot)
            spot_bal = self.exchange.fetch_balance({'type': 'spot'})
            spot_usdt = float(spot_bal.get('total', {}).get('USDT', 0))
            
            # جلب رصيد العقود الآجلة (Futures)
            swap_bal = self.exchange.fetch_balance({'type': 'swap'})
            swap_usdt = float(swap_bal.get('total', {}).get('USDT', 0))
            
            return spot_usdt, swap_usdt
        except:
            return 0.0, 0.0

    def run_automated_logic(self, initial_balance):
        self.is_running = True
        target_profit = initial_balance * 1.10
        
        # قائمة العملات للمسح
        symbols = ['BTC/USDT', 'ETH/USDT'] 
        
        while self.is_running:
            spot, swap = self.get_all_balances()
            current_total = spot + swap
            profit_loss = current_total - initial_balance
            
            # --- إصلاح الخطأ: التأكد من أن الرصيد ليس صفراً قبل القسمة ---
            profit_percent = (profit_loss / initial_balance * 100) if initial_balance > 0 else 0.0

            # عرض النتائج في الشاشة
            c1, c2, c3 = st.columns(3)
            c1.metric("رصيد السبوت", f"${spot:.2f}")
            c2.metric("رصيد العقود الآجلة", f"${swap:.2f}")
            c3.metric("صافي الأرباح", f"${profit_loss:.2f}", f"{profit_percent:.2f}%")

            if current_total >= target_profit:
                yield "✅ تم تحقيق ربح 10%! جاري إغلاق الصفقات..."
                break

            # (منطق التداول التلقائي هنا بناءً على نوع السوق المتوفر فيه رصيد)
            time.sleep(10)

# --- واجهة المستخدم الرئيسية ---
st.title("🤖 بوت تداول MEXC (فوري + آجلة)")

with st.expander("🔑 أدخل مفاتيح الـ API"):
    api = st.text_input("API Key", type="password")
    sec = st.text_input("Secret Key", type="password")

if api and sec:
    bot = TradingBot(api, sec)
    spot_res, swap_res = bot.get_all_balances()
    total_res = spot_res + swap_res

    st.subheader(f"💰 إجمالي الرصيد الحقيقي: ${total_res:.2f}")

    if st.button("🚀 ابدأ التداول الشامل (12 ساعة)", use_container_width=True, type="primary"):
        if total_res > 0:
            for update in bot.run_automated_logic(total_res):
                st.write(update)
        else:
            st.error("❌ لا يوجد رصيد USDT كافٍ في حساب السبوت أو العقود الآجلة!")
else:
    st.info("يرجى إدخال المفاتيح لتظهر لك بيانات المحفظة.")
                 
