import ccxt

class TradingEngine:
    def __init__(self, api_key, secret_key):
        # الربط المباشر باستخدام المفاتيح الممررة من app.py
        self.exchange = ccxt.mexc({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
        })
        self.target_profit = 0.10  # هدف 10%
        self.stop_loss = 0.05      # حماية 5%

    def get_signal(self):
        """البحث عن عملة صاعدة بنسبة تدل على قوة"""
        try:
            self.exchange.load_markets()
            tickers = self.exchange.fetch_tickers()
            # فلترة العملات الصاعدة بين 2% و 5% مقابل USDT
            for symbol, ticker in tickers.items():
                if '/USDT' in symbol and ticker['percentage'] is not None:
                    change = ticker['percentage']
                    if 2.0 <= change <= 5.0:
                        return symbol, ticker['last']
            return None, None
        except Exception as e:
            return None, str(e)

    def execute_trade(self, symbol, amount_usdt):
        """تنفيذ أمر الشراء"""
        try:
            # شراء بسعر السوق
            order = self.exchange.create_market_buy_order(symbol, amount_usdt)
            return order
        except Exception as e:
            return None
            
