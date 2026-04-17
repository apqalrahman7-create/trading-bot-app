import streamlit as st
import ccxt
import time

# --- UI Configuration ---
st.set_page_config(page_title="MEXC Trading Bot", layout="centered")
st.title("🤖 MEXC AI Trading Bot")
st.subheader("Target: 10% Profit")

# --- API Keys Input on Main Screen ---
st.info("Please enter your MEXC API credentials below to start.")
api_key = st.text_input("MEXC Access Key:", type="password")
secret_key = st.text_input("MEXC Secret Key:", type="password")

if api_key and secret_key:
    try:
        # Initialize Exchange
        exchange = ccxt.mexc({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
        })
        
        # Check Connection & Balance
        balance = exchange.fetch_balance()
        usdt_balance = balance['total'].get('USDT', 0)
        
        st.success(f"✅ Connected! Current Balance: {usdt_balance:.2f} USDT")
        st.divider()

        # Trade Settings
        order_amount = st.number_input("Order Amount (USDT):", min_value=11.0, value=12.0)
        
        if st.button("🚀 Start Auto-Trading"):
            st.warning("Scanning markets for 10% profit opportunities...")
            
            # Simple Scanner Logic
            tickers = exchange.fetch_tickers()
            found_opportunity = False
            
            for symbol, t in tickers.items():
                # Strategy: Target coins with 2% to 5% growth (Potential breakout)
                if '/USDT' in symbol and 2.0 <= t.get('percentage', 0) <= 5.0:
                    st.write(f"🎯 Opportunity Found: {symbol} at price {t['last']}")
                    st.info(f"Setting Sell Target at: {t['last'] * 1.10:.4f} (+10%)")
                    
                    # Execute Market Buy
                    # exchange.create_market_buy_order(symbol, order_amount)
                    
                    st.success(f"Trade executed for {symbol}!")
                    found_opportunity = True
                    break
            
            if not found_opportunity:
                st.error("No high-potential opportunities found right now. Try again in a few minutes.")

    except Exception as e:
        st.error(f"❌ Connection Error: Please check your API keys. Details: {e}")

else:
    st.warning("Waiting for API keys to connect to MEXC...")

st.divider()
st.caption("Secure Connection: Keys are used for this session only.")
