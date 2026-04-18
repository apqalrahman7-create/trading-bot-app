import ccxt

class TradingEngine:
    def __init__(self, api_key, secret_key):
        self.exchange = ccxt.mexc({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'} # ضبط المحرك على العقود الآجلة
        })
        self.target_profit = 0.10  
        self.stop_loss = 0.05      

    def get_signal(self):
        try:
            self.exchange.load_markets()
            tickers = self.exchange.fetch_tickers()
            # مسح الـ 40 عملة كما طلبت
            for symbol, ticker in list(tickers.items())[:40]:
                if '/USDT:USDT' in symbol and ticker['percentage'] is not None:
                    change = ticker['percentage']
                    # إشارة صعود قوية
                    if 2.0 <= change <= 5.0:
                        return symbol, ticker['last']
            return None, None
        except:
            return None, None

    def execute_trade(self, symbol, amount_usdt):
        """تنفيذ أمر الشراء بعد تصحيح الكمية"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            last_price = ticker['last']
            
            # 1. حساب الكمية (المبلغ بالدولار / السعر)
            raw_amount = amount_usdt / last_price
            
            # 2. ضبط الدقة البرمجية (ضروري لمنع الأخطاء)
            market = self.exchange.market(symbol)
            final_amount = self.exchange.amount_to_precision(symbol, raw_amount)

            # 3. إرسال أمر الشراء (Market Long)
            order = self.exchange.create_market_buy_order(symbol, float(final_amount))
            return order
        except Exception as e:
            print(f"Trade Error: {e}")
            return None
            
