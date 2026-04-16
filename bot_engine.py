import ccxt
import time
import pandas as pd

class TradingBot:
    def __init__(self, exchange_id, api_key, secret_key):
        self.exchange = getattr(ccxt, exchange_id)({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'} # العقود الآجلة
        })
        self.is_running = False
        self.leverage = 5 # رافعة مالية افتراضية

    def get_total_balance(self):
        try:
            balance = self.exchange.fetch_balance()
            return float(balance['total'].get('USDT', 0))
        except: return 0.0

    def run_automated_logic(self, balance):
        self.is_running = True
        target_profit = balance * 1.10
        usable_budget = min(balance, 2500.0)
        
        yield f"🚀 Session Started! Budget: ${usable_budget} | Target: ${target_profit:.2f}"
        
        # قائمة العملات للمسح الشامل
        symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'AVAX/USDT:USDT', 'LTC/USDT:USDT']
        
        while self.is_running:
            for symbol in symbols:
                yield f"🔍 Scanning: {symbol}..."
                try:
                    # تحليل فني مبسط للسعر
                    bars = self.exchange.fetch_ohlcv(symbol, timeframe='5m', limit=20)
                    df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
                    df['ema'] = df['c'].ewm(span=10, adjust=False).mean()
                    
                    price = df['c'].iloc[-1]
                    ema = df['ema'].iloc[-1]

                    if price > ema:
                        yield f"📈 Bullish on {symbol}. Potential LONG."
                    elif price < ema:
                        yield f"📉 Bearish on {symbol}. Potential SHORT."
                except: pass
                time.sleep(2)
            
            # فحص الوصول للهدف (10% ربح)
            if self.get_total_balance() >= target_profit:
                yield "✅ 10% Profit Target Achieved! Session Closed."
                break
            time.sleep(10)
            
