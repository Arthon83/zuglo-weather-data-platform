from dataclasses import dataclass
from pathlib import Path
import os


# -------- Location --------

ZUGLO_LAT = 47.51758
ZUGLO_LON = 19.10549
LOCATION_NAME = "zuglo"


# -------- Ingest behavior --------

DEFAULT_POLLING_MINUTES = int(os.getenv("WEATHER_POLLING_MINUTES", "15"))

#RAW_DATA_DIR = Path(os.getenv("WEATHER_RAW_DIR", "data/raw"))
#RAW_FILENAME = os.getenv("WEATHER_RAW_FILE", "weather_zuglo.jsonl")

#RAW_PATH = RAW_DATA_DIR / RAW_FILENAME


# -------- Source metadata --------

SOURCE_NAME = "open-meteo"
SOURCE_TIMEZONE = "UTC"