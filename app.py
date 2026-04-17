import streamlit as st
import time

# تعريف الزر
if 'run' not in st.session_state: st.session_state.run = False

if st.sidebar.button("🚀 تشغيل"): st.session_state.run = True
if st.sidebar.button("🛑 إيقاف قسري"): 
    st.session_state.run = False
    st.rerun() # تحديث الصفحة لإجبار الحلقة على التوقف

# الحلقة الآمنة
while st.session_state.run:
    # --- كود التداول هنا ---
    st.write("البوت يعمل...")
    
    # أهم سطر: التحقق من زر الإيقاف داخل الحلقة
    time.sleep(2) 
    if not st.session_state.run:
        break # الخروج من الحلقة فوراً
