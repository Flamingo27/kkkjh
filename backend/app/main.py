from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .elexon import ElexonError, get_assessment

app = FastAPI(title="Wind Procurement Desk", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/assessment")
async def assessment(delivery_date: date = Query(alias="deliveryDate"), cutoff: datetime | None = None):
    # Default day-ahead auction decision convention: 12:00 UTC on D-1.
    if cutoff is None:
        cutoff = datetime.combine(delivery_date - timedelta(days=1), time(12), tzinfo=timezone.utc)
    elif cutoff.tzinfo is None:
        cutoff = cutoff.replace(tzinfo=timezone.utc)
    try:
        return await get_assessment(delivery_date, cutoff)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ElexonError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


static_dir = Path(__file__).resolve().parents[2] / "frontend_dist"
if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str):
        candidate = static_dir / path
        return FileResponse(candidate if path and candidate.is_file() else static_dir / "index.html")
