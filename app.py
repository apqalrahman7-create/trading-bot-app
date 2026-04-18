import streamlit as st
import ccxt
import pandas as pd
from datetime import datetime
import time

# --- 1. إعدادات النظام المتقدمة ---
LEVERAGE = 5
MAX_TRADES = 10         
TP_TARGET = 0.04        # هدف ربح 4%
SL_LIMIT = -0.02        # وقف خسارة 2%
TRADE_DURATION_MINS = 30 
ANALYSIS_TIMEFRAME = '2m' # تحليل فريم الدقيقتين

st.set_page_config(page_title="AI Integrated Engine Pro", layout="wide")
st.title("🤖 المحرك المتكامل الذكي (إصدار الحماية)")
st.caption("تم دمج المحرك وحل مشكلات الربط مع MEXC")

# تهيئة مخزن البيانات
if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- 2. واجهة التحكم الجانبية ---
st.sidebar.header("🔑 إعدادات الوصول")
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("Secret Key", type="password")

if st.sidebar.button("🚀 تشغيل المحرك"):
    if api_key and api_secret: st.session_state.running = True
    else: st.sidebar.error("يرجى إدخال المفاتيح أولاً")

if st.sidebar.button("🚨 إيقاف وتصفية"):
    st.session_state.running = False

# --- 3. المحرك الرئيسي (All-in-One Engine) ---
if st.session_state.running and api_key and api_secret:
    try:
        # إعداد الاتصال مع MEXC مع معاملات العقود الآجلة الصحيحة
        ex = ccxt.mexc({
            'apiKey': api_key, 
            'secret': api_secret, 
            'options': {'defaultType': 'swap'},
            'enableRateLimit': True
        })
        
        # جلب الرصيد وتحديث مبلغ الدخول التراكمي
        balance = ex.fetch_balance()
        total_equity = balance['total'].get('USDT', 0)
        free_usdt = balance['free'].get('USDT', 0)
        # دخول بـ 15% من إجمالي المحفظة لنمو سريع
        dynamic_entry = max(11, total_equity * 0.15) 

        # أ. مراقبة الصفقات النشطة وإغلاقها
        for sym, data in list(st.session_state.positions.items()):
            ticker = ex.fetch_ticker(sym)
            current_p = ticker['last']
            
            # حساب الربح/الخسارة بناءً على نوع الصفقة
            if data['side'] == 'buy':
                pnl = (current_p - data['entry']) / data['entry']
            else:
                pnl = (data['entry'] - current_p) / data['entry']
            
            mins_passed = (datetime.now() - data['start_time']).total_seconds() / 60
            
            # شروط الخروج (الهدف، الوقت، أو الحماية)
            if pnl >= TP_TARGET or pnl <= SL_LIMIT or mins_passed >= TRADE_DURATION_MINS:
                side_close = 'sell' if data['side'] == 'buy' else 'buy'
                # المعامل positionType ضروري لمنع Parameter Error (1 للشراء، 2 للبيع)
                p_type = 2 if data['side'] == 'buy' else 1
                try:
                    ex.create_market_order(sym, side_close, data['amount'], params={'openType': 2, 'positionType': p_type})
                    del st.session_state.positions[sym]
                    st.toast(f"✅ تم إغلاق {sym} بنجاح")
                except Exception as e:
                    st.error(f"فشل إغلاق {sym}: {e}")

        # ب. تحليل السوق (40 عملة) واقتناص الفرص
        if len(st.session_state.positions) < MAX_TRADES and free_usdt > dynamic_entry:
            tickers = ex.fetch_tickers()
            symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT')][:40]
            
            for s in symbols:
                if s in st.session_state.positions: continue
                if len(st.session_state.positions) >= MAX_TRADES: break
                
                try:
                    # تحليل سريع لشموع الدقيقتين
                    ohlcv = ex.fetch_ohlcv(s, timeframe=ANALYSIS_TIMEFRAME, limit=10)
                    df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
                    curr_p = df['close'].iloc[-1]
                    avg_p = df['close'].mean()
                    
                    # قرار الدخول: إذا كان السعر يندفع بقوة فوق المتوسط اللحظي
                    side = 'buy' if curr_p > avg_p and curr_p > df['open'].iloc[-1] else 'sell' if curr_p < avg_p and curr_p < df['open'].iloc[-1] else None
                    
                    if side:
                        # 1. ضبط الرافعة المالية
                        p_type = 1 if side == 'buy' else 2
                        ex.set_leverage(LEVERAGE, s, params={'openType': 2, 'positionType': p_type})
                        
                        # 2. حساب الكمية الدقيقة
                        raw_amt = (dynamic_entry * LEVERAGE) / curr_p
                        final_amt = float(ex.amount_to_precision(s, raw_amt))
                        
                        # 3. فتح الصفقة مع المعاملات الإجبارية لمنع خطأ Parameter Error
                        ex.create_market_order(s, side, final_amt, params={'openType': 2, 'positionType': p_type})
                        
                        st.session_state.positions[s] = {
                            'side': side, 'entry': curr_p, 'amount': final_amt,
                            'start_time': datetime.now(), 'capital': dynamic_entry
                        }
                        st.info(f"🚀 تم فتح صفقة {side.upper()} في {s}")
                        break 
                except:
                    continue

        # ج. عرض البيانات في الواجهة
        col1, col2, col3 = st.columns(3)
        col1.metric("إجمالي المحفظة", f"${total_equity:.2f}")
        col2.metric("حجم الصفقة القادمة", f"${dynamic_entry:.2f}")
        col3.metric("الصفقات المفتوحة", len(st.session_state.positions))
        
        if st.session_state.positions:
            st.write("### 📊 الصفقات النشطة")
            st.dataframe(pd.DataFrame(st.session_state.positions).T[['side', 'entry', 'capital']], use_container_width=True)

        time.sleep(25)
        st.rerun()

    except Exception as e:
        st.warning(f"المحرك يقوم بمسح الإشارات... {e}")
        time.sleep(10)
        st.rerun()
                     
