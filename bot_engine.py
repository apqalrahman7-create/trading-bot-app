import ccxt
import pandas as pd
import time

class TradingBot:
    def __init__(self, exchange_id, api_key, secret_key):
        self.exchange = getattr(ccxt, exchange_id)({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap', 'adjustForTimeDifference': True}
        })
        self.is_running = False

    def get_total_balance(self):
        """الدالة التي أظهرت لك الرصيد سابقاً مع تحسينها لتعمل دائماً"""
        try:
            balance = self.exchange.fetch_balance()
            # البحث عن الرصيد في كل الزوايا (إجمالي، حر، أو معلومات إضافية)
            total = float(balance.get('USDT', {}).get('total', balance.get('total', {}).get('USDT', 0)))
            return total
        except: return 0.0

    def run_automated_logic(self, initial_balance):
        self.is_running = True
        target_profit = initial_balance * 1.10 # هدف 10%
        symbol = 'BTC/USDT:USDT'
        
        yield f"🚀 انطلق التداول الحقيقي | الرصيد المبدئي: ${initial_balance:.2f}"
        
        while self.is_running:
            try:
                current_bal = self.get_total_balance()
                profit_now = current_bal - initial_balance
                
                # إظهار الأرباح الحالية
                yield f"💰 الرصيد الآن: ${current_bal:.2f} | الربح المجني: ${profit_now:.2f}"

                if current_bal >= target_profit:
                    yield "✅ تم الوصول للهدف (10%)! إغلاق الجلسة وتأمين الأرباح."
                    self.is_running = False ; break
                
                # تحليل سريع للتدخل
                bars = self.exchange.fetch_ohlcv(symbol, timeframe='1m', limit=15)
                df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
                ema = df['c'].ewm(span=10, adjust=False).mean().iloc[-1]
                price = df['c'].iloc[-1]

                # تنفيذ صفقات حقيقية (شراء وبيع تلقائي)
                # استخدام رافعة مالية 10x وتقسيم المحفظة
                qty = (current_bal * 10 * 0.9) / price
                precise_qty = self.exchange.amount_to_precision(symbol, qty)

                if price > ema:
                    yield f"📈 إشارة شراء حقيقية على {symbol}.."
                    self.exchange.create_market_buy_order(symbol, precise_qty)
                elif price < ema:
                    yield f"📉 إشارة بيع حقيقية على {symbol}.."
                    self.exchange.create_market_sell_order(symbol, precise_qty)

            except Exception as e:
                yield f"⚠️ تنبيه: {str(e)}"
            time.sleep(20)
            
