from typing import Optional, Dict, List
from .base import DataSource
from app.config import settings

class AlphaVantage(DataSource):
    """Alpha Vantage data source"""

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self):
        super().__init__("AlphaVantage")
        self.api_key = settings.ALPHA_VANTAGE_KEY

    async def fetch_quote(self, symbol: str) -> Optional[Dict]:
        if not self.api_key:
            return None
        params = {'function': 'GLOBAL_QUOTE', 'symbol': symbol, 'apikey': self.api_key}
        data = await self.fetch_with_retry(self.BASE_URL, params=params)
        if not data or 'Global Quote' not in data:
            return None
        quote = data['Global Quote']
        if not quote:
            return None
        try:
            pct = quote.get('10. change percent', '0').rstrip('%')
            pct_val = float(pct) if pct not in (None, '') else 0.0
        except Exception:
            pct_val = 0.0
        return {
            'symbol': quote.get('01. symbol', symbol),
            'price': float(quote.get('05. price', 0) or 0),
            'pct': pct_val,
            'high': float(quote.get('03. high', 0) or 0),
            'low': float(quote.get('04. low', 0) or 0),
            'volume': int(float(quote.get('06. volume', 0) or 0))
        }

    async def fetch_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        quotes = {}
        for symbol in symbols[:5]:
            q = await self.fetch_quote(symbol)
            if q:
                quotes[symbol] = q
        return quotes

    async def fetch_intraday(self, symbol: str) -> List[float]:
        if not self.api_key:
            return []
        params = {'function': 'TIME_SERIES_INTRADAY', 'symbol': symbol, 'interval': '5min', 'apikey': self.api_key}
        data = await self.fetch_with_retry(self.BASE_URL, params=params)
        if not data or 'Time Series (5min)' not in data:
            return []
        ts = data['Time Series (5min)']
        closes = [float(v['4. close']) for k, v in list(ts.items())[:50]]
        return list(reversed(closes))
