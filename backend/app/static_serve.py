from pathlib import Path
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

DIST = (Path(__file__).resolve().parents[1] / "frontend" / "dist")

def mount_static(app):
    if DIST.exists():
        # serve built JS/CSS
        app.mount("/assets", StaticFiles(directory=str(DIST / "assets")), name="assets")

        index_file = DIST / "index.html"

        @app.get("/", include_in_schema=False, response_class=HTMLResponse)
        async def serve_index():
            return index_file.read_text(encoding="utf-8")
    else:
        @app.get("/", include_in_schema=False)
        async def root_fallback():
            return {"message": "Market Aggregator API (no frontend dist/ found)"}
