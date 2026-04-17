import ccxt
import time

# --- إعدادات الحساب ---
API_KEY = 'ضع_هنا_الـ_ACCESS_KEY'
SECRET_KEY = 'ضع_هنا_الـ_SECRET_KEY'

# الربط مع منصة MEXC
exchange = ccxt.mexc({
    'apiKey': API_KEY,
    'secret': SECRET_KEY,
    'enableRateLimit': True,
})

# --- إعدادات التداول ---
TARGET_PROFIT = 0.10  # هدف الربح 10%
STOP_LOSS = 0.05      # وقف الخسارة 5% لحماية رصيدك
ORDER_AMOUNT_USDT = 12 # مبلغ الدخول في الصفقة (أكبر من حد المنصة الأدنى)

def get_all_usdt_symbols():
    """جلب جميع العملات المتاحة للتداول مقابل USDT"""
    exchange.load_markets()
    return [symbol for symbol in exchange.symbols if '/USDT' in symbol and ':USDT' not in symbol]

def scan_for_opportunity():
    """البحث عن عملة صعدت بنسبة 2% في آخر ساعة كإشارة دخول"""
    symbols = get_all_usdt_symbols()
    print(f"جاري فحص {len(symbols)} عملة في MEXC...")
    
    for symbol in symbols:
        try:
            ticker = exchange.fetch_ticker(symbol)
            change = ticker['percentage'] # نسبة التغير في 24 ساعة
            
            # استراتيجية بسيطة: إذا صعدت العملة بين 2% و 5% الآن (بداية صعود)
            if 2.0 <= change <= 5.0:
                print(f"✅ فرصة مكتشفة في {symbol} | نسبة الصعود: {change}%")
                return symbol
        except:
            continue
    return None

def trade():
    print("🚀 البوت بدأ العمل للبحث عن ربح 10%...")
    
    while True:
        try:
            # 1. البحث عن فرصة
            symbol = scan_for_opportunity()
            
            if symbol:
                # 2. تنفيذ أمر شراء بسعر السوق
                print(f"🛒 محاولة شراء {symbol} بمبلغ {ORDER_AMOUNT_USDT} USDT...")
                order = exchange.create_market_buy_order(symbol, ORDER_AMOUNT_USDT)
                buy_price = order['price'] if order['price'] else exchange.fetch_ticker(symbol)['last']
                
                print(f"💰 تم الشراء بسعر: {buy_price}")

                # 3. حساب أهداف البيع
                take_profit_price = buy_price * (1 + TARGET_PROFIT)
                stop_loss_price = buy_price * (1 - STOP_LOSS)

                # 4. مراقبة الصفقة للبيع عند ربح 10%
                while True:
                    current_ticker = exchange.fetch_ticker(symbol)
                    current_price = current_ticker['last']
                    
                    print(f"📊 {symbol} | السعر الحالي: {current_price} | الهدف: {take_profit_price:.4f}", end='\r')

                    if current_price >= take_profit_price:
                        print(f"\n🎉 تم الوصول لهدف 10%! جاري البيع...")
                        exchange.create_market_sell_order(symbol, order['amount'])
                        break
                    
                    if current_price <= stop_loss_price:
                        print(f"\n📉 ضرب وقف الخسارة. جاري الخروج...")
                        exchange.create_market_sell_order(symbol, order['amount'])
                        break
                    
                    time.sleep(10) # فحص السعر كل 10 ثواني
            
            else:
                print("😴 لا توجد فرص حالياً، سأعيد الفحص بعد دقيقة...")
                time.sleep(60)

        except Exception as e:
            print(f"⚠️ حدث خطأ: {e}")
            time.sleep(30)

if __name__ == "__main__":
    trade()
    
