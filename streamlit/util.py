#!/usr/bin/env python
# coding: utf-8

# In[1]:


import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime as dt
from databricks_client import get_connection


# In[2]:


def get_silver_zuglo():
    query = "SELECT * FROM weather.silver.zuglo_data"
    with get_connection() as conn:
        df = pd.read_sql(query, conn)
    return df


# In[ ]:


def clean(silver):
    silver = silver.sort_values(["event_time_utc"], ascending = False)
    silver["event_time_hu"] = silver["event_time_utc"].dt.tz_convert("Europe/Budapest").dt.tz_localize(None)
    silver['month'] = silver['event_time_hu'].dt.month
    silver['weekday'] = silver['event_time_hu'].dt.weekday
    silver["week"] = silver["event_time_hu"].dt.isocalendar().week
    silver["day"] = silver["event_time_hu"].dt.day
    silver['date'] = silver['event_time_hu'].dt.date
    silver['time'] = silver['event_time_hu'].dt.time
    silver['hour'] = silver['event_time_hu'].dt.hour
    silver['sunrise'] = silver["sunrise_utc"].dt.tz_convert("Europe/Budapest").dt.tz_localize(None)
    silver['sunset'] = silver["sunset_utc"].dt.tz_convert("Europe/Budapest").dt.tz_localize(None)
    
    silver = silver[['event_time_hu', 'date','time','month','week','day','hour','temperature_c', 'humidity_pct','pressure_hpa','wind_speed_kmh','rain_mm','cloudcover_pct','sunrise','sunset']].reset_index(drop=True)
    return silver

def load_data() -> pd.DataFrame:
    df = get_silver_zuglo()
    df_clean = clean(df).copy()
    df_clean = df_clean[df_clean["date"] > pd.Timestamp("2026-03-15").date()]

    df_clean["date"] = pd.to_datetime(df_clean["date"]).dt.date
    

    # Biztonsági konverziók
    if "event_time_hu" in df_clean.columns:
        df_clean["event_time_hu"] = pd.to_datetime(df_clean["event_time_hu"], errors="coerce")

    if "event_time_utc" in df_clean.columns:
        df_clean["event_time_utc"] = pd.to_datetime(df_clean["event_time_utc"], errors="coerce")

    if "sunrise" in df_clean.columns:
        df_clean["sunrise"] = pd.to_datetime(df_clean["sunrise"], errors="coerce")

    if "sunset" in df_clean.columns:
        df_clean["sunset"] = pd.to_datetime(df_clean["sunset"], errors="coerce")

    # Nappal / éjszaka logika
    if all(col in df_clean.columns for col in ["event_time_hu", "sunrise", "sunset"]):
        df_clean["is_day"] = (
            (df_clean["event_time_hu"] >= df_clean["sunrise"]) &
            (df_clean["event_time_hu"] < df_clean["sunset"])
        )
    else:
        df_clean["is_day"] = False

    return df_clean

def get_time_column(df: pd.DataFrame) -> str:
    if "event_time_hu" in df.columns and df["event_time_hu"].notna().any():
        return "event_time_hu"
    if "event_time_utc" in df.columns and df["event_time_utc"].notna().any():
        return "event_time_utc"
    raise ValueError("Nincs használható időbélyeg oszlop.")


def get_last_record(df: pd.DataFrame) -> pd.Series:
    time_col = get_time_column(df)
    valid = df[df[time_col].notna()].sort_values(time_col)
    if valid.empty:
        raise ValueError("Nincs megjeleníthető rekord.")
    return valid.iloc[-1]


def format_last_record_time(last_row: pd.Series, time_col: str) -> str:
    ts = pd.to_datetime(last_row[time_col], errors="coerce")
    if pd.isna(ts):
        return "N/A"
    return ts.strftime("%Y-%m-%d %H:%M")


