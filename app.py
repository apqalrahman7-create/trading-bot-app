import streamlit as st
import ccxt
import pandas as pd
import time

# إعداد واجهة المستخدم
st.set_page_config(page_title="MEXC AI Sniper", page_icon="⚡")
st.title("⚡ AI Sniper - Instant Execution")

# الإعدادات في الجانب الجانبي
st.sidebar.header("⚙️ إعدادات البوت")
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")
symbol = st.sidebar.text_input("الزوج (مثال: BTC/USDT)", value="BTC/USDT")
amount_usdt = st.sidebar.number_input("مبلغ الشراء بـ USDT", min_value=10.0, value=15.0)

# تهيئة الاتصال بالمنصة
def init_exchange(key, secret):
    return ccxt.mexc({
        'apiKey': key,
        'secret': secret,
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })

# دالة جلب البيانات والتحليل
def get_signal(exchange, symbol):
    bars = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=50)
    df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
    
    # استراتيجية بسيطة: تقاطع المتوسطات
    df['sma_fast'] = df['c'].rolling(window=5).mean()
    df['sma_slow'] = df['c'].rolling(window=20).mean()
    
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]
    
    if prev_row['sma_fast'] < prev_row['sma_slow'] and last_row['sma_fast'] > last_row['sma_slow']:
        return 'buy'
    elif prev_row['sma_fast'] > prev_row['sma_slow'] and last_row['sma_fast'] < last_row['sma_slow']:
        return 'sell'
    return 'hold'

# التحكم في التشغيل
if 'running' not in st.session_state:
    st.session_state.running = False

col1, col2 = st.columns(2)
if col1.button("🚀 تشغيل البوت"):
    if not api_key or not api_secret:
        st.error("الرجاء إدخال مفاتيح API أولاً!")
    else:
        st.session_state.running = True

if col2.button("🛑 إيقاف"):
    st.session_state.running = False

# حلقة التنفيذ الرئيسية
status_box = st.empty()
log_box = st.container()

if st.session_state.running:
    try:
        mexc = init_exchange(api_key, api_secret)
        status_box.success(f"البوت يعمل الآن على زوج {symbol}...")
        
        while st.session_state.running:
            signal = get_signal(mexc, symbol)
            current_price = mexc.fetch_ticker(symbol)['last']
            
            with log_box:
                st.write(f"🔍 تحليل: السعر {current_price} | الإشارة: {signal}")
            
            if signal == 'buy':
                st.warning("🎯 إشارة شراء اكتشفت! جاري التنفيذ...")
                # حساب الكمية بناءً على المبلغ والدقة المطلوبة في MEXC
                amount = amount_usdt / current_price
                precise_amount = mexc.amount_to_precision(symbol, amount)
                
                order = mexc.create_market_buy_order(symbol, precise_amount)
                st.balloons()
                st.success(f"✅ تم الشراء بنجاح! رقم العملية: {order['id']}")
                # توقف مؤقت بعد الشراء لتجنب تكرار الصفقات
                time.sleep(60) 

            elif signal == 'sell':
                st.info("🎯 إشارة بيع اكتشفت! جاري التنفيذ...")
                # هنا تحتاج لجلب رصيد العملة لبيعها بالكامل
                balance = mexc.fetch_balance()[symbol.split('/')[0]]['free']
                if balance > 0:
                    precise_sell = mexc.amount_to_precision(symbol, balance)
                    order = mexc.create_market_sell_order(symbol, precise_sell)
                    st.success(f"✅ تم البيع بنجاح! رقم العملية: {order['id']}")
                
            time.sleep(10) # فحص كل 10 ثواني
            
    except Exception as e:
        st.error(f"❌ حدث خطأ: {str(e)}")
        st.session_state.running = False
        
