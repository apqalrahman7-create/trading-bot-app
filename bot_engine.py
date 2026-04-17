import ccxt
import pandas as pd
import time

class TradingBot:
    def __init__(self, exchange_id, api_key, secret_key):
        self.exchange = getattr(ccxt, exchange_id)({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap', 'adjustForTimeDifference': True}
        })
        self.is_running = False

    def get_total_balance(self):
        try:
            # محاولة جلب رصيد العقود الآجلة أولاً
            balance = self.exchange.fetch_balance({'type': 'swap'})
            res = float(balance.get('total', {}).get('USDT', 0))
            if res == 0:
                # محاولة جلب رصيد السبوت
                balance = self.exchange.fetch_balance({'type': 'spot'})
                res = float(balance.get('total', {}).get('USDT', 0))
            return res
        except Exception as e:
            return 0.0

    def run_automated_logic(self, initial_balance):
        self.is_running = True
        target = initial_balance * 1.10
        symbol = 'BTC/USDT:USDT'
        
        yield f"🚀 بدأت الجلسة الحقيقية | الرصيد: ${initial_balance:.2f} | الهدف: ${target:.2f}"
        
        while self.is_running:
            try:
                current_bal = self.get_total_balance()
                if current_bal >= target:
                    yield "✅ تم تحقيق الهدف! جاري الإغلاق..."
                    self.is_running = False ; break
                
                # تحليل السوق
                bars = self.exchange.fetch_ohlcv(symbol, timeframe='1m', limit=20)
                df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
                ema = df['c'].ewm(span=10, adjust=False).mean().iloc[-1]
                price = df['c'].iloc[-1]

                # تنفيذ صفقات حقيقية بـ 10% من المحفظة ورافعة 10x
                qty = (current_bal * 10 * 0.1) / price
                precise_qty = self.exchange.amount_to_precision(symbol, qty)

                if price > ema:
                    yield f"📈 شراء حقيقي على {symbol}..."
                    self.exchange.create_market_buy_order(symbol, precise_qty)
                elif price < ema:
                    yield f"📉 بيع حقيقي على {symbol}..."
                    self.exchange.create_market_sell_order(symbol, precise_qty)

            except Exception as e:
                yield f"⚠️ تنبيه: {str(e)}"
            time.sleep(20)
            
