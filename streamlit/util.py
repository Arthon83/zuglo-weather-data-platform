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
