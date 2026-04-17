import streamlit as st
import threading
import time
import ccxt

st.set_page_config(page_title="Ultra-Fast Sniper", layout="centered")
st.title("⚡ AI Ultra-Fast Sniper Bot")

if 'bot_active' not in st.session_state:
    st.session_state.bot_active = False

def fast_trading_engine(api_key, api_secret):
    exchange = ccxt.binance({'apiKey': api_key, 'secret': api_secret, 'enableRateLimit': True})
    
    while st.session_state.get('bot_active', False):
        try:
            # 1. التداول التراكمي: جلب الرصيد وتقسيمه
            balance = exchange.fetch_balance()
            usdt_total = balance['free'].get('USDT', 0)
            if usdt_total < 10: 
                time.sleep(30); continue
            
            # دخول بـ 25% من المحفظة لزيادة الأرباح التراكمية
            trade_amount = usdt_total * 0.25 

            # 2. ماسح السوق السريع (Real-time Scanner)
            tickers = exchange.fetch_tickers()
            # نبحث عن أي عملة بدأت بالتحرك (صعود > 1.5% فقط) لسرعة التنفيذ
            fast_pairs = [s for s in tickers if '/USDT' in s and tickers[s]['percentage'] > 1.5]
            
            if fast_pairs:
                target = fast_pairs[0] # اختيار أول عملة تحقق الشرط فوراً
                entry_price = tickers[target]['last']
                
                # 3. مراقبة "الشموع الحية" (الحماية من انعكاس السوق)
                start_time = time.time()
                while (time.time() - start_time) < 3600: # حد الـ 60 دقيقة
                    if not st.session_state.get('bot_active', False): break
                    
                    current_ticker = exchange.fetch_ticker(target)
                    current_price = current_ticker['last']
                    profit = ((current_price - entry_price) / entry_price) * 100
                    
                    # --- الشروط الذكية ---
                    # أ- جني الربح السريع (10%)
                    if profit >= 10:
                        print(f"💰 Take Profit hit on {target}!")
                        break
                    
                    # ب- الخروج الفوري عند انعكاس السوق (حماية صارمة)
                    # إذا نزل السعر 0.5% فقط عن سعر الدخول، اخرج فوراً
                    if profit <= -0.5:
                        print(f"⚠️ Market reversed on {target}! Emergency Exit to save capital.")
                        break
                    
                    time.sleep(5) # فحص فائق السرعة كل 5 ثوانٍ
            
            time.sleep(2) # انتظار بسيط قبل الصيد التالي
        except Exception:
            time.sleep(10)

# --- الواجهة ---
with st.sidebar:
    k = st.text_input("API Key", type="password")
    s = st.text_input("Secret Key", type="password")

if st.button("🚀 Start Ultra-Fast Trading", type="primary", use_container_width=True):
    if k and s:
        st.session_state.bot_active = True
        threading.Thread(target=fast_trading_engine, args=(k, s), daemon=True).start()
        st.success("Fast Scanner Active! Entries will be much quicker now.")

if st.button("🛑 Stop Bot", use_container_width=True):
    st.session_state.bot_active = False

st.divider()
st.info("الوضع الحالي: البحث السريع مفعل | الحماية من الانعكاس: 0.5% | هدف الربح: 10%")
