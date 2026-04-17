import streamlit as st
from pymexc import spot
from llama_cpp import Llama  # مكتبة الذكاء الاصطناعي أوفلاين
import time

# 1. إعدادات واجهة Streamlit
st.set_page_config(page_title="AI Offline Trader", layout="wide")
st.title("🤖 بوت التداول الذكي (ملف واحد - أوفلاين)")

# 2. تحميل الذكاء الاصطناعي (يتم مرة واحدة فقط لتوفير الذاكرة)
@st.cache_resource
def load_ai():
    # استبدل 'model.gguf' باسم ملف النموذج الذي حملته على جهازك
    return Llama(model_path="model.gguf", n_ctx=2048)

ai_model = load_ai()

# 3. القائمة الجانبية للإعدادات
with st.sidebar:
    st.header("⚙️ الإعدادات")
    api_key = st.text_input("MEXC API Key", type="password")
    secret_key = st.text_input("MEXC Secret Key", type="password")
    symbol = st.text_input("العملة", value="BTCUSDT")
    trade_amount = st.number_input("مبلغ الدخول ($)", value=10)
    is_running = st.button("🚀 بدء التداول الآلي")

# 4. دالة اتخاذ القرار عبر الذكاء الاصطناعي
def ai_decision(price):
    prompt = f"السعر الحالي لعملة {symbol} هو {price}. هل تنصح بالشراء أم الانتظار؟ أجب بكلمة واحدة فقط: BUY أو WAIT."
    response = ai_model(f"Q: {prompt} A:", max_tokens=10)
    return response["choices"][0]["text"].strip().upper()

# 5. منطق التشغيل
if is_running:
    if not api_key or not secret_key:
        st.error("يرجى إدخال مفاتيح الـ API أولاً!")
    else:
        client = spot.HTTP(api_key=api_key, api_secret=secret_key)
        st.success("البوت يعمل الآن...")
        
        status_box = st.empty()
        log_box = st.empty()
        
        while True:
            try:
                # جلب السعر
                ticker = client.ticker_price(symbol)
                current_price = float(ticker['price'])
                
                # استشارة الذكاء الاصطناعي
                decision = ai_decision(current_price)
                
                status_box.metric("السعر الحالي", f"${current_price}", delta=decision)
                
                if "BUY" in decision:
                    log_box.write("✅ ذكاء اصطناعي: تم إرسال أمر شراء...")
                    # كود الشراء الحقيقي (مفعل):
                    # client.new_order(symbol=symbol, side="BUY", type="MARKET", quoteOrderQty=trade_amount)
                
                time.sleep(10) # فحص كل 10 ثوانٍ
            except Exception as e:
                st.error(f"خطأ: {e}")
                break
                
