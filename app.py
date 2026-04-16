import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime, timedelta

# --- إعدادات الصفحة ---
st.set_page_config(page_title="بوت الـ 12 ساعة المطور", layout="wide")

class FinalMexcBot:
    def __init__(self, api, secret):
        self.exchange = ccxt.mexc({
            'apiKey': api,
            'secret': secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'} # التركيز على العقود الآجلة
        })

    def get_wallet_balance(self):
        try:
            # محاولة جلب الرصيد بأكثر من طريقة لضمان ظهوره
            bal = self.exchange.fetch_balance()
            total = float(bal.get('total', {}).get('USDT', 0))
            free = float(bal.get('free', {}).get('USDT', 0))
            return max(total, free)
        except: return 0.0

    def get_market_data(self, symbol):
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe='1m', limit=30)
            df = pd.DataFrame(ohlcv, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
            ema = df['c'].ewm(span=10, adjust=False).mean().iloc[-1]
            return df['c'].iloc[-1], ema
        except: return 0, 0

    def open_trade(self, symbol, side, usdt_amount, leverage):
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            price = ticker['last']
            # حساب الكمية مع دقة MEXC الصارمة
            raw_qty = (usdt_amount * leverage * 0.90) / price
            precise_qty = self.exchange.amount_to_precision(symbol, raw_qty)
            
            if side == 'buy':
                return self.exchange.create_market_buy_order(symbol, precise_qty)
            else:
                return self.exchange.create_market_sell_order(symbol, precise_qty)
        except Exception as e:
            return str(e)

# --- الواجهة ---
st.title("🛡️ بوت الـ 12 ساعة (نسخة الإصلاح النهائي)")

with st.sidebar:
    api_key = st.text_input("API Key", type="password")
    secret_key = st.text_input("Secret Key", type="password")
    lev = st.slider("الرافعة المالية", 1, 20, 10)

if api_key and secret_key:
    bot = FinalMexcBot(api_key, secret_key)
    
    # ضمان جلب الرصيد وتخزينه
    actual_balance = bot.get_wallet_balance()
    
    if 'start_time' not in st.session_state: st.session_state.start_time = None
    if 'initial_bal' not in st.session_state or st.session_state.initial_bal == 0:
        st.session_state.initial_bal = actual_balance

    # عرض الإحصائيات
    c1, c2, c3 = st.columns(3)
    c1.metric("رصيد البداية", f"${st.session_state.initial_bal:.2f}")
    c2.metric("الرصيد الحقيقي الآن", f"${actual_balance:.2f}")
    
    if st.session_state.start_time:
        rem = (st.session_state.start_time + timedelta(hours=12)) - datetime.now()
        c3.metric("الوقت المتبقي", str(rem).split('.')[0])
    else:
        c3.metric("الوقت المتبقي", "12:00:00")

    if st.button("🚀 إطلاق الدورة المصلحة", type="primary", use_container_width=True):
        st.session_state.start_time = datetime.now()
        st.session_state.active = True

    if st.session_state.get('active') and actual_balance > 0:
        symbol = 'BTC/USDT:USDT'
        price, ema = bot.get_market_data(symbol)
        
        # فحص وجود صفقات مفتوحة
        pos = bot.exchange.fetch_positions([symbol])
        has_pos = any(float(p['contracts']) != 0 for p in pos)

        if not has_pos:
            if price > ema:
                st.info("📈 جاري فتح صفقة Long مصلحة...")
                res = bot.open_trade(symbol, 'buy', actual_balance, lev)
                st.write(res)
            elif price < ema:
                st.info("📉 جاري فتح صفقة Short مصلحة...")
                res = bot.open_trade(symbol, 'sell', actual_balance, lev)
                st.write(res)
        
        time.sleep(15)
        st.rerun()
    elif actual_balance == 0:
        st.warning("⚠️ الرصيد يظهر صفر. تأكد من وجود USDT في محفظة العقود الآجلة (Futures) في MEXC.")
        
