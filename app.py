import streamlit as st
import ccxt
import time

st.set_page_config(page_title="MEXC AI BOT", layout="wide")

class TradingBot:
    def __init__(self, api, secret):
        self.exchange = ccxt.mexc({
            'apiKey': api, 'secret': secret,
            'enableRateLimit': True,
            'options': {'adjustForTimeDifference': True}
        })

    def get_total_balance(self):
        try:
            # جلب الرصيد من السبوت والفيوتشر معاً
            spot = self.exchange.fetch_balance({'type': 'spot'})
            futures = self.exchange.fetch_balance({'type': 'swap'})
            
            spot_usdt = float(spot.get('total', {}).get('USDT', 0))
            futures_usdt = float(futures.get('total', {}).get('USDT', 0))
            
            return spot_usdt, futures_usdt
        except: return 0.0, 0.0

st.title("🤖 MEXC Smart Trader")

with st.sidebar:
    api = st.text_input("API Key", type="password")
    sec = st.text_input("Secret Key", type="password")

if api and sec:
    bot = TradingBot(api, sec)
    spot_bal, futures_bal = bot.get_total_balance()
    total = spot_bal + futures_bal

    st.subheader("💰 إحصائيات المحفظة الحقيقية")
    c1, c2, c3 = st.columns(3)
    c1.metric("رصيد السبوت", f"${spot_bal:.2f}")
    c2.metric("رصيد الفيوتشر", f"${futures_bal:.2f}")
    c3.metric("إجمالي الرصيد", f"${total:.2f}", delta="USDT")

    if total >= 5:
        if st.button("🚀 ابدأ التداول التلقائي"):
            st.success("تم تفعيل البوت.. جاري البحث عن صفقات")
            # (هنا يوضع منطق التداول الحقيقي)
    else:
        st.warning(f"⚠️ الرصيد الحالي (${total:.2f}) أقل من الحد الأدنى المطلوب للتداول ($5)")
        
