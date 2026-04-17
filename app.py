import streamlit as st
import ccxt
import time

# --- 1. ضع مفاتيحك هنا مباشرة ---
# امسح النجوم وضع رموزك الحقيقية من MEXC
API_KEY = "ضـع_هنـا_الـACCESS_KEY"
SECRET_KEY = "ضـع_هنـا_الـSECRET_KEY"

# --- 2. محرك التداول (مدمج لضمان العمل) ---
class TradingBot:
    def __init__(self):
        self.ex = ccxt.mexc({
            'apiKey': API_KEY,
            'secret': SECRET_KEY,
            'enableRateLimit': True,
        })

    def get_balance(self):
        return self.ex.fetch_balance()['total'].get('USDT', 0)

    def scan_and_trade(self, amount):
        tickers = self.ex.fetch_tickers()
        for symbol, t in tickers.items():
            if '/USDT' in symbol and 2.0 <= t.get('percentage', 0) <= 5.0:
                # تنفيذ الشراء
                order = self.ex.create_market_buy_order(symbol, amount)
                return symbol, t['last']
        return None, None

# --- 3. واجهة Streamlit ---
st.title("🤖 بوت MEXC التلقائي (10% ربح)")

try:
    bot = TradingBot()
    bal = bot.get_balance()
    st.success(f"💰 الرصيد المتصل الآن: {bal:.2f} USDT")
    
    amount = st.number_input("مبلغ التداول", value=12.0, min_value=11.0)
    
    if st.button("🚀 تشغيل البوت"):
        st.info("🔎 جاري البحث عن عملات تحقق شروط الربح...")
        sym, price = bot.scan_and_trade(amount)
        if sym:
            st.write(f"✅ تم شراء {sym} بسعر {price}")
            st.write(f"🎯 الهدف القادم: بيع عند {price * 1.10:.4f} (ربح 10%)")
        else:
            st.warning("😴 لم يتم العثور على فرص صاعدة حالياً.")

except Exception as e:
    st.error(f"⚠️ خطأ: تأكد من وضع المفاتيح داخل الكود بشكل صحيح. الخطأ: {e}")
    
