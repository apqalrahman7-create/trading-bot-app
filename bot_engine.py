import ccxt
import time
import pandas as pd

class TradingBot:
    def __init__(self, exchange_id, api_key, secret_key):
        self.exchange = getattr(ccxt, exchange_id)({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap', # للبحث في العقود الآجلة
                'adjustForTimeDifference': True # حل مشكلة توقيت السيرفر
            }
        })
        self.is_running = False
        self.leverage = 10

    def get_total_balance(self):
        """كود إجباري لجلب الرصيد الحقيقي من MEXC"""
        try:
            # 1. محاولة جلب رصيد العقود الآجلة
            balance = self.exchange.fetch_balance({'type': 'swap'})
            res = float(balance.get('total', {}).get('USDT', 0))
            
            # 2. إذا كان صفراً، ابحث في السبوت (Spot) تلقائياً
            if res == 0:
                spot_bal = self.exchange.fetch_balance({'type': 'spot'})
                res = float(spot_bal.get('total', {}).get('USDT', 0))
                
            return res
        except Exception as e:
            print(f"Error connecting to MEXC: {e}")
            return 0.0

    def run_automated_logic(self, balance):
        self.is_running = True
        initial_balance = balance
        target_profit = initial_balance * 1.10 # هدف 10%
        
        yield f"🚀 انطلق البوت! الرصيد المكتشف: ${initial_balance:.2f}"
        
        symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT']
        
        while self.is_running:
            # تحديث الرصيد الحالي
            current_bal = self.get_total_balance()
            
            # فحص تحقيق الهدف (10% ربح)
            if current_bal >= target_profit:
                yield "✅ تم تحقيق ربح 10%! جاري إغلاق الجلسة."
                self.is_running = False
                break
                
            for symbol in symbols:
                try:
                    # تحليل السوق
                    bars = self.exchange.fetch_ohlcv(symbol, timeframe='5m', limit=20)
                    df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
                    ema = df['c'].ewm(span=10, adjust=False).mean().iloc[-1]
                    price = df['c'].iloc[-1]

                    # حساب كمية الصفقة بدقة (تجنب خطأ InvalidOrder)
                    qty = (current_bal * self.leverage * 0.9) / price
                    precise_qty = float(self.exchange.amount_to_precision(symbol, qty))

                    # تنفيذ التداول الحقيقي
                    if price > ema:
                        yield f"📈 شراء (Long) على {symbol}.."
                        self.exchange.create_market_buy_order(symbol, precise_qty)
                    elif price < ema:
                        yield f"📉 بيع (Short) على {symbol}.."
                        self.exchange.create_market_sell_order(symbol, precise_qty)
                        
                except Exception as e:
                    yield f"⚠️ تنبيه: {str(e)}"
                time.sleep(2)
            
            time.sleep(15)
            
