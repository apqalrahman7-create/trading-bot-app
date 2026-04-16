import streamlit as st
import ccxt
import pandas as pd
import time

# --- إعدادات الواجهة ---
st.set_page_config(page_title="الذكاء الاصطناعي للتداول - MEXC", layout="wide")

class ProfessionalBot:
    def __init__(self, api, secret):
        self.exchange = ccxt.mexc({
            'apiKey': api, 'secret': secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'} # العقود الآجلة
        })

    def analyze_market(self, symbol):
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe='5m', limit=50)
            df = pd.DataFrame(ohlcv, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
            # مؤشر المتوسط المتحرك
            df['ema'] = df['c'].ewm(span=10, adjust=False).mean()
            # مؤشر القوة النسبية RSI (للذكاء في الدخول)
            delta = df['c'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            return df.iloc[-1]
        except: return None

    def get_balance(self):
        try:
            bal = self.exchange.fetch_balance()
            return float(bal['total'].get('USDT', 0))
        except: return 0

# --- الشاشة الرئيسية ---
st.title("🧠 بوت التداول الذكي (إدارة رأس مال + تحليل متعدد)")

with st.sidebar:
    st.header("⚙️ الإعدادات الذكية")
    api_key = st.text_input("API Key", type="password")
    secret_key = st.text_input("Secret Key", type="password")
    risk_per_trade = st.slider("نسبة المخاطرة لكل صفقة %", 1, 20, 5)
    leverage = st.number_input("الرافعة المالية", 1, 50, 10)

if api_key and secret_key:
    bot = ProfessionalBot(api_key, secret_key)
    usdt = bot.get_balance()
    
    st.metric("إجمالي رأس المال المتاح", f"${usdt:.2f}")
    
    symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']
    
    if 'running' not in st.session_state: st.session_state.running = False

    if st.button("🚀 تشغيل النظام الذكي", type="primary", use_container_width=True):
        st.session_state.running = True

    if st.session_state.running:
        st.info("🔎 جاري مسح الأسواق وتقسيم رأس المال ذكياً...")
        
        for symbol in symbols:
            data = bot.analyze_market(symbol)
            if data is not None:
                price = data['c']
                ema = data['ema']
                rsi = data['rsi']
                
                # --- منطق الدخول الذكي ---
                # دخول Long: السعر فوق EMA و RSI ليس في منطقة تشبع شراء (< 70)
                if price > ema and rsi < 70:
                    trade_budget = (usdt * (risk_per_trade/100)) # تقسيم رأس المال
                    qty = (trade_budget * leverage) / price
                    st.success(f"✅ فرصة ذكية في {symbol}: شراء (Long) بـ ${trade_budget:.2f}")
                    bot.exchange.create_market_buy_order(symbol, qty)
                
                # دخول Short: السعر تحت EMA و RSI ليس في منطقة تشبع بيع (> 30)
                elif price < ema and rsi > 30:
                    trade_budget = (usdt * (risk_per_trade/100))
                    qty = (trade_budget * leverage) / price
                    st.warning(f"📉 فرصة ذكية في {symbol}: بيع (Short) بـ ${trade_budget:.2f}")
                    bot.exchange.create_market_sell_order(symbol, qty)
                
                else:
                    st.write(f"⏳ {symbol}: في حالة انتظار (لا توجد فرصة آمنة حالياً)")

        time.sleep(20)
        st.rerun()
else:
    st.warning("يرجى إدخال مفاتيح الـ API للبدء.")
    
