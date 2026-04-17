import ccxt
import pandas as pd
import time

class TradingBot:
    def __init__(self, exchange_id, api_key, secret_key):
        self.exchange = getattr(ccxt, exchange_id)({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
            'options': {'adjustForTimeDifference': True} 
        })
        self.is_running = False

    def get_total_balance(self):
        """Standardized function to fetch balance from Spot and Futures"""
        try:
            # 1. Fetch Spot Balance
            spot_bal = self.exchange.fetch_balance({'type': 'spot'})
            s_usdt = float(spot_bal.get('total', {}).get('USDT', 0))
            
            # 2. Fetch Futures Balance (Swap)
            swap_bal = self.exchange.fetch_balance({'type': 'swap'})
            f_usdt = float(swap_bal.get('total', {}).get('USDT', 0))
            
            # Return the one that has money (Priority to Spot as per user)
            return s_usdt if s_usdt >= 5 else f_usdt
        except:
            return 0.0

    def run_automated_logic(self, balance):
        self.is_running = True
        initial_bal = balance
        target = initial_bal * 1.10
        
        # Decide Market Type automatically
        spot_val = self.get_total_balance()
        market_type = 'spot' if spot_val >= 5 else 'swap'
        symbol = 'BTC/USDT' if market_type == 'spot' else 'BTC/USDT:USDT'
        
        yield f"🚀 Logic Started on {market_type.upper()}! Target: ${target:.2f}"
        
        while self.is_running:
            try:
                curr_bal = self.get_total_balance()
                yield f"💰 Balance: ${curr_bal:.2f} | Profit: ${curr_bal - initial_bal:.2f}"

                if curr_bal >= target:
                    yield "✅ Target Reached! Closing session."
                    self.is_running = False ; break

                # Technical Analysis
                bars = self.exchange.fetch_ohlcv(symbol.replace(':USDT',''), timeframe='1m', limit=15)
                df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
                ema = df['c'].ewm(span=10, adjust=False).mean().iloc[-1]
                price = df['c'].iloc[-1]

                # Execution
                qty = (curr_bal * 0.95) / price
                precise_qty = self.exchange.amount_to_precision(symbol, qty)
                params = {'type': market_type}

                if price > ema:
                    yield f"📈 BUY Signal on {symbol}"
                    self.exchange.create_market_buy_order(symbol, precise_qty, params)
                elif price < ema:
                    yield f"📉 SELL Signal on {symbol}"
                    self.exchange.create_market_sell_order(symbol, precise_qty, params)

            except Exception as e:
                yield f"⚠️ Alert: {str(e)}"
            time.sleep(20)
            
