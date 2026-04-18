import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime

# --- ⚙️ إعدادات محرك الأرباح التراكمية ---
SYMBOLS = ['ORDI_USDT', 'BTC_USDT', 'ETH_USDT', 'SOL_USDT', 'XRP_USDT', 'SUI_USDT', 'PEPE_USDT']
MAX_TRADES = 5           
LEVERAGE = 5             
RISK_PER_TRADE = 0.18    # 18% من الرصيد لكل صفقة
TP_TARGET = 0.02         # جني ربح تلقائي عند 2% (10% مع الرافعة)

st.set_page_config(page_title="Compounding Sniper", layout="wide")
st.title("💰 بوت الأرباح التراكمية - النسخة النهائية")

if 'running' not in st.session_state: st.session_state.running = False

with st.sidebar:
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 بدء التشغيل"): st.session_state.running = True
    if st.button("🛑 إيقاف"): st.session_state.running = False

if st.session_state.running and api_key and api_secret:
    try:
        mexc = ccxt.mexc({
            'apiKey': api_key, 'secret': api_secret,
            'options': {'defaultType': 'future'}, 'enableRateLimit': True
        })

        while st.session_state.running:
            # 1. حل مشكلة fetchBalance (جلب الرصيد المتاح فقط)
            account_data = mexc.fetch_balance()
            # الوصول المباشر للرصيد المتاح لتجنب خطأ "self method"
            available_bal = float(account_data['info']['data']['availableBalance'])
            
            # 2. فحص الصفقات
            pos = mexc.fetch_positions()
            active_p = [p for p in pos if float(p.get('contracts', 0)) != 0]
            current_count = len(active_p)
            active_names = [p['symbol'] for p in active_p]

            st.write(f"💵 الرصيد المتاح للتراكم: {available_bal:.2f} USDT | الصفقات: {current_count}/{MAX_TRADES}")

            for symbol in SYMBOLS:
                if current_count >= MAX_TRADES: break
                
                if symbol not in active_names:
                    try:
                        ohlcv = mexc.fetch_ohlcv(symbol, timeframe='1m', limit=20)
                        df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                        price = df['c'].iloc[-1]
                        
                        # حساب RSI سريع
                        delta = df['c'].diff()
                        rsi = 100 - (100 / (1 + (delta.clip(lower=0).mean() / -delta.clip(upper=0).mean())))

                        if rsi <= 35 or rsi >= 65:
                            side = 'buy' if rsi <= 35 else 'sell'
                            
                            # حساب حجم الصفقة التراكمي
                            trade_val = available_bal * RISK_PER_TRADE
                            qty = (trade_val * LEVERAGE) / price
                            formatted_qty = float(mexc.amount_to_precision(symbol, qty))

                            # ضبط الرافعة والمعاملات
                            try:
                                mexc.set_leverage(LEVERAGE, symbol, {'openType': 2, 'positionType': 1 if side == 'buy' else 2})
                            except: pass

                            # تنفيذ الصفقة ووضع هدف ربح آلي
                            mexc.create_market_order(symbol, side, formatted_qty)
                            
                            # وضع أمر جني الربح (TP) فوراً لضمان التراكم
                            tp_price = price * (1 + TP_TARGET) if side == 'buy' else price * (1 - TP_TARGET)
                            mexc.create_order(symbol, 'LIMIT', 'sell' if side == 'buy' else 'buy', formatted_qty, tp_price, {'reduceOnly': True})
                            
                            st.success(f"🎯 صفقة تراكمية لـ {symbol} بمبلغ {trade_val:.2f}$")
                            current_count += 1
                    except: continue

            time.sleep(20)

    except Exception as e:
        st.error(f"⚠️ خطأ: {e}")
        time.sleep(15)
        
