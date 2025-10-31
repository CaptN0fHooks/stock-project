from typing import Optional, Dict, List
from .base import DataSource
from app.config import settings

class Finnhub(DataSource):
    """Finnhub data source"""

    BASE_URL = "https://finnhub.io/api/v1"

    def __init__(self):
        super().__init__("Finnhub")
        self.api_key = settings.FINNHUB_KEY

    async def fetch_quote(self, symbol: str) -> Optional[Dict]:
        if not self.api_key:
            return None
        url = f"{self.BASE_URL}/quote"
        params = {'symbol': symbol, 'token': self.api_key}
        data = await self.fetch_with_retry(url, params=params)
        if not data or 'c' not in data:
            return None
        current = data.get('c', 0)
        prev_close = data.get('pc', current or 0)
        pct_change = ((current - prev_close) / prev_close * 100) if prev_close else 0
        return {
            'symbol': symbol,
            'price': current,
            'pct': pct_change,
            'high': data.get('h'),
            'low': data.get('l'),
            'volume': None
        }

    async def fetch_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        quotes = {}
        for symbol in symbols:
            q = await self.fetch_quote(symbol)
            if q:
                quotes[symbol] = q
        return quotes
