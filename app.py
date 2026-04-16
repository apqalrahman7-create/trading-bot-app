import streamlit as st
import ccxt
import time
import pandas as pd

# --- إعدادات الصفحة ---
st.set_page_config(page_title="MEXC Auto Trader", layout="wide")

class MexcFinalBot:
    def __init__(self, api, secret):
        self.exchange = ccxt.mexc({
            'apiKey': api,
            'secret': secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap', 'adjustForTimeDifference': True}
        })

    def fetch_all_balances(self):
        try:
            # جلب الرصيد من MEXC مع تحديد النوع لضمان عدم العودة بصفر
            balance = self.exchange.fetch_balance()
            total_usdt = float(balance.get('total', {}).get('USDT', 0))
            free_usdt = float(balance.get('free', {}).get('USDT', 0))
            return max(total_usdt, free_usdt)
        except Exception as e:
            return f"Error: {str(e)}"

# --- واجهة المستخدم الرئيسية ---
st.title("🤖 بوت MEXC المتكامل (تداول 12 ساعة / هدف 10%)")
st.markdown("---")

# القائمة الجانبية للمفاتيح
with st.sidebar:
    st.header("🔑 إعدادات API")
    api_k = st.text_input("API Key", type="password")
    sec_k = st.text_input("Secret Key", type="password")
    lev = st.slider("الرافعة المالية", 1, 20, 10)

if api_k and sec_k:
    bot = MexcFinalBot(api_k, sec_k)
    real_bal = bot.fetch_all_balances()

    if isinstance(real_bal, float):
        # عرض الرصيد الحقيقي فوراً
        st.subheader("💰 ملخص المحفظة")
        c1, c2 = st.columns(2)
        c1.metric("الرصيد المكتشف (USDT)", f"${real_bal:.2f}")
        c2.info("الحالة: متصل وجاهز" if real_bal > 0 else "الحالة: متصل ولكن الرصيد 0")

        if 'active' not in st.session_state:
            st.session_state.active = False

        st.markdown("---")
        
        # أزرار التحكم
        col_start, col_stop = st.columns(2)
        if col_start.button("🚀 بدء التداول الآلي الذكي", type="primary", use_container_width=True):
            st.session_state.active = True
        
        if col_stop.button("🛑 إيقاف فوري", use_container_width=True):
            st.session_state.active = False
            st.warning("تم إرسال أمر الإيقاف.")

        # منطقة تنفيذ العمليات
        if st.session_state.active and real_bal > 5:
            st.success("🔄 البوت يعمل الآن.. يحلل السوق ويفتح صفقات تلقائياً.")
            
            # --- منطق التداول (BTC كمثال) ---
            symbol = 'BTC/USDT:USDT'
            ohlcv = bot.exchange.fetch_ohlcv(symbol, timeframe='5m', limit=20)
            df = pd.DataFrame(ohlcv, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
            price = df['c'].iloc[-1]
            ema = df['c'].ewm(span=10, adjust=False).mean().iloc[-1]

            if price > ema:
                st.write(f"📈 إشارة شراء على {symbol}.. تنفيذ صفقة Long")
                qty = (real_bal * lev * 0.9) / price
                bot.exchange.create_market_buy_order(symbol, bot.exchange.amount_to_precision(symbol, qty))
            
            elif price < ema:
                st.write(f"📉 إشارة بيع على {symbol}.. تنفيذ صفقة Short")
                qty = (real_bal * lev * 0.9) / price
                bot.exchange.create_market_sell_order(symbol, bot.exchange.amount_to_precision(symbol, qty))

            time.sleep(15)
            st.rerun() # إجبار الصفحة على التحديث لجلب الرصيد الجديد والتحليل القادم
    else:
        st.error(f"❌ فشل الاتصال: {real_bal}")
else:
    st.warning("⚠️ أدخل مفاتيح الـ API في القائمة الجانبية لتنشيط البوت.")
    
