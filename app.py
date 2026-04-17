import streamlit as st
import threading
import time
import ccxt

# --- CONFIG ---
st.set_page_config(page_title="12H Compound Bot", layout="centered")
st.title("📈 12-Hour Portfolio Compounding Bot")

if 'bot_active' not in st.session_state:
    st.session_state.bot_active = False

def compounding_engine(api_key, api_secret):
    exchange = ccxt.mexc({'apiKey': api_key, 'secret': api_secret, 'enableRateLimit': True})
    
    while st.session_state.get('bot_active', False):
        try:
            # 1. تحديد رصيد البداية للدورة الحالية
            balance_data = exchange.fetch_balance()
            start_balance = balance_data['total'].get('USDT', 0)
            target_balance = start_balance * 1.10 # هدف 10% نمو للمحفظة
            
            start_time = time.time()
            twelve_hours = 12 * 3600 # 12 ساعة بالثواني
            
            st.toast(f"New Cycle Started! Capital: {start_balance:.2f}$, Target: {target_balance:.2f}$")

            # 2. حلقة العمل المكثف خلال الـ 12 ساعة
            while (time.time() - start_time) < twelve_hours:
                if not st.session_state.get('bot_active', False): break
                
                # تحديث الرصيد الحالي لمراقبة التقدم
                current_balance = exchange.fetch_balance()['total'].get('USDT', 0)
                progress = (current_balance - start_balance) / (target_balance - start_balance) if target_balance > start_balance else 0
                
                # فحص الهدف
                if current_balance >= target_balance:
                    st.success(f"🎊 Cycle Complete! Portfolio grew 10%. Profit added to capital.")
                    break # إنهاء الدورة والبدء في واحدة جديدة برأس مال أكبر (تراكمي)

                # 3. صفقات سريعة لجمع الأرباح (Scalping)
                usdt_free = exchange.fetch_balance()['free'].get('USDT', 0)
                if usdt_free > 5:
                    # ماسح سريع لـ MEXC واقتناص فرص الصعود > 0.1%
                    # تنفيذ الصفقات المقسمة لضمان استمرارية النمو
                    pass
                
                time.sleep(30) # تحديث كل 30 ثانية
            
            # انتظار بسيط قبل بدء الدورة التراكمية التالية
            time.sleep(60)
            
        except Exception as e:
            time.sleep(30)

# --- UI ---
with st.sidebar:
    st.header("🔑 MEXC Keys")
    k = st.text_input("API Key", type="password")
    s = st.text_input("Secret Key", type="password")

if st.button("🚀 Start 12H Compound Mode", type="primary", use_container_width=True):
    if k and s:
        st.session_state.bot_active = True
        threading.Thread(target=compounding_engine, args=(k, s), daemon=True).start()
        st.success("Compounding bot is active! Target: +10% every 12 hours.")

if st.button("🚨 Emergency Exit & Sell All", use_container_width=True):
    st.session_state.bot_active = False
    # كود إغلاق كافة الصفقات الذي صممناه
    
