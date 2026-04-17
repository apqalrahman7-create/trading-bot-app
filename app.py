import streamlit as st
import ccxt
import time

# إعدادات مخففة جداً للتجربة فقط
LEVERAGE = 5
MAX_TRADES = 1 
MIN_VOLATILITY = 0.1 # سيفتح صفقة إذا تحرك السعر 0.1% فقط (للتجربة)

st.title("🐞 مصلح أخطاء البوت - فحص الاتصال")

api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

if st.sidebar.button("🚀 ابدأ الفحص والتداول"):
    st.session_state.running = True

if st.session_state.running:
    try:
        ex = ccxt.mexc({
            'apiKey': api_key,
            'secret': api_secret,
            'options': {'defaultType': 'swap'}
        })

        # --- خطوة 1: فحص الرصيد (للتأكد من أنه يرى محفظة الفيوتشرز) ---
        balance = ex.fetch_balance()
        usdt_free = balance['free'].get('USDT', 0)
        st.write(f"💰 الرصيد المتاح في الفيوتشرز: {usdt_free} USDT")

        if usdt_free < 5:
            st.error("❌ رصيدك أقل من 5 دولار في محفظة الفيوتشرز. لن يتم فتح صفقات.")
        else:
            # --- خطوة 2: محاولة فتح صفقة تجريبية فوراً ---
            symbol = 'BTC/USDT:USDT'
            ticker = ex.fetch_ticker(symbol)
            change = ticker['percentage']
            
            st.write(f"📊 حالة السوق لـ BTC: التغير الحالي {change}%")

            if abs(change) >= MIN_VOLATILITY:
                side = 'buy' if change > 0 else 'sell'
                st.write(f"🎯 محاولة فتح صفقة {side} بمبلغ 10$...")
                
                # حساب الكمية (تأكد من كبر المبلغ لتجاوز الحد الأدنى)
                amount = (10.0 * LEVERAGE) / ticker['last']
                
                # تنفيذ الأمر مع معالجة الخطأ التفصيلية
                try:
                    ex.set_leverage(LEVERAGE, symbol)
                    order = ex.create_market_order(symbol, side, amount, params={'openType': 2})
                    st.success(f"✅ نجحت العملية! تم فتح صفقة: {order['id']}")
                except Exception as trade_error:
                    st.error(f"❌ المنصة رفضت الصفقة. السبب: {str(trade_error)}")
            else:
                st.warning("⏳ السوق مستقر جداً، الشرط لم يتحقق بعد.")

    except Exception as connection_error:
        st.error(f"❌ خطأ في الاتصال أو المفاتيح: {str(connection_error)}")
    
    time.sleep(10)
    st.rerun()
    
