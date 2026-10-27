from datetime import datetime, timezone

from app.logic import assess, select_as_of


def test_as_of_never_uses_later_forecast():
    rows = [
        {"startTime": "2026-01-03T00:00:00Z", "publishTime": "2026-01-02T10:00:00Z", "generation": 100},
        {"startTime": "2026-01-03T00:00:00Z", "publishTime": "2026-01-02T13:00:00Z", "generation": 200},
    ]
    selected = select_as_of(rows, datetime(2026, 1, 2, 12, tzinfo=timezone.utc))
    assert selected[0]["generation"] == 100


def test_metrics_use_actual_minus_forecast():
    points, metrics = assess(
        [{"startTime": "t", "publishTime": "2026-01-01T00:00:00Z", "generation": 100}],
        [{"startTime": "t", "generation": 130}],
    )
    assert points[0]["errorMw"] == 30
    assert metrics["maeMw"] == 30
    assert metrics["p90DownsideMw"] == 30
