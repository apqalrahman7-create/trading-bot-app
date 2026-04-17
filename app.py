import streamlit as st
import threading
import time
import ccxt

st.set_page_config(page_title="MEXC Force Sniper", layout="centered")
st.title("⚡ AI Sniper - Instant Execution Mode")

if 'bot_active' not in st.session_state:
    st.session_state.bot_active = False

def trading_engine(api_key, api_secret):
    exchange = ccxt.mexc({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })

    while st.session_state.get('bot_active', False):
        try:
            # 1. فحص الرصيد المتاح
            balance = exchange.fetch_balance()
            free_usdt = balance['free'].get('USDT', 0)
            
            if free_usdt < 5: # الحد الأدنى في MEXC
                st.toast("⚠️ رصيد USDT غير كافٍ للبدء")
                time.sleep(30)
                continue

            # 2. جلب كافة العملات وترتيبها حسب الأعلى صعوداً (Top Gainers)
            tickers = exchange.fetch_tickers()
            # فلترة العملات الصالحة مقابل USDT
            valid_pairs = {k: v for k, v in tickers.items() if '/USDT' in k and v['percentage'] is not None}
            # ترتيبها لاختيار الأكثر نشاطاً (Momentum)
            sorted_pairs = sorted(valid_pairs.items(), key=lambda x: x[1]['percentage'], reverse=True)

            if sorted_pairs:
                target_symbol = sorted_pairs[0][0] # اختيار العملة رقم 1 في السوق الآن
                price = sorted_pairs[0][1]['last']
                
                # تنفيذ الشراء فوراً (Instant Market Buy)
                amount = (free_usdt * 0.98) / price # استخدام 98% لضمان تغطية الرسوم
                
                st.toast(f"🎯 تنفيذ شراء فوري: {target_symbol}")
                exchange.create_market_buy_order(target_symbol, amount)
                
                # 3. مراقبة الربح التراكمي (هدف 10% أو حماية من الانعكاس)
                entry_price = price
                while st.session_state.get('bot_active', False):
                    curr_ticker = exchange.fetch_ticker(target_symbol)
                    curr_profit = ((curr_ticker['last'] - entry_price) / entry_price) * 100
                    
                    # عرض الحالة للمستخدم
                    st.write(f"📈 {target_symbol} Profit: {curr_profit:.2f}%")
                    
                    if curr_profit >= 10.0 or curr_profit <= -0.5:
                        exchange.create_market_sell_order(target_symbol, amount)
                        st.success(f"✅ تم الإغلاق. الربح المضاف للمحفظة: {curr_profit:.2f}%")
                        break
                    time.sleep(5) # فحص سريع جداً

            time.sleep(5)
        except Exception as e:
            st.error(f"Execution Error: {e}")
            time.sleep(20)

# --- UI ---
with st.sidebar:
    k = st.text_input("MEXC API Key", type="password")
    s = st.text_input("MEXC Secret Key", type="password")

if st.button("🚀 تشغيل القناص (تنفيذ فوري)", type="primary", use_container_width=True):
    if k and s:
        st.session_state.bot_active = True
        threading.Thread(target=trading_engine, args=(k, s), daemon=True).start()
        st.success("البوت بدأ العمل... سيتم فتح صفقة على أقوى عملة في السوق حالاً.")

if st.button("🛑 إيقاف"):
    st.session_state.bot_active = False
    
