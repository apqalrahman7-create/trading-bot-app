import streamlit as st
import ccxt
import pandas as pd
import time

# --- ⚙️ إعدادات الربح التراكمي (Compounding) ---
SYMBOLS = ['ORDI_USDT', 'BTC_USDT', 'ETH_USDT', 'SOL_USDT', 'SUI_USDT']
MAX_TRADES = 4
LEVERAGE = 5
# تخصيص 20% من الرصيد المتاح لكل صفقة (100% / 5 صفقات = 20%)
RISK_PER_TRADE = 0.20 
TP_PERCENT = 0.012  # جني الربح عند 1.2%
SL_PERCENT = 0.010  # وقف الخسارة عند 1%

st.title("💰 قناص الربح التراكمي - MEXC Force")

if 'running' not in st.session_state: st.session_state.running = False

with st.sidebar:
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 تشغيل محرك الأرباح"): st.session_state.running = True
    if st.button("🛑 إيقاف"): st.session_state.running = False

if st.session_state.running and api_key and api_secret:
    try:
        mexc = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'options': {'defaultType': 'future'}})
        
        while st.session_state.running:
            # 1. جلب الرصيد المتاح "حالياً" (لحساب الربح التراكمي)
            balance_data = mexc.fetch_balance()
            available_balance = float(balance_data['info']['data']['availableBalance'])
            
            # 2. فحص الصفقات النشطة
            pos = mexc.fetch_positions()
            active_list = [p['symbol'] for p in pos if float(p.get('contracts', 0)) != 0]
            current_count = len(active_list)
            
            st.info(f"💵 الرصيد المتاح للتدوير: {available_balance:.2f} USDT | الصفقات: {current_count}/{MAX_TRADES}")

            # 3. محرك القنص
            for symbol in SYMBOLS:
                if current_count >= MAX_TRADES: break
                
                if symbol not in active_list:
                    try:
                        ticker = mexc.fetch_ticker(symbol)
                        price = float(ticker['last'])
                        
                        # --- الحسبة التراكمية ---
                        # الدخول بـ 20% من رصيدك الحالي
                        entry_usd = available_balance * RISK_PER_TRADE
                        qty = (entry_usd * LEVERAGE) / price
                        fmt_qty = float(mexc.amount_to_precision(symbol, qty))

                        if fmt_qty > 0:
                            # تنفيذ الدخول
                            mexc.create_market_buy_order(symbol, fmt_qty)
                            
                            # وضع أهداف القنص الفوري في المنصة
                            tp_p = price * (1 + TP_PERCENT)
                            sl_p = price * (1 - SL_PERCENT)
                            mexc.create_order(symbol, 'LIMIT', 'sell', fmt_qty, tp_p, {'reduceOnly': True})
                            
                            st.success(f"🔥 صفقة تراكمية: {symbol} بمبلغ {entry_usd:.2f}$")
                            current_count += 1
                            active_list.append(symbol)
                    except: continue

            time.sleep(15) # فحص دوري سريع
    except Exception as e:
        st.error(f"⚠️ تنبيه: {e}")
        time.sleep(20)
        
