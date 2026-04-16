import streamlit as st
import ccxt
import pandas as pd
import time

# --- إعدادات الصفحة ---
st.set_page_config(page_title="MEXC AI Trader", layout="wide")

class MEXCProBot:
    def __init__(self, api, secret):
        self.exchange = ccxt.mexc({
            'apiKey': api,
            'secret': secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'} # تداول العقود الآجلة
        })

    def get_market_data(self, symbol):
        try:
            # جلب البيانات والتحليل
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe='5m', limit=30)
            df = pd.DataFrame(ohlcv, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
            df['ema'] = df['c'].ewm(span=10, adjust=False).mean()
            # حساب RSI بسيط
            delta = df['c'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            df['rsi'] = 100 - (100 / (1 + (gain / loss)))
            return df.iloc[-1]
        except: return None

    def get_balance(self):
        try:
            bal = self.exchange.fetch_balance()
            return float(bal['total'].get('USDT', 0))
        except: return 0.0

    def safe_trade(self, symbol, side, usdt_amount, leverage):
        try:
            # جلب السعر الحالي ودقة العملة لمنع خطأ InvalidOrder
            ticker = self.exchange.fetch_ticker(symbol)
            price = ticker['last']
            
            # حساب الكمية مع خصم بسيط للرسوم (90%)
            raw_qty = (usdt_amount * leverage * 0.90) / price
            
            # تصحيح الكمية حسب قوانين MEXC
            precise_qty = float(self.exchange.amount_to_precision(symbol, raw_qty))
            
            if side == 'buy':
                return self.exchange.create_market_buy_order(symbol, precise_qty)
            else:
                return self.exchange.create_market_sell_order(symbol, precise_qty)
        except Exception as e:
            return f"Error: {str(e)}"

# --- الواجهة الرئيسية ---
st.title("🧠 نظام MEXC للتداول الذكي (عقود آجلة)")

with st.sidebar:
    st.header("🔐 إعدادات الحساب")
    api_k = st.text_input("API Key", type="password")
    sec_k = st.text_input("Secret Key", type="password")
    st.divider()
    risk = st.slider("المخاطرة لكل صفقة %", 5, 50, 10)
    lev = st.number_input("الرافعة المالية", 1, 50, 5)

if api_k and sec_k:
    bot = MEXCProBot(api_k, sec_k)
    current_bal = bot.get_balance()
    
    # عرض الرصيد بشكل واضح لمنع خطأ ZeroDivision
    st.metric("الرصيد المتاح (USDT)", f"${current_bal:.2f}")

    if 'running' not in st.session_state: st.session_state.running = False

    col1, col2 = st.columns(2)
    if col1.button("🚀 تشغيل البوت الذكي", use_container_width=True, type="primary"):
        st.session_state.running = True
    if col2.button("🛑 إيقاف فوري", use_container_width=True):
        st.session_state.running = False

    if st.session_state.running and current_bal > 5:
        st.info("🔄 النظام يحلل السوق ويوزع رأس المال حالياً...")
        
        symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT']
        for sym in symbols:
            data = bot.get_market_data(sym)
            if data is not None:
                price, ema, rsi = data['c'], data['ema'], data['rsi']
                
                # منطق الدخول الذكي
                if price > ema and rsi < 70:
                    st.write(f"📈 فرصة Long في {sym}")
                    res = bot.safe_trade(sym, 'buy', (current_bal * risk/100), lev)
                    st.success(f"تم التنفيذ: {res}")
                
                elif price < ema and rsi > 30:
                    st.write(f"📉 فرصة Short في {sym}")
                    res = bot.safe_trade(sym, 'sell', (current_bal * risk/100), lev)
                    st.warning(f"تم التنفيذ: {res}")
        
        time.sleep(20)
        st.rerun()
    elif current_bal <= 5 and st.session_state.running:
        st.error("⚠️ الرصيد منخفض جداً للتداول (يجب أن يكون أكثر من 5$)")
else:
    st.warning("يرجى إدخال مفاتيح الـ API للبدء.")
    
