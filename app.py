import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime

# --- ⚙️ إعدادات محرك الأرباح (الربح التراكمي) ---
SYMBOLS = ['ORDI_USDT', 'BTC_USDT', 'ETH_USDT', 'SOL_USDT', 'XRP_USDT', 'SUI_USDT', 'PEPE_USDT']
MAX_TRADES = 5           # تقسيم المحفظة على 5 صفقات فقط لقوة الربح
LEVERAGE = 5             # رافعة مالية متوازنة
RISK_PER_TRADE = 0.18    # الدخول بـ 18% من الرصيد (لترك مساحة للهامش والربح التراكمي)

st.set_page_config(page_title="Accumulative Profit Bot", layout="wide")
st.title("💰 بوت الأرباح التراكمية - النسخة المستقرة")

if 'running' not in st.session_state: st.session_state.running = False

with st.sidebar:
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 بدء جني الأرباح"): st.session_state.running = True
    if st.button("🛑 إيقاف فوري"): st.session_state.running = False

# --- المحرك الرئيسي ---
if st.session_state.running and api_key and api_secret:
    try:
        mexc = ccxt.mexc({
            'apiKey': api_key, 
            'secret': api_secret, 
            'options': {'defaultType': 'future'},
            'enableRateLimit': True
        })

        while st.session_state.running:
            # 1. جلب الرصيد الحي للربح التراكمي
            balance = mexc.fetch_balance()
            total_bal = float(balance['info']['data']['availableBalance'])
            
            # 2. فحص الصفقات المفتوحة
            pos = mexc.fetch_positions()
            active_p = [p for p in pos if float(p.get('contracts', 0)) != 0]
            current_count = len(active_p)
            active_names = [p['symbol'] for p in active_p]

            st.info(f"💰 الرصيد المتاح للتدوير: {total_bal:.2f} USDT | الصفقات: {current_count}/{MAX_TRADES}")

            for symbol in SYMBOLS:
                if current_count >= MAX_TRADES: break
                
                if symbol not in active_names:
                    try:
                        # تحليل سريع قبل الدخول (RSI)
                        ohlcv = mexc.fetch_ohlcv(symbol, timeframe='1m', limit=20)
                        df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                        delta = df['c'].diff()
                        rsi = 100 - (100 / (1 + (delta.clip(lower=0).mean() / -delta.clip(upper=0).mean())))

                        # شرط القنص
                        if rsi <= 35 or rsi >= 65:
                            side = 'buy' if rsi <= 35 else 'sell'
                            
                            # حساب حجم الصفقة (الربح التراكمي)
                            trade_val = total_bal * RISK_PER_TRADE
                            price = df['c'].iloc[-1]
                            qty = (trade_val * LEVERAGE) / price
                            formatted_qty = float(mexc.amount_to_precision(symbol, qty))

                            # --- حل خطأ الرافعة المالية ---
                            try:
                                mexc.set_leverage(LEVERAGE, symbol, {
                                    'openType': 2, # Cross Margin
                                    'positionType': 1 if side == 'buy' else 2
                                })
                            except: pass # إذا كانت مضبوطة مسبقاً

                            # تنفيذ الصفقة
                            mexc.create_market_order(symbol, side, formatted_qty)
                            st.success(f"🔥 تم فتح صفقة تراكمية لـ {symbol} بقيمة {trade_val:.2f}$")
                            current_count += 1
                            time.sleep(1)
                    except: continue

            time.sleep(20) # فحص كل 20 ثانية لإعادة الكرة

    except Exception as e:
        st.error(f"⚠️ خطأ: {e}")
        time.sleep(10)
        
