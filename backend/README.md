# Market Aggregator (Backend)

Local-first FastAPI service that aggregates free U.S. market data with multi-source fallbacks, a session posture heuristic, and a simple watchlist + miniquotes (sparklines) endpoint.

## Quickstart (Windows / PowerShell)

```powershell
cd backend
.\run.ps1
```

Then open: `http://localhost:8000/docs`

## Endpoints

- `GET /api/summary`
- `GET /api/miniquotes?symbols=AAPL,MSFT`
- `GET /api/watchlist` / `POST /api/watchlist` / `PUT /api/watchlist` / `DELETE /api/watchlist/{symbol}`
- `GET /api/health`

## Notes

- Free sources can be ~15 min delayed.
- Breadth and Movers are placeholders until a compliant free source is integrated.
- Provide `ALPHA_VANTAGE_KEY` and `FINNHUB_KEY` in `.env` for better fallbacks.
