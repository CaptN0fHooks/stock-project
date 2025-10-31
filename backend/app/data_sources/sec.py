from typing import List, Dict, Optional
from .base import DataSource
import xml.etree.ElementTree as ET
from datetime import datetime
import httpx

class SECEdgar(DataSource):
    """SEC EDGAR filings source"""

    RSS_URL = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=&company=&dateb=&owner=include&start=0&count=10&output=atom"

    def __init__(self):
        super().__init__("SECEdgar")

    async def fetch_headlines(self) -> List[Dict]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {'User-Agent': 'Market Aggregator contact@example.com'}
                response = await client.get(self.RSS_URL, headers=headers)
                response.raise_for_status()
                root = ET.fromstring(response.text)
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                headlines = []
                for entry in root.findall('atom:entry', ns)[:5]:
                    title_elem = entry.find('atom:title', ns)
                    link_elem = entry.find('atom:link', ns)
                    updated_elem = entry.find('atom:updated', ns)
                    if title_elem is not None and link_elem is not None:
                        headlines.append({
                            'time': updated_elem.text if updated_elem is not None else datetime.now().isoformat(),
                            'title': title_elem.text,
                            'url': link_elem.get('href', '')
                        })
                self.healthy = True
                return headlines
        except Exception as e:
            print(f"[SECEdgar] Error fetching headlines: {e}")
            self.healthy = False
            return []

    async def fetch_quote(self, symbol: str) -> Optional[Dict]:
        return None

    async def fetch_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        return {}
