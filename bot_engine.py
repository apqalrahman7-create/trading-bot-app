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
                'defaultType': 'spot',  # التركيز على محفظة الفوري (Spot)
                'adjustForTimeDifference': True
            }
        })
        self.is_running = False

    def get_total_balance(self):
        """جلب رصيد الـ USDT المتاح في محفظة الفوري"""
        try:
            balance = self.exchange.fetch_balance({'type': 'spot'})
            # جلب الرصيد المتاح للتداول (Free Balance)
            usdt_free = float(balance.get('free', {}).get('USDT', 0))
            return usdt_free
        except Exception as e:
            print(f"Error fetching spot balance: {e}")
            return 0.0

    def run_automated_logic(self, balance):
        self.is_running = True
        initial_bal = balance
        target = initial_bal * 1.10  # هدف الربح 10%
        symbol = 'BTC/USDT'  # رمز التداول الفوري
        
        yield f"🚀 Spot Session Started! Balance: ${initial_bal:.2f} | Target: ${target:.2f}"
        
        while self.is_running:
            try:
                curr_bal = self.get_total_balance()
                profit = curr_bal - initial_bal
                yield f"💰 Current Balance: ${curr_bal:.2f} | Net Profit: ${profit:.2f}"

                if curr_bal >= target:
                    yield "✅ 10% Profit Achieved in Spot! Closing session."
                    self.is_running = False ; break

                # تحليل الاتجاه (EMA)
                bars = self.exchange.fetch_ohlcv(symbol, timeframe='1m', limit=20)
                df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
                ema = df['c'].ewm(span=10, adjust=False).mean().iloc[-1]
                price = df['c'].iloc[-1]

                # في التداول الفوري (Spot)، نشتري فقط عندما يكون السعر صاعداً
                if price > ema:
                    # حساب الكمية (استخدام 95% من الرصيد المتاح لترك هامش للرسوم)
                    amount_usdt = curr_bal * 0.95
                    qty = amount_usdt / price
                    precise_qty = self.exchange.amount_to_precision(symbol, qty)
                    
                    yield f"📈 Bullish Signal! Executing BUY on {symbol}"
                    self.exchange.create_market_buy_order(symbol, precise_qty)
                
                elif price < ema:
                    # فحص إذا كان لدينا عملات (BTC) لبيعها وجني الأرباح
                    bal_data = self.exchange.fetch_balance({'type': 'spot'})
                    btc_qty = float(bal_data.get('free', {}).get('BTC', 0))
                    
                    if btc_qty > 0.0001:
                        yield f"📉 Price below EMA. Selling BTC to secure profit."
                        self.exchange.create_market_sell_order(symbol, btc_qty)

            except Exception as e:
                yield f"⚠️ Alert: {str(e)}"
            
            time.sleep(20)
            
