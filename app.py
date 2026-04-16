import streamlit as st
import ccxt
import pandas as pd
import time

# --- إعدادات الواجهة ---
st.set_page_config(page_title="MEXC Smart Bot", layout="wide")

class MEXCBot:
    def __init__(self, api, secret):
        self.exchange = ccxt.mexc({
            'apiKey': api,
            'secret': secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'} 
        })

    def fetch_data(self):
        try:
            # جلب الرصيد الإجمالي (سبوت)
            bal = self.exchange.fetch_balance()
            usdt = float(bal['total'].get('USDT', 0))
            
            # جلب سعر البيتكوين وتحليله
            ohlcv = self.exchange.fetch_ohlcv('BTC/USDT', timeframe='5m', limit=20)
            df = pd.DataFrame(ohlcv, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
            ema = df['c'].ewm(span=10, adjust=False).mean().iloc[-1]
            price = df['c'].iloc[-1]
            
            return usdt, price, ema
        except Exception as e:
            st.error(f"خطأ في الاتصال: {e}")
            return 0, 0, 0

    def trade(self, side, amount):
        try:
            if side == 'buy':
                return self.exchange.create_market_buy_order('BTC/USDT', amount)
            else:
                return self.exchange.create_market_sell_order('BTC/USDT', amount)
        except Exception as e:
            st.error(f"فشل تنفيذ الصفقة: {e}")
            return None

# --- عرض الشاشة الرئيسية ---
st.title("🤖 بوت التداول الذكي - MEXC")

with st.sidebar:
    st.header("🔑 إعدادات API")
    api_key = st.text_input("API Key", type="password")
    secret_key = st.text_input("Secret Key", type="password")

if api_key and secret_key:
    bot = MEXCBot(api_key, secret_key)
    usdt, price, ema = bot.fetch_data()

    # عرض الرصيد والبيانات
    c1, c2, c3 = st.columns(3)
    c1.metric("رصيد USDT", f"${usdt:.2f}")
    c2.metric("سعر BTC الحالي", f"${price:.2f}")
    c3.metric("مؤشر EMA", f"${ema:.2f}")

    if 'active' not in st.session_state:
        st.session_state.active = False

    col_btn1, col_btn2 = st.columns(2)
    if col_btn1.button("🚀 تشغيل (12 ساعة)", type="primary", use_container_width=True):
        st.session_state.active = True
    
    if col_btn2.button("🛑 إيقاف فوري", use_container_width=True):
        st.session_state.active = False

    if st.session_state.active:
        st.info("✅ البوت يعمل الآن ويراقب السوق...")
        # تنفيذ صفقة حقيقية عند تحقق الشرط
        if price > ema and usdt > 10:
            qty = (usdt * 0.95) / price
            st.warning(f"📈 إشارة شراء! جاري تنفيذ صفقة بـ {qty:.5f} BTC")
            res = bot.trade('buy', qty)
            if res: st.success("✅ تمت عملية الشراء بنجاح!")
        
        elif price < ema:
            # هنا يمكنك إضافة منطق البيع إذا كان لديك رصيد BTC
            st.write("🔍 السعر تحت الـ EMA.. في انتظار فرصة.")
            
        time.sleep(10)
        st.rerun()
else:
    st.warning("يرجى إدخال المفاتيح في القائمة الجانبية للبدء.")
    
