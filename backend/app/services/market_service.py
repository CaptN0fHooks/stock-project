from typing import List, Dict
from app.data_sources import YahooFinance, AlphaVantage, Finnhub, FRED, SECEdgar
from app.cache import cached, quote_cache, sector_cache, mover_cache
from datetime import datetime

class MarketService:
    """Main service for fetching market data with multi-source fallback"""

    INDICES = ['^GSPC', '^IXIC', '^DJI']
    VIX = '^VIX'

    SECTORS = {
        'XLY': 'Consumer Disc',
        'XLP': 'Consumer Staples',
        'XLE': 'Energy',
        'XLF': 'Financials',
        'XLV': 'Healthcare',
        'XLI': 'Industrials',
        'XLB': 'Materials',
        'XLK': 'Info Tech',
        'XLU': 'Utilities',
        'XLRE': 'Real Estate',
        'XLC': 'Communication'
    }

    def __init__(self):
        self.sources = [YahooFinance(), AlphaVantage(), Finnhub()]
        self.fred = FRED()
        self.sec = SECEdgar()

    async def fetch_with_fallback(self, symbols: List[str]):
        for source in self.sources:
            try:
                quotes = await source.fetch_quotes(symbols)
                if quotes:
                    return quotes, source.name
            except Exception as e:
                print(f"[{source.name}] Error: {e}")
                continue
        return {}, "None"

    @cached(quote_cache)
    async def get_indices(self):
        quotes, source = await self.fetch_with_fallback(self.INDICES)
        return [quotes.get(s, {'symbol': s, 'price': 0, 'pct': 0}) for s in self.INDICES], source

    @cached(quote_cache)
    async def get_vix(self):
        quotes, source = await self.fetch_with_fallback([self.VIX])
        return quotes.get(self.VIX, {'symbol': self.VIX, 'price': 0, 'pct': 0}), source

    @cached(sector_cache)
    async def get_sectors(self):
        symbols = list(self.SECTORS.keys())
        quotes, source = await self.fetch_with_fallback(symbols)
        sectors = []
        for sym, name in self.SECTORS.items():
            quote = quotes.get(sym, {})
            sectors.append({'symbol': sym, 'name': name, 'pct': quote.get('pct', 0)})
        return sectors, source

    async def get_breadth(self):
        breadth = {
            'nyse': {'advancers': None, 'decliners': None, 'upVol': None, 'downVol': None},
            'nasdaq': {'advancers': None, 'decliners': None, 'upVol': None, 'downVol': None}
        }
        return breadth, "MockData"

    @cached(mover_cache)
    async def get_movers(self):
        movers = {'gainers': [], 'losers': [], 'most_active': []}
        return movers, "MockData"

    async def get_macro_calendar(self):
        return await self.fred.fetch_calendar()

    async def get_sec_headlines(self):
        return await self.sec.fetch_headlines()

    async def get_sparkline(self, symbol: str):
        yahoo = YahooFinance()
        sparkline = await yahoo.fetch_sparkline(symbol)
        if sparkline:
            return sparkline
        av = AlphaVantage()
        return await av.fetch_intraday(symbol)
