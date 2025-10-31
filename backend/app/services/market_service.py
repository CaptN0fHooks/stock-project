from typing import List, Dict
from app.data_sources import YahooFinance, AlphaVantage, Finnhub, FRED, SECEdgar
from app.cache import cached, quote_cache, sector_cache, mover_cache
from datetime import datetime
import httpx
import os
from app.config import settings

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
        """
        Use ETF proxies to avoid the caret-index API pain:
          ^GSPC ≈ SPY, ^IXIC ≈ QQQ, ^DJI ≈ DIA
        Falls back to empty on failure (frontend still renders).
        """
        from app.config import settings
        symbols = [
            ("^GSPC", "SPY"),
            ("^IXIC", "QQQ"),
            ("^DJI",  "DIA"),
        ]
        out = []
        source = "AlphaVantage"
        try:
            for idx_symbol, proxy in symbols:
                q = await self._alpha_vantage_quote(proxy, settings.ALPHA_VANTAGE_KEY)
                out.append({
                    "symbol": idx_symbol,
                    "price": float(q.get("price", 0) or 0.0),
                    "pct":   float(q.get("pct",   0) or 0.0),
                })
        except Exception:
            source = "None"
            out = []
        return out, source
    async def get_vix(self):
        """
        Prefer Finnhub (intraday). If it fails/zeros, fall back to FRED VIXCLS daily.
        """
        from app.config import settings
        price = 0.0
        pct   = 0.0
        source = "Finnhub"
        try:
            q = await self._finnhub_quote("^VIX", settings.FINNHUB_KEY)
            price = float(q.get("price", 0) or 0.0)
            pct   = float(q.get("pct",   0) or 0.0)
            if price <= 0:
                raise ValueError("empty vix from finnhub")
        except Exception:
            source = "FRED"
            try:
                fred = await self._fred_series_latest("VIXCLS", settings.FRED_API_KEY)
                v = fred.get("value")
                if v not in (None, ".", ""):
                    price = float(v)
                    pct   = 0.0
                else:
                    source = "None"
            except Exception:
                source = "None"
        return {"symbol": "^VIX", "price": price, "pct": pct}, source
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
