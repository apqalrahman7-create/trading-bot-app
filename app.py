import streamlit as st
import threading
import time
import ccxt

st.set_page_config(page_title="MEXC AI Sniper", layout="centered")
st.title("⚡ AI Sniper - Instant Execution")

# مساحة لتحديث البيانات حياً
status_placeholder = st.empty()
info_placeholder = st.empty()

if 'bot_active' not in st.session_state:
    st.session_state.bot_active = False

def trading_engine(api_key, api_secret):
    exchange = ccxt.mexc({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })

    while st.session_state.bot_active:
        try:
            balance = exchange.fetch_balance()
            free_usdt = balance['free'].get('USDT', 0)
            
            if free_usdt < 10: 
                status_placeholder.warning("⚠️ رصيد USDT غير كافٍ (أقل من 10)")
                time.sleep(30)
                continue

            tickers = exchange.fetch_tickers()
            valid_pairs = {k: v for k, v in tickers.items() if '/USDT' in k and v['percentage'] is not None}
            sorted_pairs = sorted(valid_pairs.items(), key=lambda x: x[1]['percentage'], reverse=True)

            if sorted_pairs:
                target_symbol = sorted_pairs[0][0]
                price = sorted_pairs[0][1]['last']
                
                # حساب الكمية بدقة
                raw_amount = (free_usdt * 0.95) / price 
                amount = exchange.amount_to_precision(target_symbol, raw_amount)
                
                status_placeholder.info(f"🎯 محاولة شراء: {target_symbol}")
                exchange.create_market_buy_order(target_symbol, amount)
                entry_price = price
                
                # حلقة المراقبة
                while st.session_state.bot_active:
                    ticker = exchange.fetch_ticker(target_symbol)
                    curr_price = ticker['last']
                    profit = ((curr_price - entry_price) / entry_price) * 100
                    
                    info_placeholder.metric(label=f"Trading {target_symbol}", value=f"{profit:.2f}%", delta=f"{curr_price}")
                    
                    if profit >= 5.0 or profit <= -1.5: # أهداف واقعية أكثر
                        # جلب الرصيد المتاح من العملة للبيع بالكامل
                        sell_balance = exchange.fetch_balance()['free'].get(target_symbol.split('/')[0], 0)
                        exchange.create_market_sell_order(target_symbol, exchange.amount_to_precision(target_symbol, sell_balance))
                        status_placeholder.success(f"✅ تم الإغلاق بربح: {profit:.2f}%")
                        break
                    time.sleep(2)

            time.sleep(5)
        except Exception as e:
            status_placeholder.error(f"Error: {e}")
            time.sleep(10)

# --- UI ---
with st.sidebar:
    k = st.text_input("MEXC API Key", type="password")
    s = st.text_input("MEXC Secret Key", type="password")

col1, col2 = st.columns(2)
with col1:
    if st.button("🚀 تشغيل", use_container_width=True):
        if k and s:
            st.session_state.bot_active = True
            threading.Thread(target=trading_engine, args=(k, s), daemon=True).start()
with col2:
    if st.button("🛑 إيقاف", use_container_width=True):
        st.session_state.bot_active = False
        
