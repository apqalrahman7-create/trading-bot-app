import streamlit as st
import ccxt
import time
import pandas as pd
from datetime import datetime, timedelta

# --- إعدادات الصفحة ---
st.set_page_config(page_title="بوت الـ 12 ساعة الذكي", layout="wide")

class TradingBot:
    def __init__(self, api_key, secret_key, exchange_id):
        self.exchange = getattr(ccxt, exchange_id)({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'} # تفعيل العقود الآجلة تلقائياً
        })
        self.is_running = False

    def get_real_balance(self):
        try:
            balance = self.exchange.fetch_balance()
            return float(balance['total'].get('USDT', 0))
        except: return 0.0

    def close_all_positions(self, symbols):
        """إغلاق كافة الصفقات وإعادة الرصيد للأصول"""
        for symbol in symbols:
            try:
                positions = self.exchange.fetch_positions([symbol])
                for pos in positions:
                    size = float(pos['contracts'])
                    if size != 0:
                        side = 'sell' if size > 0 else 'buy'
                        self.exchange.create_order(symbol, 'market', side, abs(size), params={'reduceOnly': True})
            except: pass

    def run_session(self):
        self.is_running = True
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=12)
        initial_balance = self.get_real_balance()
        target_balance = initial_balance * 1.10 # هدف 10% ربح
        
        symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']
        
        # حاويات العرض المباشر
        metrics_placeholder = st.empty()
        log_placeholder = st.empty()

        while self.is_running:
            current_balance = self.get_real_balance()
            elapsed_time = datetime.now() - start_time
            remaining_time = end_time - datetime.now()
            profit_loss = current_balance - initial_balance

            # 1. تحديث الشاشة بالرصيد الحقيقي والأرباح
            with metrics_placeholder.container():
                c1, c2, c3 = st.columns(3)
                c1.metric("الرصيد الحقيقي المباشر", f"${current_balance:.2f}")
                c2.metric("صافي الربح (تارجت 10%)", f"${profit_loss:.2f}", f"{(profit_loss/initial_balance)*100:.2f}%")
                c3.metric("الوقت المتبقي", str(remaining_time).split('.')[0])

            # 2. فحص شروط الإغلاق (الربح أو الوقت)
            if current_balance >= target_balance:
                st.balloons()
                yield "💰 تم تحقيق هدف الـ 10%! جاري تصفية الصفقات وإعادة الأصول..."
                self.close_all_positions(symbols)
                break
            
            if datetime.now() >= end_time:
                yield "⏱️ انتهت الـ 12 ساعة. جاري إغلاق الجلسة وتأمين الرصيد..."
                self.close_all_positions(symbols)
                break

            # 3. منطق التداول التلقائي (الخلفية)
            for symbol in symbols:
                try:
                    bars = self.exchange.fetch_ohlcv(symbol, timeframe='5m', limit=20)
                    df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
                    ema = df['c'].ewm(span=10, adjust=False).mean().iloc[-1]
                    price = df['c'].iloc[-1]

                    # تنفيذ صفقات بكامل المحفظة (مع إدارة مخاطرة بسيطة)
                    order_size = (current_balance * 0.1) / price # دخول بـ 10% من المحفظة لكل صفقة
                    
                    if price > ema:
                        yield f"📈 إشارة صعود {symbol}.. تنفيذ Long"
                        self.exchange.create_market_buy_order(symbol, order_size)
                    elif price < ema:
                        yield f"📉 إشارة هبوط {symbol}.. تنفيذ Short"
                        self.exchange.create_market_sell_order(symbol, order_size)
                except Exception as e:
                    yield f"⚠️ تنبيه {symbol}: {str(e)}"
                
            time.sleep(30) # فحص كل 30 ثانية

# --- الواجهة الرسومية ---
st.title("🛡️ بوت التداول الآلي (دورة 12 ساعة / هدف 10%)")

with st.expander("🔐 إعدادات الوصول للمحفظة", expanded=True):
    col_a, col_b, col_c = st.columns(3)
    api = col_a.text_input("API Key", type="password")
    sec = col_b.text_input("Secret Key", type="password")
    ex = col_c.selectbox("المنصة", ["binance", "bybit"])

if api and sec:
    bot = TradingBot(api, sec, ex)
    
    if st.button("🚀 ابدأ دورة التداول (12 ساعة)", type="primary", use_container_width=True):
        st.session_state.running = True
        for msg in bot.run_session():
            st.write(msg)
    
    if st.button("🛑 إيقاف طارئ وإغلاق الصفقات", use_container_width=True):
        bot.is_running = False
        bot.close_all_positions(['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT'])
        st.error("تم إيقاف البوت وتصفية المحفظة فوراً.")
else:
    st.warning("يرجى إدخال مفاتيح الـ API للاتصال بمحفظتك.")
    
