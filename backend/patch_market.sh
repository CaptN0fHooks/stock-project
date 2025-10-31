# run from: /mnt/d/Apps/market-aggregator/backend
set -euo pipefail

FILE="app/services/market_service.py"
BACKUP="app/services/market_service.py.bak.$(date +%Y%m%d-%H%M%S)"

cp "$FILE" "$BACKUP" && echo "🔐 Backup: $BACKUP"

python3 - <<'PY'
import re, pathlib

p = pathlib.Path("app/services/market_service.py")
src = p.read_text(encoding="utf-8")

def replace_function(src, name, new_body):
    lines = src.splitlines(True)
    # find the def line (async def or def), capture its indent
    pat = re.compile(rf'^(\s*)(?:async\s+)?def\s+{name}\s*\(.*?\):\s*$', re.M)
    m = pat.search(src)
    if not m:
        raise SystemExit(f"❌ could not find function: {name}")
    start_idx = src[:m.start()].count("\n")
    indent = m.group(1)
    # find end of the function by scanning until next def/class at same or less indent
    i = start_idx + 1
    while i < len(lines):
        line = lines[i]
        # next top-level or same-scope block starts a new def/async def/class with indent <= current indent
        if re.match(rf'^{indent}(?:async\s+)?def\s+\w+\s*\(|^{indent}class\s+\w+\s*\(', line):
            break
        # also break at EOF
        i += 1
    # prepare replacement with preserved indent
    repl = "".join(indent + l if l.strip() else l for l in new_body.splitlines(True))
    # splice
    before = "".join(lines[:start_idx])
    after  = "".join(lines[i:])
    return before + repl + after

get_indices_impl = '''
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
'''.lstrip()

get_vix_impl = '''
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
'''.lstrip()

src = replace_function(src, "get_indices", get_indices_impl)
src = replace_function(src, "get_vix",     get_vix_impl)

pathlib.Path("app/services/market_service.py").write_text(src, encoding="utf-8")
print("✅ Patched: get_indices + get_vix")
PY

# restart backend cleanly
pkill -f "uvicorn" 2>/dev/null || true
nohup ./run.sh >/tmp/ma_api.out 2>&1 &
sleep 2
tail -n 3 /tmp/ma_api.out || true

# quick checks
echo "---- /api/summary (static) ----"
curl -s http://localhost:8000/api/summary | python3 -m json.tool | sed -n '1,60p'

echo
echo "---- /api/summary?live=1 (live) ----"
curl -s "http://localhost:8000/api/summary?live=1" | python3 -m json.tool | sed -n '1,140p'
