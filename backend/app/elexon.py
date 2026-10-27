from __future__ import annotations

import os
from datetime import date, datetime, time, timedelta, timezone

import httpx

from .logic import assess, select_as_of

BASE_URL = os.getenv("ELEXON_BASE_URL", "https://data.elexon.co.uk/bmrs/api/v1").rstrip("/")


class ElexonError(Exception):
    pass


async def _get(client: httpx.AsyncClient, path: str, params: dict) -> list[dict]:
    try:
        response = await client.get(f"{BASE_URL}{path}", params=params)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise ElexonError("Elexon data could not be retrieved. Please try again shortly.") from exc
    if isinstance(payload, list):
        return payload
    # Some Elexon endpoints use a `data` envelope.
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        return payload["data"]
    raise ElexonError("Elexon returned an unexpected response format.")


async def get_assessment(delivery_date: date, cutoff: datetime) -> dict:
    if delivery_date.year != 2026 or delivery_date.month != 1:
        raise ValueError("This demonstration is intentionally limited to January 2026.")
    # Raw WINDFOR/FUELHH are filtered by *publication* time, not target startTime.
    # Two days captures the D-1 updates and retains a fallback when the most recent
    # eligible forecast was published early. The later as-of selection still guards
    # against look-ahead; the actual join keeps delivery-day periods only.
    wind_params = {
        "publishDateTimeFrom": (cutoff - timedelta(days=2)).isoformat().replace("+00:00", "Z"),
        "publishDateTimeTo": cutoff.isoformat().replace("+00:00", "Z"),
    }
    fuel_params = {"settlementDateFrom": delivery_date.isoformat(), "settlementDateTo": delivery_date.isoformat()}
    async with httpx.AsyncClient(timeout=30) as client:
        forecasts, all_fuels = await _get(client, "/datasets/WINDFOR/stream", wind_params), await _get(client, "/datasets/FUELHH/stream", fuel_params)
    actuals = [r for r in all_fuels if str(r.get("fuelType", "")).upper() == "WIND"]
    eligible = select_as_of(forecasts, cutoff)
    points, metrics = assess(eligible, actuals)
    return {"deliveryDate": delivery_date.isoformat(), "decisionCutoff": cutoff.isoformat(), "points": points, "metrics": metrics,
            "source": {"actuals": "FUELHH / WIND", "forecasts": "WINDFOR"}}
