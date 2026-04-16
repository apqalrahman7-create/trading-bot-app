import streamlit as st
import ccxt
import time
import pandas as pd

class SmartTradingBot:
    def __init__(self, api_key, secret_key):
        self.exchange = ccxt.mexc({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
        })
        self.is_running = False

    def get_balances(self):
        try:
            # جلب رصيد السبوت والعقود الآجلة معاً
            spot = self.exchange.fetch_balance({'type': 'spot'})['total'].get('USDT', 0)
            swap = self.exchange.fetch_balance({'type': 'swap'})['total'].get('USDT', 0)
            return float(spot), float(swap)
        except: return 0.0, 0.0

    def execute_trade(self, market_type, symbol, side, amount):
        """تنفيذ الصفقة في السوق المحدد"""
        try:
            params = {'type': 'swap'} if market_type == 'futures' else {'type': 'spot'}
            if side == 'buy':
                return self.exchange.create_market_buy_order(symbol, amount, params)
            else:
                return self.exchange.create_market_sell_order(symbol, amount, params)
        except Exception as e:
            return f"Error: {str(e)}"

    def run_automated_logic(self):
        self.is_running = True
        spot_bal, swap_bal = self.get_balances()
        initial_total = spot_bal + swap_bal
        target_profit = initial_total * 1.10 # هدف 10%
        
        # تحديد الأسواق (السبوت والعقود الآجلة)
        spot_symbol = 'BTC/USDT'
        futures_symbol = 'BTC/USDT:USDT'
        
        yield f"🚀 انطلق البوت! إجمالي الرصيد: ${initial_total:.2f} | الهدف: ${target_profit:.2f}"

        while self.is_running:
            current_spot, current_swap = self.get_balances()
            current_total = current_spot + current_swap
            
            # عرض التحديث في الشاشة
            st.write(f"📊 الرصيد الحالي: ${current_total:.2f} | الربح المستهدف: ${target_profit:.2f}")

            # فحص جني الأرباح (10%)
            if current_total >= target_profit:
                yield "💰 مبروك! تم تحقيق هدف الـ 10%. جاري تصفية المراكز وإعادة الرصيد..."
                # (هنا تضاف دالة إغلاق كافة الصفقات المفتوحة)
                self.is_running = False
                break

            # --- تحليل السوق واتخاذ القرار ---
            try:
                bars = self.exchange.fetch_ohlcv(spot_symbol, timeframe='5m', limit=20)
                df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
                ema = df['c'].ewm(span=10, adjust=False).mean().iloc[-1]
                price = df['c'].iloc[-1]

                # إذا كانت الإشارة "شراء" والرصيد في السبوت
                if price > ema and current_spot > 10:
                    yield f"📈 إشارة صعود.. شراء في سوق السبوت (Spot) بـ ${current_spot:.2f}"
                    self.execute_trade('spot', spot_symbol, 'buy', (current_spot * 0.98) / price)
                
                # إذا كانت الإشارة "بيع/شورت" والرصيد في الآجلة
                elif price < ema and current_swap > 10:
                    yield f"📉 إشارة هبوط.. فتح صفقة Short في العقود الآجلة بـ ${current_swap:.2f}"
                    self.execute_trade('futures', futures_symbol, 'sell', (current_swap * 0.98) / price)

            except Exception as e:
                yield f"⚠️ تنبيه: {str(e)}"
            
            time.sleep(30) # فحص كل 30 ثانية

# --- واجهة Streamlit ---
st.title("🤖 بوت MEXC الذكي (سبوت + فيوتشر)")
# (أضف هنا حقول إدخال الـ API والزر كما في الكود السابق)
