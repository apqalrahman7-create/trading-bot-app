import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. إعدادات استقرار الواجهة ---
# التحديث التلقائي كل 30 ثانية يمنع خطأ removeChild ويحافظ على استمرار البوت
st_autorefresh(interval=30 * 1000, key="bot_refresh_stable")

# --- 2. إعدادات النظام ---
LEVERAGE = 5
MAX_TRADES = 10         
TP_TARGET = 0.04        # هدف 4%
SL_LIMIT = -0.02        # حماية 2%
TRADE_DURATION_MINS = 30 
ANALYSIS_TIMEFRAME = '2m' # تحليل فريم الدقيقتين كما طلبت

st.set_page_config(page_title="AI Trading Bot", layout="wide")
st.title("🤖 AI Autonomous Compound Bot (2m Analysis)")

# تهيئة مخزن الجلسة
if 'running' not in st.session_state: st.session_state.running = False
if 'positions' not in st.session_state: st.session_state.positions = {}

# --- 3. واجهة التحكم ---
st.sidebar.header("🔑 API Settings")
api_key = st.sidebar.text_input("MEXC API Key", type="password")
api_secret = st.sidebar.text_input("MEXC Secret Key", type="password")

col_btn1, col_btn2 = st.sidebar.columns(2)
if col_btn1.button("🚀 START"):
    if api_key and api_secret: st.session_state.running = True
if col_btn2.button("🚨 STOP"):
    st.session_state.running = False

# --- 4. دالة التوقع الذكي (2 دقيقة) ---
def get_prediction(ex, symbol):
    try:
        # جلب آخر 20 شمعة دقيقة للتحليل
        ohlcv = ex.fetch_ohlcv(symbol, timeframe=ANALYSIS_TIMEFRAME, limit=20)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        
        # مؤشرات سريعة للتنبؤ بالحركة القادمة
        df['RSI'] = ta.rsi(df['close'], length=7)
        df['EMA'] = ta.ema(df['close'], length=9)
        
        last = df.iloc[-1]
        
        # التوقع: شراء إذا كان السعر فوق المتوسط والزخم صاعد
        if last['close'] > last['EMA'] and 50 < last['RSI'] < 75:
            return 'buy'
        # التوقع: بيع إذا كان السعر تحت المتوسط والزخم هابط
        elif last['close'] < last['EMA'] and 25 < last['RSI'] < 50:
            return 'sell'
        return None
    except:
        return None

# --- 5. المحرك الرئيسي ---
if st.session_state.running and api_key and api_secret:
    try:
        # الربط مع المنصة (MEXC)
        ex = ccxt.mexc({
            'apiKey': api_key, 
            'secret': api_secret, 
            'options': {'defaultType': 'swap'},
            'enableRateLimit': True
        })
        
        # أ. حساب الربح التراكمي
        balance = ex.fetch_balance()
        total_equity = balance['total'].get('USDT', 0)
        free_usdt = balance['free'].get('USDT', 0)
        # دخول بـ 10% من إجمالي المحفظة لزيادة الأرباح تدريجياً
        dynamic_entry = max(10, total_equity * 0.10)

        # ب. مراقبة وإغلاق الصفقات
        for sym, data in list(st.session_state.positions.items()):
            ticker = ex.fetch_ticker(sym)
            current_p = ticker['last']
            
            # حساب الربح/الخسارة الفعلي
            pnl = (current_p - data['entry']) / data['entry'] if data['side'] == 'buy' else (data['entry'] - current_p) / data['entry']
            mins_passed = (datetime.now() - data['start_time']).total_seconds() / 60
            
            # شروط الإغلاق (4% ربح، 2% خسارة، أو 30 دقيقة)
            if pnl >= TP_TARGET or pnl <= SL_LIMIT or mins_passed >= TRADE_DURATION_MINS:
                side_close = 'sell' if data['side'] == 'buy' else 'buy'
                p_idx = 2 if data['side'] == 'buy' else 1
                ex.create_market_order(sym, side_close, data['amount'], params={'positionType': p_idx})
                del st.session_state.positions[sym]
                st.toast(f"✅ Closed {sym} | PNL: {pnl*100:.2f}%")

        # ج. تحليل 40 عملة وفتح صفقات جديدة بناءً على التوقع
        if len(st.session_state.positions) < MAX_TRADES and free_usdt > dynamic_entry:
            tickers = ex.fetch_tickers()
            symbols = [s for s in tickers.keys() if s.endswith('/USDT:USDT')][:40]
            
            for s in symbols:
                if s in st.session_state.positions or len(st.session_state.positions) >= MAX_TRADES: continue
                
                prediction = get_prediction(ex, s)
                if prediction:
                    try:
                        last_price = tickers[s]['last']
                        # حساب الكمية الدقيقة مع الرافعة المالية
                        raw_amt = (dynamic_entry * LEVERAGE) / last_price
                        final_amt = float(ex.amount_to_precision(s, raw_amt))
                        
                        p_idx = 1 if prediction == 'buy' else 2
                        ex.set_leverage(LEVERAGE, s, params={'positionType': p_idx})
                        ex.create_market_order(s, prediction, final_amt, params={'positionType': p_idx})
                        
                        st.session_state.positions[s] = {
                            'side': prediction, 'entry': last_price, 'amount': final_amt,
                            'start_time': datetime.now(), 'capital': dynamic_entry
                        }
                        st.info(f"🔮 AI Predicted {prediction.upper()} for {s}")
                        break 
                    except: continue

        # د. لوحة العرض (Dashboard)
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Equity (Compounded)", f"${total_equity:.2f}")
        col_m2.metric("Next Trade Size", f"${dynamic_entry:.2f}")
        col_m3.metric("Open Trades", len(st.session_state.positions))
        
        if st.session_state.positions:
            st.write("### 📈 Active Positions")
            df = pd.DataFrame(st.session_state.positions).T
            st.dataframe(df[['side', 'entry', 'start_time', 'capital']], use_container_width=True)

    except Exception as e:
        st.warning(f"Connecting to Exchange... {e}")

# تعليمات هامة للمستخدم
st.divider()
st.caption("⚠️ Note: Disable 'Google Translate' for this page to prevent browser errors.")

