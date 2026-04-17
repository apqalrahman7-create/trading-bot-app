import ccxt
import time
import pandas as pd

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
        self.leverage = 10 # رافعة مالية افتراضية

    def get_total_balance(self):
        """جلب الرصيد الحقيقي من MEXC وإصلاح مشكلة الـ 0.00"""
        try:
            balance = self.exchange.fetch_balance({'type': 'swap'})
            # محاولة قراءة الرصيد من أكثر من مفتاح (total أو free أو info)
            usdt_bal = balance.get('USDT', {}).get('total', 0)
            if usdt_bal == 0:
                usdt_bal = balance.get('total', {}).get('USDT', 0)
            return float(usdt_bal)
        except Exception as e:
            print(f"Error fetching balance: {e}")
            return 0.0

    def close_all_positions(self, symbols):
        """إغلاق كافة الصفقات المفتوحة وإعادة الرصيد للمحفظة"""
        for symbol in symbols:
            try:
                positions = self.exchange.fetch_positions([symbol])
                for pos in positions:
                    size = float(pos['contracts'])
                    if size != 0:
                        side = 'sell' if size > 0 else 'buy'
                        self.exchange.create_order(symbol, 'market', side, abs(size), params={'reduceOnly': True})
            except: pass

    def run_automated_logic(self, balance):
        self.is_running = True
        initial_balance = balance
        target_profit = initial_balance * 1.10 # هدف 10%
        
        yield f"🚀 بدأت الجلسة الذكية! الرصيد: ${initial_balance:.2f} | الهدف: ${target_profit:.2f}"
        
        symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']
        
        while self.is_running:
            current_balance = self.get_total_balance()
            
            # 1. فحص الوصول للهدف (10% ربح)
            if current_balance >= target_profit:
                yield f"💰 تم تحقيق الهدف بنجاح! الرصيد الحالي: ${current_balance:.2f}"
                self.close_all_positions(symbols)
                self.is_running = False
                break
            
            for symbol in symbols:
                if not self.is_running: break
                
                try:
                    # تحليل فني (EMA)
                    bars = self.exchange.fetch_ohlcv(symbol, timeframe='5m', limit=20)
                    df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
                    ema = df['c'].ewm(span=10, adjust=False).mean().iloc[-1]
                    price = df['c'].iloc[-1]

                    # تحديد كمية الصفقة (تقسيم رأس المال: استخدام 10% من المحفظة)
                    trade_amount_usdt = current_balance * 0.1
                    qty = (trade_amount_usdt * self.leverage) / price
                    precise_qty = float(self.exchange.amount_to_precision(symbol, qty))

                    # 2. تنفيذ التداول التلقائي الذكي
                    if price > ema:
                        yield f"📈 إشارة شراء (Long) على {symbol}..."
                        self.exchange.create_market_buy_order(symbol, precise_qty)
                    elif price < ema:
                        yield f"📉 إشارة بيع (Short) على {symbol}..."
                        self.exchange.create_market_sell_order(symbol, precise_qty)

                except Exception as e:
                    yield f"⚠️ تنبيه في {symbol}: {str(e)}"
                
                time.sleep(2)
            
            time.sleep(15) # انتظار بين دورات المسح
