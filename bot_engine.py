import ccxt
import time

class TradingEngine:
    def __init__(self, api_key, secret_key):
        # الربط مع MEXC
        self.exchange = ccxt.mexc({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
        })
        self.target_profit = 0.10  # هدف 10%
        self.stop_loss = 0.05      # حماية 5%

    def check_volume_spike(self, symbol):
        """التأكد من وجود سيولة وحركة حقيقية على العملة"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            volume = ticker['quoteVolume'] # حجم التداول بالدولار
            # نختار العملات التي حجم تداولها فوق 50 ألف دولار لضمان سهولة البيع
            if volume > 50000:
                return True
            return False
        except:
            return False

    def get_signal(self):
        """البحث عن عملة في بداية انفجار سعري"""
        self.exchange.load_markets()
        all_symbols = [s for s in self.exchange.symbols if '/USDT' in s and ':USDT' not in s]
        
        print(f"🔍 فحص محرك الذكاء لـ {len(all_symbols)} عملة...")
        
        for symbol in all_symbols:
            try:
                ticker = self.exchange.fetch_ticker(symbol)
                change = ticker['percentage']
                
                # استراتيجية: العملة التي صعدت بين 3% و 7% مع حجم تداول جيد
                if 3.0 <= change <= 7.0:
                    if self.check_volume_spike(symbol):
                        return symbol, ticker['last']
            except:
                continue
        return None, None

    def execute_trade(self, symbol, amount_usdt):
        """تنفيذ الصفقة وملاحقة الربح"""
        try:
            print(f"🚀 إشارة قوية! شراء {symbol} بمبلغ {amount_usdt} USDT")
            order = self.exchange.create_market_buy_order(symbol, amount_usdt)
            buy_price = self.exchange.fetch_ticker(symbol)['last']
            
            tp_price = buy_price * (1 + self.target_profit)
            sl_price = buy_price * (1 - self.stop_loss)

            print(f"✅ تم الدخول بسعر {buy_price} | الهدف (+10%): {tp_price:.4f}")

            while True:
                price = self.exchange.fetch_ticker(symbol)['last']
                print(f"⏳ مراقبة {symbol}: {price} | الربح المستهدف: {tp_price:.4f}", end='\r')

                if price >= tp_price:
                    print(f"\n💰 تم تحقيق هدف الـ 10%! جاري جني الأرباح...")
                    self.exchange.create_market_sell_order(symbol, order['amount'])
                    return True

                if price <= sl_price:
                    print(f"\n⚠️ خروج اضطراري (وقف خسارة) لحماية الرصيد.")
                    self.exchange.create_market_sell_order(symbol, order['amount'])
                    return False

                time.sleep(5)
        except Exception as e:
            print(f"❌ خطأ في التنفيذ: {e}")
            return False
            
