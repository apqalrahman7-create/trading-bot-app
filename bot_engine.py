import ccxt
import time
import pandas as pd

class TradingBot:
    def __init__(self, exchange_id, api_key, secret_key):
        self.exchange = getattr(ccxt, exchange_id)({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'} # تفعيل العقود الآجلة (Futures)
        })
        self.is_running = False
        self.leverage = 5 # تحديد الرافعة المالية (مثلاً 5x)

    def get_total_balance(self):
        """جلب رصيد المحفظة الخاص بالعقود الآجلة"""
        try:
            balance = self.exchange.fetch_balance()
            # في العقود الآجلة نبحث عن الرصيد المتاح (USDT)
            return float(balance['total'].get('USDT', 0))
        except: return 0.0

    def set_leverage(self, symbol):
        """تحديد الرافعة المالية للعملة قبل البدء"""
        try:
            self.exchange.set_leverage(self.leverage, symbol)
        except: pass

    def run_automated_logic(self, balance):
        self.is_running = True
        target_profit = balance * 1.10
        usable_budget = min(balance, 2500.0)
        
        yield f"🚀 Futures Session Started! Budget: ${usable_budget} | Leverage: {self.leverage}x | Target: ${target_profit:.2f}"
        
        # قائمة أزواج العقود الآجلة النشطة (لاحظ إضافة :USDT للرمز)
        symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'AVAX/USDT:USDT']
        
        while self.is_running:
            for symbol in symbols:
                if not self.is_running: break
                yield f"🔍 Analyzing Futures Market: {symbol}..."
                
                try:
                    self.set_leverage(symbol)
                    bars = self.exchange.fetch_ohlcv(symbol, timeframe='5m', limit=20)
                    df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
                    
                    # تحليل سريع (EMA Cross)
                    df['ema_fast'] = df['c'].ewm(span=7, adjust=False).mean()
                    df['ema_slow'] = df['c'].ewm(span=21, adjust=False).mean()
                    
                    last_f = df['ema_fast'].iloc[-1]
                    last_s = df['ema_slow'].iloc[-1]

                    if last_f > last_s:
                        yield f"🔥 Bullish Signal! Opening LONG on {symbol}"
                        # كود تنفيذ صفقة شراء (Long)
                    elif last_f < last_s:
                        yield f"📉 Bearish Signal! Opening SHORT on {symbol}"
                        # كود تنفيذ صفقة بيع (Short)
                        
                except Exception as e:
                    yield f"⚠️ Error analyzing {symbol}: {str(e)}"
                
                time.sleep(2)
            
            if self.get_total_balance() >= target_profit:
                yield "✅ 10% Profit Achieved in Futures! Closing session."
                break
            time.sleep(10)
            
