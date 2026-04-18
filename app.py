import streamlit as st
import ccxt
import pandas as pd
import time

# --- ⚙️ إعدادات الربح التراكمي الذكي ---
SYMBOLS = ['ORDI_USDT', 'BTC_USDT', 'ETH_USDT', 'SOL_USDT', 'XRP_USDT']
MAX_TRADES = 4
LEVERAGE = 5
# استخدام 15% فقط من الرصيد لترك مساحة للهامش (Margin) ومنع التنبيه
RISK_PER_TRADE = 0.15 
TP_PERCENT = 0.015  # ربح 1.5%

st.title("💰 قناص الربح التراكمي المستقر")

if 'running' not in st.session_state: st.session_state.running = False

with st.sidebar:
    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("Secret Key", type="password")
    if st.button("🚀 تشغيل"): st.session_state.running = True
    if st.button("🛑 إيقاف"): st.session_state.running = False

if st.session_state.running and api_key and api_secret:
    try:
        # اتصال احترافي مع ضبط MEXC
        mexc = ccxt.mexc({
            'apiKey': api_key, 
            'secret': api_secret, 
            'options': {'defaultType': 'future'},
            'enableRateLimit': True
        })

        while st.session_state.running:
            # 1. جلب البيانات (حل مشكلة التنبيه)
            account = mexc.fetch_balance()
            # قراءة الرصيد المتاح فعلياً من داخل بيانات MEXC
            free_balance = float(account['info']['data']['availableBalance'])
            
            pos = mexc.fetch_positions()
            active_p = [p for p in pos if float(p.get('contracts', 0)) != 0]
            current_count = len(active_p)
            active_names = [p['symbol'] for p in active_p]

            st.write(f"💵 رصيدك المتاح: {free_balance:.2f} USDT | الصفقات: {current_count}/{MAX_TRADES}")

            for symbol in SYMBOLS:
                if current_count >= MAX_TRADES: break
                
                if symbol not in active_names:
                    try:
                        ticker = mexc.fetch_ticker(symbol)
                        price = float(ticker['last'])
                        
                        # حساب حجم الصفقة التراكمي (تجنب التنبيه عبر ترك مساحة 5% للأمان)
                        entry_usd = free_balance * RISK_PER_TRADE
                        qty = (entry_usd * LEVERAGE) / price
                        
                        # تقريب الكمية حسب قوانين المنصة
                        formatted_qty = float(mexc.amount_to_precision(symbol, qty))

                        if formatted_qty > 0:
                            # تنفيذ الصفقة مع ضبط الهامش لعدم ظهور تنبيه "Position Type"
                            try:
                                mexc.set_leverage(LEVERAGE, symbol, {'openType': 2})
                            except: pass
                            
                            mexc.create_market_order(symbol, 'buy', formatted_qty)
                            
                            # وضع أمر جني الربح فوراً (قنص)
                            tp_price = price * (1 + TP_PERCENT)
                            mexc.create_order(symbol, 'LIMIT', 'sell', formatted_qty, tp_price, {'reduceOnly': True})
                            
                            st.success(f"🎯 قنص تراكمي: {symbol} بمبلغ {entry_usd:.2f}$")
                            current_count += 1
                            active_names.append(symbol)
                    except Exception as e:
                        continue

            time.sleep(20) # مهلة كافية لضمان استقرار الاتصال
    except Exception as e:
        st.error(f"⚠️ تنبيه من المنصة: {e}")
        time.sleep(15)
        
