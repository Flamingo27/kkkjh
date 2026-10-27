from __future__ import annotations

from datetime import datetime
from math import sqrt
from typing import Iterable


def parse_time(value: str) -> datetime:
    """Parse Elexon ISO timestamps, normalising trailing Z."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def select_as_of(forecasts: Iterable[dict], cutoff: datetime) -> list[dict]:
    """Return the last forecast published no later than cutoff per target period."""
    chosen: dict[str, dict] = {}
    for row in forecasts:
        if "publishTime" not in row or "startTime" not in row:
            continue
        published = parse_time(row["publishTime"])
        if published > cutoff:
            continue
        key = row["startTime"]
        if key not in chosen or published > parse_time(chosen[key]["publishTime"]):
            chosen[key] = row
    return [chosen[key] for key in sorted(chosen)]


def assess(forecasts: list[dict], actuals: list[dict]) -> tuple[list[dict], dict]:
    actual_by_time = {row.get("startTime"): row for row in actuals}
    points = []
    for forecast in forecasts:
        actual = actual_by_time.get(forecast.get("startTime"))
        if actual is None:
            continue
        try:
            predicted = float(forecast["generation"])
            observed = float(actual["generation"])
        except (KeyError, TypeError, ValueError):
            continue
        error = observed - predicted
        points.append({
            "startTime": forecast["startTime"], "forecastMw": round(predicted, 1),
            "actualMw": round(observed, 1), "errorMw": round(error, 1),
            "publishTime": forecast["publishTime"],
        })
    if not points:
        return [], {"count": 0, "maeMw": None, "rmseMw": None, "biasMw": None, "p90DownsideMw": None}
    errors = [p["errorMw"] for p in points]
    mae = sum(abs(x) for x in errors) / len(errors)
    rmse = sqrt(sum(x * x for x in errors) / len(errors))
    downside = sorted(max(x, 0) for x in errors)
    # Nearest-rank P90: a reserve proxy for under-forecast wind exposure.
    p90 = downside[max(0, int(0.9 * len(downside) + 0.999999) - 1)]
    metrics = {"count": len(points), "maeMw": round(mae, 1), "rmseMw": round(rmse, 1),
               "biasMw": round(sum(errors) / len(errors), 1), "p90DownsideMw": round(p90, 1)}
    return points, metrics
