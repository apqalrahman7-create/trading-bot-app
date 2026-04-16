import ccxt
import time
import pandas as pd
from datetime import datetime, timedelta

class TradingBot:
    def __init__(self, exchange_id, api_key, secret_key):
        self.exchange = getattr(ccxt, exchange_id)({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        
        self.max_capital_limit = 2500.0  
        self.min_order_size = 10.0      
        self.profit_target_pct = 0.10   
        self.is_running = False

    def get_wallet_balance(self):
        """جلب رصيد الـ USDT المتاح حالياً"""
        try:
            balance = self.exchange.fetch_balance()
            return float(balance['total'].get('USDT', 0))
        except: return 0.0

    def sell_all_and_return_to_usdt(self, symbol="BTC/USDT"):
        """تحويل كافة العملات إلى USDT لإعادة الرصيد لأصله"""
        try:
            coin_symbol = symbol.split('/')[0] # استخراج رمز العملة مثل BTC
            balance = self.exchange.fetch_balance()
            amount_to_sell = balance['total'].get(coin_symbol, 0)
            
            if amount_to_sell > 0:
                print(f"إغلاق المركز: بيع {amount_to_sell} {coin_symbol} والعودة لـ USDT")
                return self.exchange.create_market_sell_order(symbol, amount_to_sell)
        except Exception as e:
            print(f"خطأ أثناء إعادة المال للأصل: {e}")
            return None

    def fetch_market_data(self, symbol="BTC/USDT"):
        bars = self.exchange.fetch_ohlcv(symbol, timeframe='5m', limit=50)
        return pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    def technical_analysis(self, df):
        df['sma_fast'] = df['close'].rolling(window=7).mean()
        df['sma_slow'] = df['close'].rolling(window=25).mean()
        
        if df['sma_fast'].iloc[-1] > df['sma_slow'].iloc[-1]: return 'BUY'
        elif df['sma_fast'].iloc[-1] < df['sma_slow'].iloc[-1]: return 'SELL'
        return 'HOLD'

    def start_12h_session(self, symbol="BTC/USDT"):
        """بدء جلسة تداول آلي تنتهي بإعادة الرصيد للمحفظة"""
        self.is_running = True
        
        # 1. التأكد من أن الرصيد يبدأ كـ USDT
        self.sell_all_and_return_to_usdt(symbol)
        time.sleep(2)
        
        start_balance = self.get_wallet_balance()
        target_amount = start_balance * (1 + self.profit_target_pct)
        end_time = datetime.now() + timedelta(hours=12)

        print(f"بدأت الجلسة. الرصيد الأولي: {start_balance}$. المستهدف: {target_amount}$")

        while datetime.now() < end_time and self.is_running:
            try:
                df = self.fetch_market_data(symbol)
                signal = self.technical_analysis(df)
                curr_usdt = self.get_wallet_balance()

                # تنفيذ الشراء بكامل السيولة المتاحة
                if signal == 'BUY' and curr_usdt >= self.min_order_size:
                    buy_amount = curr_usdt * 0.98
                    ticker = self.exchange.fetch_ticker(symbol)
                    self.exchange.create_market_buy_order(symbol, buy_amount / ticker['last'])
                
                # تنفيذ البيع (إعادة المال للأصل) عند تحقق الربح أو إشارة البيع
                elif signal == 'SELL' or curr_usdt >= target_amount:
                    self.sell_all_and_return_to_usdt(symbol)
                    if curr_usdt >= target_amount:
                        print("تم الوصول للهدف! تم تأمين الأرباح في USDT.")
                        break

                time.sleep(300) # فحص كل 5 دقائق
            except Exception as e:
                print(f"خطأ في الدورة: {e}")
                time.sleep(60)
        
        # 2. ضمان إعادة كل شيء لـ USDT عند نهاية الـ 12 ساعة
        self.sell_all_and_return_to_usdt(symbol)
        print("انتهت الجلسة. تم إعادة كافة الأرصدة إلى USDT.")
        self.is_running = False
        
