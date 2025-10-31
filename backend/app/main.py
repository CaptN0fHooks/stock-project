from datetime import datetime
from typing import Dict, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    MarketSummary,
    Quote,
    VIXData,
    SectorData,
    Mover,
    MacroEvent,
    SECHeadline,
    SessionPosture,
    PostureComponents,
    HealthStatus,
    BreadthData,
)

app = FastAPI(title="Market Aggregator API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _now_iso() -> str:
    return datetime.utcnow().isoformat()

@app.get("/")
async def root():
    return {"message": "Market Aggregator API"}

@app.get("/api/health", response_model=HealthStatus)
async def health():
    return HealthStatus(
        status="ok",
        timestamp=_now_iso(),
        sources={
            "YahooFinance": True,
            "AlphaVantage": True,
            "Finnhub": True,
            "FRED": True,
            "SEC": True,
        },
    )

@app.get("/api/summary", response_model=MarketSummary)
async def summary():
    # Minimal, always-valid payload (placeholders). We’ll wire real fetchers next.
    indices: List[Quote] = []  # can be empty
    vix = VIXData(price=0.0, pct=0.0)
    breadth: Dict[str, BreadthData] = {
        "nyse": BreadthData(),
        "nasdaq": BreadthData(),
    }
    sectors: List[SectorData] = []
    movers: Dict[str, List[Mover]] = {"gainers": [], "losers": [], "most_active": []}
    macro: List[MacroEvent] = []
    sec_headlines: List[SECHeadline] = []

    session_posture = SessionPosture(
        score=0.0,
        label="Neutral",
        components=PostureComponents(breadth=0.0, dispersion=0.0, vol_overlay=0.0),
        notes=[],
    )

    return MarketSummary(
        as_of=_now_iso(),
        sources={
            "indices": "static",
            "vix": "static",
            "sectors": "static",
            "breadth": "static",
            "movers": "static",
            "macro": "static",
            "sec": "static",
        },
        latency_min={
            "indices": 0,
            "vix": 0,
            "sectors": 0,
            "breadth": 0,
            "movers": 0,
            "macro": 0,
            "sec": 0,
        },
        indices=indices,
        vix=vix,
        breadth=breadth,
        sectors=sectors,
        movers=movers,
        macro=macro,
        sec_headlines=sec_headlines,
        session_posture=session_posture,
        notes=[],
    )
