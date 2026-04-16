import streamlit as st
import ccxt
import time
import pandas as pd

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="بوت MEXC الذكي", layout="wide")

# --- 2. كلاس البوت (المنطق البرمجي) ---
class SmartTradingBot:
    def __init__(self, api_key, secret_key):
        self.exchange = ccxt.mexc({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
        })
        self.is_running = False

    def get_balances(self):
        try:
            # جلب رصيد السبوت والفيوتشر
            spot = self.exchange.fetch_balance({'type': 'spot'})['total'].get('USDT', 0)
            swap = self.exchange.fetch_balance({'type': 'swap'})['total'].get('USDT', 0)
            return float(spot), float(swap)
        except Exception as e:
            return 0.0, 0.0

    def execute_trade(self, market_type, symbol, side, amount):
        try:
            params = {'type': 'swap'} if market_type == 'futures' else {'type': 'spot'}
            if side == 'buy':
                return self.exchange.create_market_buy_order(symbol, amount, params)
            else:
                return self.exchange.create_market_sell_order(symbol, amount, params)
        except Exception as e:
            return str(e)

# --- 3. واجهة المستخدم (تظهر على الشاشة الرئيسية) ---
st.title("🤖 مركز تحكم بوت MEXC الذكي")
st.markdown("---")

# لوحة إدخال المفاتيح
with st.expander("🔐 إعدادات الوصول (API Keys)", expanded=True):
    col_api, col_sec = st.columns(2)
    api_key = col_api.text_input("أدخل API Key", type="password")
    secret_key = col_sec.text_input("أدخل Secret Key", type="password")

if api_key and secret_key:
    bot = SmartTradingBot(api_key, secret_key)
    spot_bal, swap_bal = bot.get_balances()
    total_bal = spot_bal + swap_bal

    # عرض الرصيد في مربعات ملونة
    st.subheader("💰 ملخص المحفظة الحقيقي")
    c1, c2, c3 = st.columns(3)
    c1.metric("رصيد السبوت (Spot)", f"${spot_bal:.2f}")
    c2.metric("رصيد الفيوتشر (Futures)", f"${swap_bal:.2f}")
    c3.metric("إجمالي المحفظة", f"${total_bal:.2f}")

    st.markdown("---")

    # أزرار التحكم
    col_start, col_stop = st.columns(2)
    
    if 'running' not in st.session_state:
        st.session_state.running = False

    if col_start.button("🚀 ابدأ التداول الآلي (12 ساعة / هدف 10%)", type="primary", use_container_width=True):
        st.session_state.running = True

    if col_stop.button("🛑 إيقاف فوري وإغلاق الجلسة", use_container_width=True):
        st.session_state.running = False
        st.warning("تم إيقاف البوت.")

    # منطقة العمليات المباشرة (Logs)
    if st.session_state.running:
        st.info("🔄 البوت يعمل الآن في الخلفية ويحلل السوق...")
        log_area = st.container()
        
        initial_total = total_bal
        target_profit = initial_total * 1.10
        
        # حلقة التداول
        while st.session_state.running:
            spot, swap = bot.get_balances()
            current_total = spot + swap
            
            with log_area:
                st.write(f"🔍 فحص السوق... الرصيد الحالي: ${current_total:.2f}")
                
                # فحص الهدف
                if current_total >= target_profit:
                    st.success(f"✅ تم تحقيق الهدف! الرصيد: ${current_total:.2f}")
                    st.session_state.running = False
                    break
                
                # تحليل سريع (مثال للبيتكوين)
                try:
                    bars = bot.exchange.fetch_ohlcv('BTC/USDT', timeframe='5m', limit=10)
                    price = bars[-1][4]
                    st.write(f"📊 سعر البيتكوين الحالي: ${price}")
                except:
                    pass

            time.sleep(30) # فحص كل 30 ثانية
            st.rerun() # تحديث الشاشة
else:
    st.warning("⚠️ يرجى إدخال مفاتيح الـ API في الأعلى لتفعيل لوحة التحكم.")

