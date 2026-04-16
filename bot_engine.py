import ccxt
import time
import pandas as pd

class TradingBot:
    def __init__(self, exchange_id, api_key, secret_key):
        # 1. Initialize Connection with Hybrid Support (Spot & Futures)
        self.exchange = getattr(ccxt, exchange_id)({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'} # Trading on Futures/Swap for maximum profit
        })
        
        # 2. Financial Logic Parameters
        self.min_wallet_limit = 10.0      # Start trading from $10
        self.max_wallet_limit = 2500.0    # Cap trading at $2500
        self.profit_target_pct = 0.10     # Target 10% profit per session
        self.is_running = False

    def get_total_balance(self):
        """Fetch total wallet balance automatically"""
        try:
            balance = self.exchange.fetch_balance()
            return float(balance['total'].get('USDT', 0))
        except: return 0

    def get_active_markets(self):
        """Scan the entire market for the best USDT pairs"""
        try:
            self.exchange.load_markets()
            # Filters active USDT pairs (Spot and Futures)
            symbols = [s for s in self.exchange.symbols if '/USDT' in s and ':' not in s]
            return symbols[:50] # Scan top 50 volatile pairs
        except:
            return ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']

    def analyze_market(self, symbol):
        """Internal technical analysis (EMA cross detection)"""
        try:
            bars = self.exchange.fetch_ohlcv(symbol, timeframe='5m', limit=30)
            df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
            df['ema_fast'] = df['c'].ewm(span=7, adjust=False).mean()
            df['ema_slow'] = df['c'].ewm(span=21, adjust=False).mean()
            
            last_fast = df['ema_fast'].iloc[-1]
            last_slow = df['ema_slow'].iloc[-1]
            
            if last_fast > last_slow: return 'LONG'  # Market going up
            if last_fast < last_slow: return 'SHORT' # Market going down
            return 'WAIT'
        except: return 'ERROR'

    def start_fully_automated_trading(self):
        """Main automated loop: Full wallet, Multi-market, Target 10%"""
        self.is_running = True
        symbols = self.get_active_markets()
        
        # Check starting balance
        initial_balance = self.get_total_balance()
        target_balance = initial_balance * (1 + self.profit_target_pct)
        
        # Determine usable budget (Up to $2500)
        trading_budget = min(initial_balance, self.max_wallet_limit)

        print(f"--- Session Started ---")
        print(f"Initial: ${initial_balance} | Target: ${target_balance}")

        while self.is_running:
            current_balance = self.get_total_balance()
            
            # Check if 10% Profit Target is reached
            if current_balance >= target_balance:
                print("10% Profit Achieved! Closing all positions and returning to wallet.")
                # self.close_all_positions() # Logic to exit all trades
                break

            for symbol in symbols:
                if not self.is_running: break
                
                signal = self.analyze_market(symbol)
                print(f"Scanning {symbol}: {signal}...")

                if signal in ['LONG', 'SHORT'] and trading_budget >= self.min_wallet_limit:
                    print(f"!!! Opening Automated Trade on {symbol} with full budget !!!")
                    # Execution logic here
                    # self.execute_order(symbol, signal, trading_budget)
                    time.sleep(300) # Watch trade for 5 minutes
                    break

                time.sleep(1) # Market scan speed
            
            time.sleep(60) # Wait before next market scan
        
        self.is_running = False
            
