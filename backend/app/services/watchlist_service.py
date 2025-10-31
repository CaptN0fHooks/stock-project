import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from app.models import Watchlist, WatchlistItem

WATCHLIST_PATH = Path(__file__).parent.parent.parent / "data" / "watchlist.json"
WATCHLIST_PATH.parent.mkdir(parents=True, exist_ok=True)

class WatchlistService:
    """Local JSON-backed watchlist storage with simple dedupe."""

    @staticmethod
    def _now_iso() -> str:
        return datetime.now().isoformat()

    def get(self) -> Watchlist:
        if WATCHLIST_PATH.exists():
            try:
                data = json.loads(WATCHLIST_PATH.read_text(encoding="utf-8"))
                return Watchlist(**data)
            except Exception:
                pass
        return Watchlist(symbols=[], updated_at=self._now_iso())

    def save(self, wl: Watchlist) -> Watchlist:
        wl.updated_at = self._now_iso()
        WATCHLIST_PATH.write_text(json.dumps(wl.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
        return wl

    def add_symbols(self, symbols: List[Dict]) -> Watchlist:
        wl = self.get()
        existing = {item.symbol.upper(): item for item in wl.symbols}
        for entry in symbols:
            sym = entry.get("symbol", "").upper()
            if not sym:
                continue
            notes = entry.get("notes")
            if sym in existing:
                if notes:
                    existing[sym].notes = notes
            else:
                existing[sym] = WatchlistItem(symbol=sym, notes=notes, added_at=self._now_iso())
        wl.symbols = list(existing.values())
        return self.save(wl)

    def remove_symbol(self, symbol: str) -> Watchlist:
        wl = self.get()
        symbol = symbol.upper()
        wl.symbols = [it for it in wl.symbols if it.symbol.upper() != symbol]
        return self.save(wl)

    def replace(self, items: List[Dict]) -> Watchlist:
        cleaned = []
        seen = set()
        for entry in items:
            sym = entry.get("symbol", "").upper()
            if not sym or sym in seen:
                continue
            seen.add(sym)
            cleaned.append(WatchlistItem(symbol=sym, notes=entry.get("notes"), added_at=self._now_iso()))
        wl = Watchlist(symbols=cleaned, updated_at=self._now_iso())
        return self.save(wl)
