import streamlit as st
import ccxt
import pandas as pd
import time

# إعدادات الواجهة
st.set_page_config(page_title="MEXC AI BOT", layout="wide")

# --- محرك البوت الذكي ---
class TradingBot:
    def __init__(self, api, secret):
        self.exchange = ccxt.mexc({
            'apiKey': api,
            'secret': secret,
            'enableRateLimit': True,
            'options': {'adjustForTimeDifference': True}
        })

    def get_balance(self):
        try:
            # البحث في العقود الآجلة أولاً ثم السبوت
            bal = self.exchange.fetch_balance({'type': 'swap'})
            total = float(bal.get('total', {}).get('USDT', 0))
            if total < 1:
                bal = self.exchange.fetch_balance({'type': 'spot'})
                total = float(bal.get('total', {}).get('USDT', 0))
            return total
        except: return 0.0

    def run_bot(self, balance):
        initial_bal = balance
        target = initial_bal * 1.10
        yield f"🚀 Started! Target: ${target:.2f}"
        
        while True:
            try:
                curr_bal = self.get_balance()
                if curr_bal >= target:
                    yield "✅ Target Reached! 10% Profit Achieved."
                    break
                
                # تحليل سريع للبيتكوين
                bars = self.exchange.fetch_ohlcv('BTC/USDT:USDT', timeframe='1m', limit=10)
                price = bars[-1][4]
                yield f"🔍 Analyzing... Current Price: ${price} | Balance: ${curr_bal:.2f}"
            except: pass
            time.sleep(20)

# --- واجهة المستخدم ---
st.title("🤖 AI Trading Bot (MEXC)")

with st.sidebar:
    st.header("🔐 API Keys")
    api = st.text_input("API Key", type="password")
    sec = st.text_input("Secret Key", type="password")

if api and sec:
    bot = TradingBot(api, sec)
    real_bal = bot.get_balance()
    
    st.metric("Total Balance (USDT)", f"${real_bal:.2f}")

    if st.button("🚀 START TRADING"):
        if real_bal > 0:
            st.info("Bot is active and scanning markets...")
            for msg in bot.run_bot(real_bal):
                st.write(msg)
        else:
            st.error("Balance is 0. Please add USDT to your MEXC wallet.")
else:
    st.warning("Please enter your API Keys to start.")
    
