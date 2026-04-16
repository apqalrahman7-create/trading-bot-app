import streamlit as st
import ccxt
import time
import pandas as pd

# --- 1. كلاس البوت (المنطق البرمجي) ---
class TradingBot:
    def __init__(self, api_key, secret_key):
        self.exchange = ccxt.binance({  # يمكنك تغيير binance لـ bybit أو غيرها
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'} # للعقود الآجلة
        })
        self.is_running = False

    def get_balance(self):
        try:
            balance = self.exchange.fetch_balance()
            return float(balance['total'].get('USDT', 0))
        except: return 0.0

    def close_all_positions(self, symbols):
        for symbol in symbols:
            try:
                positions = self.exchange.fetch_positions([symbol])
                for pos in positions:
                    size = float(pos['contracts'])
                    if size != 0:
                        side = 'sell' if size > 0 else 'buy'
                        self.exchange.create_order(symbol, 'market', side, abs(size), params={'reduceOnly': True})
            except: pass

    def run_logic(self):
        self.is_running = True
        initial_balance = self.get_balance()
        target_profit = initial_balance * 1.10
        symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT']
        
        yield f"🚀 بدأت الجلسة | الرصيد: ${initial_balance:.2f} | الهدف: ${target_profit:.2f}"

        while self.is_running:
            current_balance = self.get_balance()
            if current_balance >= target_profit:
                yield "✅ تم تحقيق ربح 10%! جاري إغلاق الصفقات..."
                self.close_all_positions(symbols)
                self.is_running = False
                break

            for symbol in symbols:
                try:
                    bars = self.exchange.fetch_ohlcv(symbol, timeframe='5m', limit=20)
                    df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
                    ema = df['c'].ewm(span=10, adjust=False).mean().iloc[-1]
                    price = df['c'].iloc[-1]

                    if price > ema:
                        yield f"📈 شراء {symbol} عند {price}"
                        self.exchange.create_market_buy_order(symbol, 0.001) # تأكد من حجم اللوت
                    elif price < ema:
                        yield f"📉 بيع {symbol} عند {price}"
                        self.exchange.create_market_sell_order(symbol, 0.001)
                except Exception as e:
                    yield f"⚠️ خطأ: {str(e)}"
                time.sleep(2)
            time.sleep(10)

# --- 2. واجهة المستخدم (Streamlit UI) ---
st.set_page_config(page_title="بوت التداول الآلي", page_icon="🤖")

st.title("🤖 نظام التداول الذكي")

# جلب المفاتيح من Secrets
try:
    API_KEY = st.secrets["api_key"]
    SECRET_KEY = st.secrets["secret_key"]
    bot = TradingBot(API_KEY, SECRET_KEY)
except:
    st.error("يرجى ضبط API Key في إعدادات Secrets!")
    st.stop()

# عرض الرصيد العلوي
balance = bot.get_balance()
st.metric("رصيد المحفظة (USDT)", f"{balance:.2f} $")

# حالة البوت
if 'running' not in st.session_state:
    st.session_state.running = False

col1, col2 = st.columns(2)

with col1:
    if st.button("▶️ تشغيل البوت", type="primary", use_container_width=True):
        st.session_state.running = True

with col2:
    if st.button("🛑 إيقاف وجني الأرباح", type="secondary", use_container_width=True):
        st.session_state.running = False
        bot.is_running = False
        st.warning("جاري إغلاق كل شيء...")

# تشغيل البوت وعرض النتائج
if st.session_state.running:
    st.info("البوت نشط الآن...")
    log_area = st.empty()
    for message in bot.run_logic():
        with log_area.container():
            st.write(message)
        if not st.session_state.running:
            break
else:
    st.write("البوت في وضع الاستعداد.")
    
