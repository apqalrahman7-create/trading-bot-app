import streamlit as st
import ccxt
import time

# --- الإعدادات الثابتة ---
MAX_OPEN_TRADES = 3      # لن يفتح أكثر من 3 صفقات أبداً
TRADE_AMOUNT_USD = 12.0  # مبلغ الصفقة
TAKE_PROFIT = 1.015      # ربح 1.5%
STOP_LOSS = 0.985        # خسارة 1.5%

st.title("🛡️ AI Sniper - Safe Mode")

if 'running' not in st.session_state: st.session_state.running = False
if 'open_trades' not in st.session_state: st.session_state.open_trades = []
if 'total_profit' not in st.session_state: st.session_state.total_profit = 0.0

# الأزرار في الجانب
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

if st.sidebar.button("🚀 تشغيل"): st.session_state.running = True
if st.sidebar.button("🛑 إيقاف"): st.session_state.running = False

# عرض الإحصائيات
st.metric("الربح", f"${st.session_state.total_profit:.2f}")
st.write(f"📦 الصفقات المفتوحة حالياً: {len(st.session_state.open_trades)} / {MAX_OPEN_TRADES}")

if st.session_state.running:
    try:
        ex = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'enableRateLimit': True})
        
        # حلقة المسح
        while st.session_state.running:
            # 1. أولاً: مراقبة الصفقات المفتوحة لبيعها (الأولوية للبيع)
            for trade in st.session_state.open_trades[:]:
                symbol = trade['symbol']
                entry_price = trade['price']
                
                curr_price = ex.fetch_ticker(symbol)['last']
                
                # شرط البيع بربح أو خسارة
                if curr_price >= entry_price * TAKE_PROFIT or curr_price <= entry_price * STOP_LOSS:
                    st.warning(f"🔔 محاولة بيع {symbol}...")
                    bal = ex.fetch_balance()[symbol.split('/')[0]]['free']
                    ex.create_market_sell_order(symbol, ex.amount_to_precision(symbol, bal))
                    
                    st.session_state.total_profit += (curr_price - entry_price) * trade['amount']
                    st.session_state.open_trades.remove(trade)
                    st.success(f"✅ تمت عملية البيع بنجاح!")
                    st.rerun()

            # 2. ثانياً: البحث عن شراء جديد (فقط إذا كان لدينا مكان متاح)
            if len(st.session_state.open_positions) < MAX_OPEN_TRADES:
                # مسح مختصر لأهم العملات فقط لتوفير الوقت
                markets = ex.fetch_tickers(['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'ARB/USDT', 'PEPE/USDT'])
                for symbol, data in markets.items():
                    if any(t['symbol'] == symbol for t in st.session_state.open_trades): continue
                    
                    # شرط الشراء: إذا هبط السعر 1% في الدقيقة الأخيرة (ارتداد سريع)
                    if data['percentage'] < -1.0: 
                        st.info(f"🎯 قنص فرصة ارتداد: {symbol}")
                        price = data['last']
                        amount = TRADE_AMOUNT_USD / price
                        p_amount = ex.amount_to_precision(symbol, amount)
                        
                        order = ex.create_market_buy_order(symbol, p_amount)
                        st.session_state.open_trades.append({'symbol': symbol, 'price': price, 'amount': amount})
                        st.write(f"🛒 تم شراء {symbol} بسعر {price}")
                        st.rerun()
                        break # توقف بعد كل عملية شراء لإعادة فحص السوق
            
            time.sleep(5)
            
    except Exception as e:
        st.error(f"⚠️ تنبيه: {e}")
        time.sleep(10)
        
