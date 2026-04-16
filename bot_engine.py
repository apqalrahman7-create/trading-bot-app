import ccxt
import time
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta

class TradingBot:
    def __init__(self, exchange_id, api_key, secret_key):
        self.exchange = getattr(ccxt, exchange_id)({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap' # Set to 'swap' for Futures or 'spot' for Spot trading
            }
        })
        
        # Configuration for your $17.5 balance
        self.max_capital_limit = 2500.0
        self.min_order_size = 11.0  # Safe margin above $10 minimum
        self.profit_target_pct = 0.10 # 10% Target
        self.leverage = 5            # Leverage for Futures (if applicable)
        self.is_running = False

    def get_wallet_balance(self):
        try:
            balance = self.exchange.fetch_balance()
            return balance['total'].get('USDT', 0)
        except Exception as e:
            print(f"Balance Fetch Error: {e}")
            return 0

    def get_market_symbols(self):
        """Scan top active USDT pairs in the market"""
        try:
            self.exchange.load_markets()
            symbols = [s for s in self.exchange.symbols if '/USDT' in s and ':' not in s]
            return symbols[:40] # Scan top 40 pairs for opportunities
        except:
            return ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'AVAX/USDT']

    def technical_analysis(self, symbol):
        """Multi-indicator market analysis (EMA + RSI)"""
        try:
            bars = self.exchange.fetch_ohlcv(symbol, timeframe='5m', limit=50)
            df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Technical Indicators
            df['RSI'] = ta.rsi(df['close'], length=14)
            df['EMA'] = ta.ema(df['close'], length=10)
            
            last = df.iloc[-1]
            
            # Logic: Price > EMA (Uptrend) and RSI < 60 (Not overbought)
            if last['close'] > last['EMA'] and last['RSI'] < 60:
                return 'BUY_SIGNAL'
            return 'WAIT'
        except:
            return 'ERROR'

    def execute_market_order(self, symbol, side, amount_usdt):
        """Execute real-time market orders on MEXC"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            price = ticker['last']
            amount_crypto = amount_usdt / price
            
            print(f"!!! Executing {side} order for {symbol} at {price} !!!")
            return self.exchange.create_market_order(symbol, side, amount_crypto)
        except Exception as e:
            print(f"Order Execution Failed: {e}")
            return None

    def start_automated_session(self):
        """Main loop to scan and trade automatically"""
        self.is_running = True
        active_symbols = self.get_market_symbols()
        
        print("--- Automated Market Scanner Started ---")
        
        while self.is_running:
            for symbol in active_symbols:
                if not self.is_running: break
                
                print(f"Scanning: {symbol}...")
                signal = self.technical_analysis(symbol)
                
                current_balance = self.get_wallet_balance()
                
                if signal == 'BUY_SIGNAL' and current_balance >= self.min_order_size:
                    print(f"MATCH FOUND: {symbol}. Initializing Trade.")
                    self.execute_market_order(symbol, 'buy', self.min_order_size)
                    
                    # Pause scanning to monitor the trade (10 minutes)
                    time.sleep(600) 
                    break 

                time.sleep(1.5) # Anti-ban delay
            
            time.sleep(20) # Gap between full market scans

    def stop_session(self):
        self.is_running = False
        print("Bot session stopped.")
        
