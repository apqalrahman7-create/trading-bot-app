import ccxt
import time
import pandas as pd

class TradingBot:
    def __init__(self, exchange_id, api_key, secret_key):
        self.exchange = getattr(ccxt, exchange_id)({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'} # لضمان العمل على العقود الآجلة
        })
        
        self.min_wallet_limit = 10.0      
        self.max_wallet_limit = 2500.0    
        self.profit_target_pct = 0.10     
        self.is_running = False

    def get_total_balance(self):
        try:
            # تحديث لجلب الرصيد المتاح للتداول في العقود الآجلة
            balance = self.exchange.fetch_balance()
            return float(balance['total'].get('USDT', 0))
        except Exception as e:
            print(f"Connection Error: {e}")
            return 0

    def get_active_markets(self):
        try:
            self.exchange.load_markets()
            # استهداف العملات الأكثر سيولة مقابل USDT
            symbols = [s for s in self.exchange.symbols if '/USDT' in s and ':' in s]
            return symbols[:40] 
        except:
            return ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']

    def analyze_market(self, symbol):
        try:
            bars = self.exchange.fetch_ohlcv(symbol, timeframe='5m', limit=30)
            df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
            df['ema_fast'] = df['c'].ewm(span=7, adjust=False).mean()
            df['ema_slow'] = df['c'].ewm(span=21, adjust=False).mean()
            
            if df['ema_fast'].iloc[-1] > df['ema_slow'].iloc[-1]: return 'LONG'
            if df['ema_fast'].iloc[-1] < df['ema_slow'].iloc[-1]: return 'SHORT'
            return 'WAIT'
        except: return 'ERROR'

    def execute_trade(self, symbol, side, amount_usdt):
        """تنفيذ الصفقة تلقائياً بأمر السوق"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            price = ticker['last']
            amount_crypto = amount_usdt / price
            
            order_side = 'buy' if side == 'LONG' else 'sell'
            print(f"!!! Opening {side} on {symbol} !!!")
            return self.exchange.create_market_order(symbol, order_side, amount_crypto)
        except Exception as e:
            print(f"Trade Failed: {e}")
            return None

    def start_fully_automated_trading(self):
        self.is_running = True
        symbols = self.get_market_symbols()
        initial_balance = self.get_total_balance()
        target_balance = initial_balance * (1 + self.profit_target_pct)
        
        print(f"--- System Live | Balance: ${initial_balance} | Goal: ${target_balance} ---")

        while self.is_running:
            current_balance = self.get_total_balance()
            
            if current_balance >= target_balance:
                print("10% Goal Reached! Closing session.")
                break

            for symbol in symbols:
                if not self.is_running: break
                
                signal = self.analyze_market(symbol)
                print(f"Scanning {symbol}: {signal}")

                # التأكد من الرصيد والحدود (10$ إلى 2500$)
                budget = min(current_balance, self.max_wallet_limit)
                
                if signal in ['LONG', 'SHORT'] and budget >= self.min_wallet_limit:
                    self.execute_trade(symbol, signal, budget)
                    time.sleep(600) # مراقبة الصفقة لمدة 10 دقائق
                    break

                time.sleep(1.5)
            time.sleep(30)
        self.is_running = False
        
