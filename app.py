import streamlit as st
import threading
import time
import ccxt

# --- CONFIGURATION ---
st.set_page_config(page_title="MEXC AI Sniper", layout="centered")
st.title("⚡ AI Sniper Bot (MEXC Edition)")

if 'bot_active' not in st.session_state:
    st.session_state.bot_active = False

# --- وظيفة إغلاق كافة الصفقات (زر الطوارئ) ---
def emergency_panic_exit(api_key, api_secret):
    try:
        exchange = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'enableRateLimit': True})
        balance = exchange.fetch_balance()
        # إيقاف عمل البوت أولاً
        st.session_state.bot_active = False
        
        # بيع كافة العملات المتاحة مقابل USDT
        for coin, details in balance['total'].items():
            if coin != 'USDT' and details > 0:
                symbol = f"{coin}/USDT"
                st.warning(f"🚨 Emergency Sell: {symbol}...")
                exchange.create_market_sell_order(symbol, details)
        st.success("✅ All positions liquidated to USDT. Bot stopped.")
    except Exception as e:
        st.error(f"Panic Exit Error: {e}")

# --- محرك التداول السريع ---
def trading_engine_mexc(api_key, api_secret):
    exchange = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'enableRateLimit': True})
    while st.session_state.get('bot_active', False):
        try:
            # 1. إدارة رأس المال التراكمي
            balance = exchange.fetch_balance()
            usdt_total = balance['free'].get('USDT', 0)
            if usdt_total < 5: 
                time.sleep(10); continue

            # 2. المسح السريع للسوق (حساسية 0.5%)
            tickers = exchange.fetch_tickers()
            fast_pairs = [s for s in tickers if '/USDT' in s and tickers[s]['percentage'] > 0.5]
            
            if fast_pairs:
                target = fast_pairs[0]
                entry_price = tickers[target]['last']
                
                # 3. مراقبة لحظية (حماية 0.4% وهدف 10%)
                start_time = time.time()
                while (time.time() - start_time) < 3600:
                    if not st.session_state.get('bot_active', False): break
                    
                    current_ticker = exchange.fetch_ticker(target)
                    profit = ((current_ticker['last'] - entry_price) / entry_price) * 100
                    
                    if profit >= 10 or profit <= -0.4:
                        # تنفيذ أمر البيع هنا
                        break
                    time.sleep(5)
            time.sleep(2)
        except Exception:
            time.sleep(15)

# --- واجهة التحكم ---
with st.sidebar:
    st.header("🔑 MEXC API Keys")
    k = st.text_input("API Key", type="password")
    s = st.text_input("Secret Key", type="password")
    st.divider()
    st.caption("تعطيل ترجمة المتصفح ضروري لاستقرار البوت.")

# زر الطوارئ الكبير
if st.button("🚨 EMERGENCY STOP & SELL ALL", type="primary", use_container_width=True):
    if k and s:
        emergency_panic_exit(k, s)
    else:
        st.error("Missing API Keys!")

st.divider()

col1, col2 = st.columns(2)
with col1:
    if st.button("🚀 Start Scalping", use_container_width=True):
        st.session_state.bot_active = True
        threading.Thread(target=trading_engine_mexc, args=(k, s), daemon=True).start()
        st.success("Bot is hunting for profits...")

with col2:
    if st.button("🛑 Stop Scanning", use_container_width=True):
        st.session_state.bot_active = False
        st.warning("Bot will stop after finishing current task.")

st.divider()
st.info("الاستراتيجية: قناص سريع (Scalping) | الربح المستهدف: 10% | الحماية من الانعكاس: 0.4%")
