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
            balance = self.exchange.fetch_balance()
            total = float(balance.get('total', {}).get('USDT', 0))
            if total == 0: # محاولة ثانية لو الرصيد في السبوت
                bal_spot = self.exchange.fetch_balance({'type': 'spot'})
                total = float(bal_spot.get('total', {}).get('USDT', 0))
            return total
        except: return 0.0

    def run_automated_logic(self, balance):
        self.is_running = True
        initial_bal = balance
        target = initial_bal * 1.10
        symbol = 'BTC/USDT:USDT'
        
        yield f"🚀 انطلق البوت | الرصيد: ${initial_bal:.2f} | الهدف: ${target:.2f}"
        
        while self.is_running:
            try:
                curr_bal = self.get_total_balance()
                if curr_bal >= target:
                    yield "✅ تم تحقيق ربح 10%! إغلاق الجلسة."
                    self.is_running = False ; break
                
                bars = self.exchange.fetch_ohlcv(symbol, timeframe='1m', limit=20)
                df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
                ema = df['c'].ewm(span=10, adjust=False).mean().iloc[-1]
                price = df['c'].iloc[-1]

                if price > ema:
                    yield f"📈 إشارة صعود.. تنفيذ شراء على {symbol}"
                    qty = (curr_bal * 10 * 0.9) / price # رافعة 10x
                    self.exchange.create_market_buy_order(symbol, self.exchange.amount_to_precision(symbol, qty))
                elif price < ema:
                    yield f"📉 إشارة هبوط.. تنفيذ بيع على {symbol}"
                    qty = (curr_bal * 10 * 0.9) / price
                    self.exchange.create_market_sell_order(symbol, self.exchange.amount_to_precision(symbol, qty))
            except Exception as e:
                yield f"⚠️ تنبيه: {str(e)}"
            time.sleep(15)
            
