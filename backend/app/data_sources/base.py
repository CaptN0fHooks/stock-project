import httpx
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import asyncio
from app.config import settings

class DataSource(ABC):
    """Base class for all data sources"""

    def __init__(self, name: str):
        self.name = name
        self.healthy = True
        self.timeout = settings.HTTP_TIMEOUT
        self.max_retries = settings.HTTP_RETRIES

    async def fetch_with_retry(self, url: str, headers: Optional[Dict] = None, 
                               params: Optional[Dict] = None) -> Optional[Dict]:
        """Fetch with exponential backoff retry"""
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, headers=headers, params=params)
                    response.raise_for_status()
                    self.healthy = True
                    # Try JSON; fall back to text for XML callers
                    try:
                        return response.json()
                    except Exception:
                        return {"_text": response.text}
            except Exception as e:
                if attempt == self.max_retries:
                    self.healthy = False
                    print(f"[{self.name}] Failed after {self.max_retries} retries: {e}")
                    return None
                await asyncio.sleep(0.5 * (2 ** attempt))  # Exponential backoff
        return None

    @abstractmethod
    async def fetch_quote(self, symbol: str) -> Optional[Dict]:
        pass

    @abstractmethod
    async def fetch_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        pass
