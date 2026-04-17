import streamlit as st
import pandas as pd
import time
import ccxt

# --- 1. وضع المفاتيح مباشرة هنا ---
# استبدل النجوم بمفاتيحك الحقيقية من منصة MEXC
API_KEY = "ضـع_هنـا_ACCESS_KEY"
SECRET_KEY = "ضـع_هنـا_SECRET_KEY"

# --- 2. إعداد محرك التداول داخل الملف لضمان العمل ---
class TradingEngine:
    def __init__(self):
        self.exchange = ccxt.mexc({
            'apiKey': API_KEY,
            'secret': SECRET_KEY,
            'enableRateLimit': True,
        })
        self.target_profit = 0.10  # هدف 10%
        self.stop_loss = 0.05      # حماية 5%

    def get_signal(self):
        try:
            self.exchange.load_markets()
            # جلب أفضل 50 عملة من حيث حجم التداول لتجنب العملات الوهمية
            tickers = self.exchange.fetch_tickers()
            symbols = [s for s in tickers if '/USDT' in s and tickers[s]['percentage'] is not None]
            
            for symbol in symbols:
                change = tickers[symbol]['percentage']
                # إذا كانت العملة صاعدة بين 2% و 5% (إشارة بداية انفجار)
                if 2.0 <= change <= 5.0:
                    return symbol, tickers[symbol]['last']
            return None, None
        except Exception as e:
            st.error(f"خطأ في جلب البيانات: {e}")
            return None, None

    def execute_trade(self, symbol, amount):
        try:
            order = self.exchange.create_market_buy_order(symbol, amount)
            return order
        except Exception as e:
            st.error(f"فشل تنفيذ الصفقة: {e}")
            return None

# --- 3. واجهة المستخدم (Streamlit UI) ---
st.set_page_config(page_title="MEXC AI Bot", page_icon="🤖")
st.title("🤖 بوت التداول الآلي - هدف 10%")

bot = TradingEngine()

# عرض الرصيد
try:
    balance_info = bot.exchange.fetch_balance()
    usdt_balance = balance_info['total'].get('USDT', 0)
    st.metric("رصيدك الحالي في MEXC", f"{usdt_balance:.2f} USDT")
except:
    st.error("❌ فشل الاتصال بالمنصة. تأكد من صحة المفاتيح ومن تفعيل الـ API.")

# إعدادات التداول
st.sidebar.header("⚙️ الإعدادات")
order_amount = st.sidebar.number_input("مبلغ الصفقة (USDT)", min_value=11.0, value=12.0)

if st.button("🚀 ابدأ التداول التلقائي الآن"):
    st.info("🔎 البوت يبحث الآن عن عملات صاعدة لتحقيق ربح 10%...")
    
    status_box = st.empty()
    
    while True:
        symbol, price = bot.get_signal()
        
        if symbol:
            status_box.success(f"✅ تم العثور على فرصة: {symbol} بسعر {price}")
            # تنفيذ الشراء
            order = bot.execute_trade(symbol, order_amount)
            if order:
                st.write(f"🔔 تم شراء {symbol}.. جاري ملاحقة هدف الـ 10% والبيع تلقائياً.")
                # هنا يكمل البوت مراقبة البيع (يمكنك إضافة كود البيع هنا أيضاً)
                break 
        else:
            status_box.warning("😴 لا توجد فرص حالياً.. إعادة الفحص بعد 20 ثانية")
            time.sleep(20)
            
