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

    def get_active_balance(self):
        """Scan all wallets and identify where the funds are located"""
        try:
            # 1. Check Futures Wallet (Swap)
            swap_bal = self.exchange.fetch_balance({'type': 'swap'})
            swap_usdt = float(swap_bal.get('total', {}).get('USDT', 0))
            if swap_usdt >= 5:
                return swap_usdt, 'futures', 'BTC/USDT:USDT'

            # 2. Check Spot Wallet (If Futures is empty)
            spot_bal = self.exchange.fetch_balance({'type': 'spot'})
            spot_usdt = float(spot_bal.get('total', {}).get('USDT', 0))
            if spot_usdt >= 5:
                return spot_usdt, 'spot', 'BTC/USDT'
            
            return max(swap_usdt, spot_usdt), None, None
        except:
            return 0.0, None, None

    def get_total_balance(self):
        """Helper function to display balance on the UI"""
        bal, _, _ = self.get_active_balance()
        return bal

    def run_automated_logic(self, balance):
        self.is_running = True
        # Detect where the money is before starting
        current_bal, market_type, symbol = self.get_active_balance()
        
        if not market_type:
            yield "❌ No sufficient balance found in Spot or Futures ($5 min)."
            return

        initial_bal = current_bal
        target = initial_bal * 1.10
        yield f"🚀 Bot Started on {market_type.upper()}! Target: ${target:.2f}"
        
        while self.is_running:
            try:
                # Update current balance and profit tracking
                current_bal, _, _ = self.get_active_balance()
                profit = current_bal - initial_bal
                yield f"💰 Balance: ${current_bal:.2f} | Profit: ${profit:.2f}"

                if current_bal >= target:
                    yield "✅ 10% Profit Achieved! Session Closed."
                    self.is_running = False ; break

                # Technical Analysis (EMA Strategy)
                # Cleaning symbol for OHLCV fetch
                clean_symbol = symbol.split(':')[0] if ':' in symbol else symbol
                bars = self.exchange.fetch_ohlcv(clean_symbol, timeframe='1m', limit=15)
                df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
                ema = df['c'].ewm(span=10, adjust=False).mean().iloc[-1]
                price = df['c'].iloc[-1]

                # Calculation for Order Size
                # Futures use 10x leverage | Spot uses 1x (Direct balance)
                lev = 10 if market_type == 'futures' else 1
                qty = (current_bal * lev * 0.2) / price
                precise_qty = self.exchange.amount_to_precision(symbol, qty)

                # Execute Order based on detected market
                params = {'type': 'swap'} if market_type == 'futures' else {'type': 'spot'}
                
                if price > ema:
                    yield f"📈 BUY Signal detected on {market_type.upper()}"
                    self.exchange.create_market_buy_order(symbol, precise_qty, params)
                elif price < ema:
                    yield f"📉 SELL Signal detected on {market_type.upper()}"
                    self.exchange.create_market_sell_order(symbol, precise_qty, params)

            except Exception as e:
                yield f"⚠️ Alert: {str(e)}"
            
            time.sleep(20)
            
