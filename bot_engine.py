import ccxt
import time
import pandas as pd
from datetime import datetime, timedelta

class TradingBot:
    def __init__(self, exchange_id, api_key, secret_key):
        # Initialize Exchange Connection (Binance or MEXC)
        self.exchange = getattr(ccxt, exchange_id)({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        
        # Trading Constraints
        self.max_capital_limit = 2500.0  # Maximum trading capital
        self.min_order_size = 20.0      # Minimum order amount
        self.profit_target_pct = 0.10   # 10% Profit target
        self.is_running = False

    def get_wallet_balance(self):
        """Fetch real-time USDT balance from the exchange"""
        try:
            balance = self.exchange.fetch_balance()
            return balance['total'].get('USDT', 0)
        except Exception as e:
            print(f"Error fetching balance: {e}")
            return 0

    def fetch_market_data(self, symbol="BTC/USDT"):
        """Download real-time candlestick data for analysis"""
        bars = self.exchange.fetch_ohlcv(symbol, timeframe='5m', limit=50)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        return df

    def technical_analysis(self, df):
        """Automated Market Analysis using Moving Averages"""
        df['sma_short'] = df['close'].rolling(window=10).mean()
        df['sma_long'] = df['close'].rolling(window=30).mean()
        
        last_close = df['close'].iloc[-1]
        sma_short = df['sma_short'].iloc[-1]
        
        # Auto-Signal Logic
        if last_close > sma_short:
            return 'BUY'
        elif last_close < sma_short:
            return 'SELL'
        return 'HOLD'

    def execute_auto_trade(self, symbol, side, amount_usdt):
        """Execute real market orders automatically"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            price = ticker['last']
            amount_crypto = amount_usdt / price
            
            if side == 'BUY':
                print(f"Executing AUTO-BUY: {amount_usdt} USDT on {symbol}")
                return self.exchange.create_market_buy_order(symbol, amount_crypto)
            elif side == 'SELL':
                print(f"Executing AUTO-SELL: Returning funds to wallet for {symbol}")
                return self.exchange.create_market_sell_order(symbol, amount_crypto)
        except Exception as e:
            print(f"Trade Execution Error: {e}")
            return None

    def start_12h_session(self, symbol="BTC/USDT"):
        """Main automated loop: Runs for 12 hours and aims for 10% profit"""
        self.is_running = True
        
        # Calculate Target based on current balance (Max $2500)
        current_balance = self.get_wallet_balance()
        trading_budget = min(current_balance, self.max_limit)
        target_profit_amount = trading_budget * self.profit_target_pct
        
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=12)
        accumulated_profit = 0.0

        print(f"--- Session Started ---")
        print(f"Target: ${target_profit_amount} (10%) | Budget: ${trading_budget}")

        while datetime.now() < end_time and self.is_running:
            try:
                # 1. Real-time Analysis
                df = self.fetch_market_data(symbol)
                signal = self.technical_analysis(df)

                # 2. Automated Execution
                if signal == 'BUY' and trading_budget >= self.min_order_size:
                    self.execute_auto_trade(symbol, 'BUY', self.min_order_size)
                
                # 3. Check for Profit Target
                if accumulated_profit >= target_profit_amount:
                    print("10% Profit Target Reached! Closing session early.")
                    break

                time.sleep(300) # Analyze market every 5 minutes
                
            except Exception as e:
                print(f"Loop Error: {e}")
                time.sleep(60)

        # --- End of Session Logic ---
        print("12-Hour Session Completed. Returning all capital and profits to main wallet.")
        self.execute_auto_trade(symbol, 'SELL', 0) # Close any open positions
        self.is_running = False
      
