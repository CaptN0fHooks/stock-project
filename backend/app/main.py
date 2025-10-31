from datetime import datetime
from typing import Dict, List, Any

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from app.static_serve import mount_static

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
from app.services import MarketService, WatchlistService, PostureService

app = FastAPI(title="Market Aggregator API", version="1.0.0")
mount_static(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

market = MarketService()
posture_svc = PostureService()

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

# ---------- helpers to coerce shapes safely ----------
def _as_quote(item: Any) -> Quote:
    d = item if isinstance(item, dict) else {}
    return Quote(
        symbol=str(d.get("symbol", "")),
        price=float(d.get("price", 0) or 0),
        pct=float(d.get("pct", 0) or 0),
        high=d.get("high"),
        low=d.get("low"),
        volume=d.get("volume"),
    )

def _as_vix(obj: Any) -> VIXData:
    d = {}
    if isinstance(obj, dict):
        d = obj
    elif isinstance(obj, list):
        d = obj[0] if obj else {}
    return VIXData(price=float(d.get("price", 0) or 0), pct=float(d.get("pct", 0) or 0))

# ---------- summary with optional live aggregation ----------
@app.get("/api/summary", response_model=MarketSummary)
async def summary(live: bool = Query(False, description="If true, try fetching live data with fallbacks")):
    # Defaults (static placeholders)
    indices: List[Quote] = []
    vix = VIXData(price=0.0, pct=0.0)
    breadth: Dict[str, BreadthData] = {"nyse": BreadthData(), "nasdaq": BreadthData()}
    sectors: List[SectorData] = []
    movers: Dict[str, List[Mover]] = {"gainers": [], "losers": [], "most_active": []}
    macro: List[MacroEvent] = []
    sec_headlines: List[SECHeadline] = []
    sources: Dict[str, str] = {"indices": "static", "vix": "static", "sectors": "static", "breadth": "static", "movers": "static", "macro": "static", "sec": "static"}
    latency_min: Dict[str, int] = {"indices": 0, "vix": 0, "sectors": 0, "breadth": 0, "movers": 0, "macro": 0, "sec": 0}

    if live:
        # Try each fetcher, swallow errors, keep any wins
        try:
            idx_raw, s = await market.get_indices()
            if isinstance(idx_raw, list):
                indices = [_as_quote(i) for i in idx_raw]
            sources["indices"] = s
        except Exception:
            pass

        try:
            vix_raw, s = await market.get_vix()
            vix = _as_vix(vix_raw)
            sources["vix"] = s
        except Exception:
            pass

        try:
            secs_raw, s = await market.get_sectors()
            if isinstance(secs_raw, list):
                buf = []
                for x in secs_raw:
                    if not isinstance(x, dict): 
                        continue
                    try:
                        buf.append(SectorData(symbol=str(x.get("symbol","")), name=str(x.get("name","")), pct=float(x.get("pct",0) or 0)))
                    except Exception:
                        continue
                sectors = buf
            sources["sectors"] = s
        except Exception:
            pass

        try:
            br_raw, s = await market.get_breadth()
            if isinstance(br_raw, dict):
                breadth = {
                    "nyse": BreadthData(**(br_raw.get("nyse") or {})),
                    "nasdaq": BreadthData(**(br_raw.get("nasdaq") or {})),
                }
            sources["breadth"] = s
        except Exception:
            pass

        try:
            mv_raw, s = await market.get_movers()
            if isinstance(mv_raw, dict):
                out: Dict[str, List[Mover]] = {"gainers": [], "losers": [], "most_active": []}
                for bucket in out.keys():
                    lst = mv_raw.get(bucket, []) or []
                    safe = []
                    for m in lst:
                        if not isinstance(m, dict): 
                            continue
                        try:
                            safe.append(Mover(symbol=str(m.get("symbol","")), price=float(m.get("price",0) or 0), pct=float(m.get("pct",0) or 0), vol=int(m.get("vol",0) or 0)))
                        except Exception:
                            continue
                    out[bucket] = safe
                movers = out
            sources["movers"] = s
        except Exception:
            pass

        try:
            macro_raw = await market.get_macro_calendar()
            macro = [MacroEvent(time=str(m.get("time","")), label=str(m.get("label","")), url=m.get("url")) for m in (macro_raw or []) if isinstance(m, dict)]
            sources["macro"] = "FRED"
        except Exception:
            pass

        try:
            sec_raw = await market.get_sec_headlines()
            sec_headlines = [SECHeadline(time=str(h.get("time","")), title=str(h.get("title","")), url=str(h.get("url",""))) for h in (sec_raw or []) if isinstance(h, dict)]
            sources["sec"] = "SECEdgar"
        except Exception:
            pass

    # posture: compute from whatever we have (safe defaults if empty)
    try:
        session_posture: SessionPosture = posture_svc.calculate(
            breadth={k: v.model_dump() for k,v in breadth.items()},
            sectors=[{"pct": s.pct} for s in sectors],
            vix_data={"pct": vix.pct},
        )
    except Exception:
        session_posture = SessionPosture(
            score=0.0,
            label="Neutral",
            components=PostureComponents(breadth=0.0, dispersion=0.0, vol_overlay=0.0),
            notes=[],
        )

    return MarketSummary(
        as_of=_now_iso(),
        sources=sources,
        latency_min=latency_min,
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
