import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="بوت الـ 12 ساعة التراكمي", layout="wide")

class FinalTurboBot:
    def __init__(self, api, secret):
        self.exchange = ccxt.mexc({
            'apiKey': api, 'secret': secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })

    def get_market_data(self, symbol):
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe='1m', limit=30)
            df = pd.DataFrame(ohlcv, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
            ema = df['c'].ewm(span=10, adjust=False).mean().iloc[-1]
            return df['c'].iloc[-1], ema
        except: return 0, 0

    def close_all(self, symbol):
        try:
            pos = self.exchange.fetch_positions([symbol])
            for p in pos:
                size = float(p['contracts'])
                if size != 0:
                    side = 'sell' if size > 0 else 'buy'
                    self.exchange.create_order(symbol, 'market', side, abs(size), params={'reduceOnly': True})
            return True
        except: return False

# --- الواجهة ---
st.title("🛡️ بوت تداول MEXC (دورة 12 ساعة)")

with st.sidebar:
    api_k = st.text_input("API Key", type="password")
    sec_k = st.text_input("Secret Key", type="password")
    lev = st.slider("الرافعة المالية", 1, 25, 10)

if api_k and sec_k:
    bot = FinalTurboBot(api_k, sec_k)
    
    # تهيئة متغيرات الجلسة
    if 'start_time' not in st.session_state: st.session_state.start_time = None
    if 'initial_bal' not in st.session_state: st.session_state.initial_bal = bot.exchange.fetch_balance()['total'].get('USDT', 0)

    # عرض لوحة الإحصائيات
    cur_bal = bot.exchange.fetch_balance()['total'].get('USDT', 0)
    target = st.session_state.initial_bal * 1.10
    
    c1, c2, c3 = st.columns(3)
    c1.metric("رصيد البداية", f"${st.session_state.initial_bal:.2f}")
    c2.metric("الرصيد المباشر", f"${cur_bal:.2f}", f"{((cur_bal/st.session_state.initial_bal)-1)*100:.2f}%")
    
    if st.session_state.start_time:
        remaining = (st.session_state.start_time + timedelta(hours=12)) - datetime.now()
        c3.metric("الوقت المتبقي", str(remaining).split('.')[0])
    else:
        c3.metric("الوقت المتبقي", "12:00:00")

    if st.button("🚀 إطلاق دورة الـ 12 ساعة", type="primary", use_container_width=True):
        st.session_state.start_time = datetime.now()
        st.session_state.active = True

    if st.session_state.get('active'):
        # 1. فحص انتهاء الوقت
        if datetime.now() >= st.session_state.start_time + timedelta(hours=12):
            st.error("⚠️ انتهت الـ 12 ساعة! إغلاق كافة المراكز وتأمين الرصيد.")
            bot.close_all('BTC/USDT:USDT')
            st.session_state.active = False
            st.stop()

        # 2. فحص تحقيق الهدف (10%)
        if cur_bal >= target:
            st.success("💰 مبروك! تم جني 10% أرباح تراكمية. إغلاق الجلسة.")
            bot.close_all('BTC/USDT:USDT')
            st.session_state.active = False
            st.stop()

        # 3. منطق التداول التكراري
        symbol = 'BTC/USDT:USDT'
        price, ema = bot.get_market_data(symbol)
        pos = bot.exchange.fetch_positions([symbol])
        has_pos = any(float(p['contracts']) != 0 for p in pos)

        if not has_pos:
            qty = (cur_bal * lev * 0.9) / price
            if price > ema:
                st.info("📈 فتح صفقة Long جديدة...")
                bot.exchange.create_market_buy_order(symbol, bot.exchange.amount_to_precision(symbol, qty))
            elif price < ema:
                st.info("📉 فتح صفقة Short جديدة...")
                bot.exchange.create_market_sell_order(symbol, bot.exchange.amount_to_precision(symbol, qty))
        else:
            # مراقبة الصفقة الحالية للإغلاق عند عكس الإشارة
            p = [x for x in pos if float(x['contracts']) != 0][0]
            if (p['side'] == 'long' and price < ema) or (p['side'] == 'short' and price > ema):
                st.warning("🔄 عكس الاتجاه.. إغلاق الصفقة فوراً لجني الربح المتوفر.")
                bot.close_all(symbol)

        time.sleep(20)
        st.rerun()
        
