from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class Quote(BaseModel):
    symbol: str
    price: float
    pct: float
    high: Optional[float] = None
    low: Optional[float] = None
    volume: Optional[int] = None

class VIXData(BaseModel):
    symbol: str = "^VIX"
    price: float
    pct: float

class BreadthData(BaseModel):
    advancers: Optional[int] = None
    decliners: Optional[int] = None
    upVol: Optional[int] = None
    downVol: Optional[int] = None

class SectorData(BaseModel):
    symbol: str
    name: str
    pct: float

class Mover(BaseModel):
    symbol: str
    price: float
    pct: float
    vol: int

class MacroEvent(BaseModel):
    time: str
    label: str
    url: Optional[str] = None

class SECHeadline(BaseModel):
    time: str
    title: str
    url: str

class PostureComponents(BaseModel):
    breadth: float
    dispersion: float
    vol_overlay: float

class SessionPosture(BaseModel):
    score: float
    label: str
    components: PostureComponents
    notes: List[str]

class MarketSummary(BaseModel):
    as_of: str
    sources: Dict[str, str]
    latency_min: Dict[str, int]
    indices: List[Quote]
    vix: VIXData
    breadth: Dict[str, BreadthData]
    sectors: List[SectorData]
    movers: Dict[str, List[Mover]]
    macro: List[MacroEvent]
    sec_headlines: List[SECHeadline]
    session_posture: SessionPosture
    notes: List[str]

class WatchlistItem(BaseModel):
    symbol: str
    notes: Optional[str] = None
    added_at: Optional[str] = None

class Watchlist(BaseModel):
    symbols: List[WatchlistItem]
    updated_at: str

class MiniQuote(BaseModel):
    symbol: str
    price: float
    pct: float
    volume: Optional[int] = None
    sparkline: List[float] = Field(default_factory=list)

class HealthStatus(BaseModel):
    status: str
    timestamp: str
    sources: Dict[str, bool]
