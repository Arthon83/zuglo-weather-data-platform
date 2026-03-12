from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict
import config

from weather_fetcher import Location, fetch_open_meteo_current
from databricks_client import get_connection


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def insert_silver(record: dict):
    sql = f"""
    INSERT INTO weather.silver.zuglo_data (
        event_time_utc,
        location_name,
        lat,
        lon,
        temperature_c,
        humidity_pct,
        pressure_hpa,
        wind_speed_kmh,
        rain_mm,
        cloudcover_pct,
        sunrise_utc,
        sunset_utc,
        ingested_at_utc
    )
    VALUES (
        '{record["event_time_utc"]}',
        '{record["location"]["name"]}',
        {record["location"]["lat"]},
        {record["location"]["lon"]},
        {record["metrics"]["temperature_c"]},
        {record["metrics"]["humidity_pct"]},
        {record["metrics"]["pressure_hpa"]},
        {record["metrics"]["wind_speed_kmh"]},
        {record["metrics"]["rain"]},
        {record["metrics"]["cloudcover"]},
        '{record["metrics"]["sunrise"]}',
        '{record["metrics"]["sunset"]}',
        '{record["ingested_at_utc"]}'
    )
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)

def run():
    loc = Location(name=config.LOCATION_NAME, lat=config.ZUGLO_LAT, lon=config.ZUGLO_LON)

    data = fetch_open_meteo_current(loc)

    

    record = {
        "event_time_utc": data["timestamp_utc"],
        "location": {
            "name": loc.name,
            "lat": loc.lat,
            "lon": loc.lon,
        },
        "source": {
            "name": "open-meteo",
            "endpoint": data["endpoint"],
        },
        "metrics": data["metrics"],
        "ingested_at_utc": utc_now_iso(),
    }
    print(record)
    

    insert_silver(record)
    print(f"[OK] appended {data['timestamp_utc']}")

if __name__ == "__main__":
    run()