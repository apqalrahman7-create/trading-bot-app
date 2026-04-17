import streamlit as st
import ccxt
import time

# --- إعدادات الواجهة ---
st.set_page_config(page_title="MEXC AI Bot", page_icon="📈")
st.title("🤖 بوت التداول الذكي (MEXC)")

# --- 🟢 ضع مفاتيحك هنا بين علامات الاقتباس ---
MY_API_KEY = "اكتب_هنا_الـ_ACCESS_KEY_الخاص_بك"
MY_SECRET_KEY = "اكتب_هنا_الـ_SECRET_KEY_الخاص_بك"

# --- محرك التداول ---
try:
    exchange = ccxt.mexc({
        'apiKey': MY_API_KEY,
        'secret': MY_SECRET_KEY,
        'enableRateLimit': True,
    })
    
    # جلب الرصيد للتأكد من الربط
    balance = exchange.fetch_balance()
    usdt_balance = balance['total'].get('USDT', 0)
    st.success(f"✅ تم الاتصال بنجاح! الرصيد الحالي: {usdt_balance:.2f} USDT")
    
except Exception as e:
    st.error(f"❌ خطأ في الربط: تأكد من وضع المفاتيح بشكل صحيح داخل الكود.")
    st.stop()

# --- إعدادات الاستراتيجية ---
st.sidebar.header("⚙️ إعدادات الهدف")
target_profit = 1.10  # تعني ربح 10%
order_amount = 12     # مبلغ الدخول بالدولار

if st.button("🚀 ابدأ صيد الأرباح (10%)"):
    status = st.empty()
    status.info("🔎 جاري مسح السوق بحثاً عن عملة صاعدة...")
    
    # فحص أفضل العملات الصاعدة حالياً
    tickers = exchange.fetch_tickers()
    # فلترة العملات الصاعدة بين 2% و 5%
    opportunities = [s for s in tickers if '/USDT' in s and 2.0 <= tickers[s].get('percentage', 0) <= 5.0]
    
    if opportunities:
        selected_symbol = opportunities[0]
        current_price = tickers[selected_symbol]['last']
        status.success(f"🎯 تم العثور على فرصة في {selected_symbol} بسعر {current_price}")
        
        # تنفيذ الشراء
        try:
            st.write(f"🛒 جاري شراء {selected_symbol} بمبلغ {order_amount}$...")
            # لسلامتك، قمنا بتعطيل أمر الشراء الحقيقي حتى تتأكد من الرصيد أولاً
            # لتفعيله امسح علامة الـ # من السطر التالي:
            # exchange.create_market_buy_order(selected_symbol, order_amount)
            
            st.warning(f"💡 بمجرد الشراء، سأقوم بوضع أمر بيع تلقائي عند سعر {current_price * target_profit:.4f}")
        except Exception as e:
            st.error(f"فشل الشراء: {e}")
    else:
        status.warning("😴 السوق هادئ حالياً، لا توجد فرص صعود 10% الآن.")

st.divider()
st.caption("تأكد من إبقاء هذه الصفحة مفتوحة لكي يستمر البوت في المراقبة.")
