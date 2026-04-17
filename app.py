import streamlit as st
import ccxt
import pandas as pd
import time

# --- إعدادات الواجهة ---
st.set_page_config(page_title="Global AI Sniper", layout="wide")
st.title("🌐 Global AI Sniper - All MEXC Pairs")

# مدخلات المستخدم
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")
budget_per_trade = st.sidebar.number_input("المبلغ لكل صفقة (USDT)", min_value=10.0, value=11.0)
min_volume = st.sidebar.number_input("أقل حجم تداول 24h للفترة (USDT)", value=100000)

# تهيئة المنصة
def get_mexc():
    return ccxt.mexc({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
    })

# دالة التحليل الفني
def analyze_signal(df):
    if len(df) < 20: return 'hold'
    # استراتيجية سريعة: تقاطع RSI مع المتوسط
    df['rsi'] = ccxt.Exchange.calculate_ohlcv_rsi(df['c'].values, 14)
    last_rsi = df['rsi'].iloc[-1]
    # إشارة شراء إذا كان الـ RSI تحت 30 (تشبع بيعي) وبدأ بالارتداد
    if last_rsi < 30:
        return 'buy'
    return 'hold'

if 'active' not in st.session_state:
    st.session_state.active = False

col1, col2 = st.columns(2)
if col1.button("🚀 ابدأ مسح السوق الكامل"): st.session_state.active = True
if col2.button("🛑 إيقاف"): st.session_state.active = False

log_area = st.empty()

if st.session_state.active:
    try:
        exchange = get_mexc()
        # 1. جلب كافة العملات المتاحة مقابل USDT فقط
        markets = exchange.load_markets()
        symbols = [s for s in markets if '/USDT' in s and markets[s]['active']]
        
        st.info(f"🔍 تم العثور على {len(symbols)} عملة. جاري الفحص...")

        while st.session_state.active:
            for symbol in symbols:
                if not st.session_state.active: break
                
                try:
                    # فحص حجم التداول أولاً لتجنب العملات الميتة
                    ticker = exchange.fetch_ticker(symbol)
                    if ticker['quoteVolume'] < min_volume: continue

                    # جلب البيانات والتحليل
                    ohlcv = exchange.fetch_ohlcv(symbol, '1m', limit=30)
                    df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                    signal = analyze_signal(df)

                    log_area.write(f"⏳ فحص {symbol} | السعر: {ticker['last']} | الإشارة: {signal}")

                    if signal == 'buy':
                        st.warning(f"🎯 هدف مكتشف! محاولة شراء {symbol}")
                        # تنفيذ الشراء
                        amount = budget_per_trade / ticker['last']
                        precise_amount = exchange.amount_to_precision(symbol, amount)
                        order = exchange.create_market_buy_order(symbol, precise_amount)
                        st.success(f"✅ تم شراء {symbol}! رقم الأمر: {order['id']}")
                        time.sleep(2) # راحة بسيطة بعد كل عملية

                except Exception as e:
                    continue # تخطي أي عملة بها خطأ في البيانات
            
            st.write("♻️ اكتملت دورة المسح الشامل، إعادة البدء...")
            time.sleep(5)

    except Exception as e:
        st.error(f"❌ خطأ عام: {e}")
        
