from typing import Optional, Dict, List
from .base import DataSource

class YahooFinance(DataSource):
    """Yahoo Finance data source (unofficial API)"""

    BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart"
    QUOTE_URL = "https://query1.finance.yahoo.com/v7/finance/quote"

    def __init__(self):
        super().__init__("YahooFinance")

    async def fetch_quote(self, symbol: str) -> Optional[Dict]:
        url = f"{self.QUOTE_URL}?symbols={symbol}"
        data = await self.fetch_with_retry(url)
        if not data or 'quoteResponse' not in data:
            return None
        results = data['quoteResponse'].get('result', [])
        if not results:
            return None
        quote = results[0]
        return {
            'symbol': quote.get('symbol'),
            'price': quote.get('regularMarketPrice', 0),
            'pct': quote.get('regularMarketChangePercent', 0),
            'high': quote.get('regularMarketDayHigh'),
            'low': quote.get('regularMarketDayLow'),
            'volume': quote.get('regularMarketVolume')
        }

    async def fetch_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        symbol_str = ','.join(symbols)
        url = f"{self.QUOTE_URL}?symbols={symbol_str}"
        data = await self.fetch_with_retry(url)
        if not data or 'quoteResponse' not in data:
            return {}
        results = data['quoteResponse'].get('result', [])
        quotes = {}
        for quote in results:
            sym = quote.get('symbol')
            quotes[sym] = {
                'symbol': sym,
                'price': quote.get('regularMarketPrice', 0),
                'pct': quote.get('regularMarketChangePercent', 0),
                'high': quote.get('regularMarketDayHigh'),
                'low': quote.get('regularMarketDayLow'),
                'volume': quote.get('regularMarketVolume')
            }
        return quotes

    async def fetch_sparkline(self, symbol: str, points: int = 50) -> List[float]:
        url = f"{self.BASE_URL}/{symbol}?interval=5m&range=1d"
        data = await self.fetch_with_retry(url)
        if not data or 'chart' not in data:
            return []
        result = data['chart'].get('result', [])
        if not result:
            return []
        indicators = result[0].get('indicators', {})
        quotes = indicators.get('quote', [])
        if not quotes:
            return []
        closes = quotes[0].get('close', [])
        valid_closes = [c for c in closes if c is not None]
        return valid_closes[-points:] if len(valid_closes) > points else valid_closes
