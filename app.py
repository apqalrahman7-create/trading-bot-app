import streamlit as st
import threading
import time
import ccxt

st.set_page_config(page_title="12H Compound Sniper", layout="centered")
st.title("📈 MEXC 12H Portfolio Growth (+10%)")

if 'bot_active' not in st.session_state:
    st.session_state.bot_active = False

def compounding_engine(api_key, api_secret):
    # إعداد الاتصال بمنصة MEXC
    exchange = ccxt.mexc({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
    
    while st.session_state.get('bot_active', False):
        try:
            # 1. جلب رصيد البداية للدورة
            balance = exchange.fetch_balance()
            start_usdt = balance['total'].get('USDT', 0)
            target_usdt = start_usdt * 1.10
            
            # 2. مسح السوق بحثاً عن عملات صاعدة (حساسية عالية جداً)
            tickers = exchange.fetch_tickers()
            # نبحث عن أي عملة صاعدة > 0.1% لسرعة التنفيذ
            potential_pairs = [s for s in tickers if '/USDT' in s and tickers[s]['percentage'] > 0.1]
            
            if potential_pairs:
                symbol = potential_pairs[0] # اختيار أول عملة متاحة
                usdt_free = exchange.fetch_balance()['free'].get('USDT', 0)
                
                if usdt_free > 5: # الحد الأدنى للتداول في MEXC
                    amount_to_spend = usdt_free / 2 # استخدام نصف السيولة المتاحة
                    price = tickers[symbol]['last']
                    amount_to_buy = amount_to_spend / price
                    
                    # --- تنفيذ أمر شراء حقيقي (Market Buy) ---
                    st.toast(f"🚀 Buying {symbol} to reach +10% target...")
                    order = exchange.create_market_buy_order(symbol, amount_to_buy)
                    entry_price = price
                    
                    # 3. مراقبة الصفقة (الخروج عند ربح 2% أو خسارة 0.4% لجمع الأرباح)
                    start_time = time.time()
                    while (time.time() - start_time) < 3600: # ساعة واحدة كحد أقصى للصفقة
                        current_ticker = exchange.fetch_ticker(symbol)
                        current_price = current_ticker['last']
                        profit = ((current_price - entry_price) / entry_price) * 100
                        
                        # إغلاق الصفقة (بيع حقيقي)
                        if profit >= 2.0 or profit <= -0.4:
                            exchange.create_market_sell_order(symbol, amount_to_buy)
                            st.toast(f"✅ Sold {symbol} | Profit: {profit:.2f}%")
                            break
                        time.sleep(5)
            
            time.sleep(10) # انتظار بسيط قبل البحث التالي
            
        except Exception as e:
            st.error(f"Execution Error: {e}")
            time.sleep(20)

# --- الواجهة ---
with st.sidebar:
    k = st.text_input("MEXC API Key", type="password")
    s = st.text_input("MEXC Secret Key", type="password")

if st.button("🚀 Start 12H Compound Mode", type="primary", use_container_width=True):
    if k and s:
        st.session_state.bot_active = True
        threading.Thread(target=compounding_engine, args=(k, s), daemon=True).start()
        st.success("Bot is LIVE! Trading to reach +10% total growth.")

if st.button("🛑 Stop & Emergency Sell", use_container_width=True):
    st.session_state.bot_active = False
    st.warning("Stopping bot and clearing memory...")
    
