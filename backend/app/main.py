from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import List, Dict, Any

from app.services import MarketService, WatchlistService, PostureService
from app.models import (
    MarketSummary, Quote, VIXData, SectorData, Mover,
    MacroEvent, SECHeadline, SessionPosture, HealthStatus, MiniQuote, Watchlist
)

app = FastAPI(title="Market Aggregator API", version="1.0.0")

# CORS for local dev (Vite on 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

market = MarketService()
watch = WatchlistService()
posture = PostureService()

def _now_iso() -> str:
    return datetime.utcnow().isoformat()

def _safe(data: Any, default: Any):
    return data if data is not None else default

@app.get("/")
async def root():
    return {"message": "Market Aggregator API"}

@app.get("/api/health", response_model=HealthStatus)
async def health():
    sources = {"YahooFinance": True, "AlphaVantage": True, "Finnhub": True, "FRED": True, "SEC": True}
    return HealthStatus(status="ok", timestamp=_now_iso(), sources=sources)

