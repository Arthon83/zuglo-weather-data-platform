### Zugló Weather Data Platform

A production-style data platform for collecting, transforming, and visualizing real-time weather data — built with modern data engineering tools.

---

#### Project Overview

This project ingests hourly weather data from the Open-Meteo API and processes it through a medallion architecture (Bronze → Silver → Gold) using:

- Python for ingestion
- Databricks (Lakehouse) for storage
- dbt for transformations
- Apache Airflow for orchestration
- Streamlit for visualization

The goal is to demonstrate how a real-world data pipeline can be designed end-to-end — from raw ingestion to business-ready insights.
