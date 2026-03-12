select
    date(event_time_utc)               as day,
    location_name,

    -- Temperature
    avg(temperature_c)                as avg_temperature_c,
    min(temperature_c)                as min_temperature_c,
    max(temperature_c)                as max_temperature_c,

    -- Humidity
    avg(humidity_pct)                 as avg_humidity_pct,
    min(humidity_pct)                 as min_humidity_pct,
    max(humidity_pct)                 as max_humidity_pct,

    -- Pressure
    avg(pressure_hpa)                 as avg_pressure_hpa,
    min(pressure_hpa)                 as min_pressure_hpa,
    max(pressure_hpa)                 as max_pressure_hpa,

    -- Wind
    avg(wind_speed_kmh)               as avg_wind_speed_kmh,
    max(wind_speed_kmh)               as max_wind_speed_kmh,

    count(*)                          as measurements_count
from {{ source('weather_raw', 'zuglo_data') }}
group by
    day,
    location_name
order by
    day,
    location_name
