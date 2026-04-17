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
                'defaultType': 'swap', 
                'adjustForTimeDifference': True
            }
        })
        self.is_running = False

    def get_total_balance(self):
        """Standard function to display balance correctly"""
        try:
            balance = self.exchange.fetch_balance()
            return float(balance.get('total', {}).get('USDT', 0))
        except:
            return 0.0

    def run_automated_logic(self, balance):
        self.is_running = True
        initial_bal = balance
        target = initial_bal * 1.10
        symbol = 'BTC/USDT:USDT'
        
        yield f"🚀 Session Started! Initial: ${initial_bal:.2f} | Target: ${target:.2f}"
        
        while self.is_running:
            try:
                curr_bal = self.get_total_balance()
                profit = curr_bal - initial_bal
                yield f"💰 Current Balance: ${curr_bal:.2f} | Profit: ${profit:.2f}"

                if curr_bal >= target:
                    yield "✅ 10% Profit Achieved! Closing session."
                    self.is_running = False ; break

                # Technical Analysis (EMA)
                bars = self.exchange.fetch_ohlcv(symbol, timeframe='1m', limit=15)
                df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
                ema = df['c'].ewm(span=10, adjust=False).mean().iloc[-1]
                price = df['c'].iloc[-1]

                # REAL TRADE EXECUTION
                qty = (curr_bal * 10 * 0.2) / price # Leverage 10x | Risk 20%
                precise_qty = self.exchange.amount_to_precision(symbol, qty)

                if price > ema:
                    yield f"📈 Bullish Signal! Opening LONG on {symbol}"
                    self.exchange.create_market_buy_order(symbol, precise_qty)
                elif price < ema:
                    yield f"📉 Bearish Signal! Opening SHORT on {symbol}"
                    self.exchange.create_market_sell_order(symbol, precise_qty)

            except Exception as e:
                yield f"⚠️ Alert: {str(e)}"
            
            time.sleep(20)
            
