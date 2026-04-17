    def get_active_balance(self):
        """Force MEXC to reveal balance from all possible wallet types"""
        try:
            # 1. Try fetching Unified/Futures balance
            balance_data = self.exchange.fetch_balance()
            
            # Extract USDT from all possible keys (total, free, or info)
            total_usdt = float(balance_data.get('USDT', {}).get('total', 
                             balance_data.get('total', {}).get('USDT', 0)))
            
            # 2. Identify the market type based on where funds are
            if total_usdt >= 5:
                # Determine if it's Futures or Spot based on exchange options
                m_type = self.exchange.options.get('defaultType', 'swap')
                symbol = 'BTC/USDT:USDT' if m_type == 'swap' else 'BTC/USDT'
                return total_usdt, 'futures' if m_type == 'swap' else 'spot', symbol

            # 3. Last resort: Try fetching Spot explicitly if total was 0
            spot_bal = self.exchange.fetch_balance({'type': 'spot'})
            spot_usdt = float(spot_bal.get('total', {}).get('USDT', 0))
            
            if spot_usdt >= 5:
                return spot_usdt, 'spot', 'BTC/USDT'
            
            return max(total_usdt, spot_usdt), None, None
        except Exception as e:
            print(f"Balance fetch error: {e}")
            return 0.0, None, None
            
