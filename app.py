import streamlit as st
import threading
import time
import ccxt

st.set_page_config(page_title="MEXC Force Sniper", layout="centered")
st.title("🛡️ MEXC Active Sniper (Force Execute)")

if 'bot_active' not in st.session_state:
    st.session_state.bot_active = False

def trading_engine(api_key, api_secret):
    # إعداد الاتصال مع تجاوز القيود الجغرافية
    exchange = ccxt.mexc({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })

    while st.session_state.get('bot_active', False):
        try:
            # 1. فحص الرصيد الحقيقي
            balance = exchange.fetch_balance()
            free_usdt = balance['free'].get('USDT', 0)
            
            if free_usdt < 10:
                st.sidebar.error(f"رصيد USDT غير كافٍ: {free_usdt}")
                time.sleep(30)
                continue

            # 2. البحث السريع جداً عن أي حركة
            tickers = exchange.fetch_tickers()
            # نبحث عن أكثر العملات نشاطاً الآن
            for symbol, ticker in tickers.items():
                if '/USDT' in symbol and ticker['percentage'] > 0.1:
                    # تنفيذ شراء فوري
                    price = ticker['last']
                    amount = (free_usdt * 0.95) / price # استخدام 95% من الرصيد
                    
                    st.toast(f"🎯 محاولة شراء {symbol}...")
                    order = exchange.create_market_buy_order(symbol, amount)
                    
                    # 3. مراقبة الـ 12 ساعة لتحقيق الـ 10%
                    start_price = price
                    while True:
                        curr_ticker = exchange.fetch_ticker(symbol)
                        curr_profit = ((curr_ticker['last'] - start_price) / start_price) * 100
                        
                        if curr_profit >= 10.0 or curr_profit <= -0.5:
                            exchange.create_market_sell_order(symbol, amount)
                            st.success(f"✅ تم الإغلاق بربح: {curr_profit}%")
                            break
                        time.sleep(10)
                    break 

            time.sleep(5)
        except Exception as e:
            st.sidebar.warning(f"تنبيه: {str(e)}")
            time.sleep(10)

# --- الواجهة ---
with st.sidebar:
    k = st.text_input("API Key", type="password", key="m_key")
    s = st.text_input("Secret Key", type="password", key="m_secret")

if st.button("🚀 تشغيل القناص الآن", type="primary"):
    if k and s:
        st.session_state.bot_active = True
        threading.Thread(target=trading_engine, args=(k, s), daemon=True).start()
        st.success("بدأ البحث... راقب التنبيهات الجانبية")

if st.button("🛑 إيقاف"):
    st.session_state.bot_active = False
    
