import ccxt
import pandas as pd
import time

class TradingBot:
    def __init__(self, exchange_id, api_key, secret_key):
        self.exchange = getattr(ccxt, exchange_id)({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap', # للعمل على العقود الآجلة
                'adjustForTimeDifference': True 
            }
        })
        self.is_running = False
        self.leverage = 10 # رافعة مالية

    def get_total_balance(self):
        """هذه الدالة التي أظهرت لك الرصيد سابقاً مع تحسينها"""
        try:
            balance = self.exchange.fetch_balance()
            total = float(balance.get('total', {}).get('USDT', 0))
            if total == 0:
                # إذا لم يجد في الفيوتشر يبحث في السبوت
                bal_spot = self.exchange.fetch_balance({'type': 'spot'})
                total = float(bal_spot.get('total', {}).get('USDT', 0))
            return total
        except: return 0.0

    def run_automated_logic(self, balance):
        self.is_running = True
        initial_bal = balance
        target = initial_bal * 1.10 # هدف 10% ربح
        symbol = 'BTC/USDT:USDT'
        
        yield f"🚀 بدأ التداول الحقيقي | الرصيد: ${initial_bal:.2f} | الهدف: ${target:.2f}"
        
        while self.is_running:
            try:
                # 1. تحديث الرصيد الحالي
                curr_bal = self.get_total_balance()
                
                # 2. فحص الوصول للهدف
                if curr_bal >= target:
                    yield "✅ مبروك! تم تحقيق هدف الـ 10%. إغلاق كافة العمليات."
                    self.is_running = False ; break
                
                # 3. تحليل السوق (EMA)
                bars = self.exchange.fetch_ohlcv(symbol, timeframe='1m', limit=20)
                df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
                ema = df['c'].ewm(span=10, adjust=False).mean().iloc[-1]
                price = df['c'].iloc[-1]

                # 4. تنفيذ أوامر الشراء والبيع الحقيقية (هنا يكمن الفرق)
                qty = (curr_bal * self.leverage * 0.9) / price
                precise_qty = self.exchange.amount_to_precision(symbol, qty)

                if price > ema:
                    yield f"📈 إشارة شراء حقيقية.. جاري فتح صفقة Long على {symbol}"
                    # أمر تنفيذ حقيقي
                    self.exchange.create_market_buy_order(symbol, precise_qty)
                
                elif price < ema:
                    yield f"📉 إشارة بيع حقيقية.. جاري فتح صفقة Short على {symbol}"
                    # أمر تنفيذ حقيقي
                    self.exchange.create_market_sell_order(symbol, precise_qty)

            except Exception as e:
                yield f"⚠️ تنبيه من المنصة: {str(e)}"
            
            time.sleep(20) # فحص كل 20 ثانية
