from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, timezone

@dataclass(frozen=True)
class Location:
    name: str
    lat: float
    lon: float

def _session() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    return s


def fetch_open_meteo_current(location: Location, *, timeout_s: int = 20) -> Dict[str, Any]:
    """
    Fetch current weather state for a location using Open-Meteo hourly data.
    Selects the latest available hour <= now (UTC).
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": location.lat,
        "longitude": location.lon,
        "hourly": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "surface_pressure",
            "wind_speed_10m",
            "rain",
            "cloudcover"
        ]),

        "daily": ",".join([
            "sunrise",
            "sunset",
        ]),
        "timezone": "UTC",
        "forecast_days": 1,
        "past_days": 0,
    }

    s = _session()
    r = s.get(url, params=params, timeout=timeout_s)
    r.raise_for_status()

    data = r.json()
    hourly = data["hourly"]
    daily = data["daily"]

    # ---- aktuális óra kiválasztása ----
    now = datetime.now(timezone.utc)

    times = [
        datetime.fromisoformat(t).replace(tzinfo=timezone.utc)
        for t in hourly["time"]
    ]

    idx = max(
        i for i, t in enumerate(times)
        if t <= now
    )

    return {
        "endpoint": url,
        "params": params,
        "timestamp_utc": times[idx].isoformat().replace("+00:00", "Z"),
        "metrics": {
            "temperature_c": hourly["temperature_2m"][idx],
            "humidity_pct": hourly["relative_humidity_2m"][idx],
            "pressure_hpa": hourly["surface_pressure"][idx],
            "wind_speed_kmh": hourly["wind_speed_10m"][idx],
            "rain": hourly["rain"][idx],
            "cloudcover": hourly['cloudcover'][idx],
            "sunrise": daily["sunrise"][0],
            "sunset": daily["sunset"][0]
        },
    }
