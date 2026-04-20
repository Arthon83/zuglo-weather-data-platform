import streamlit as st # type: ignore
import pandas as pd # type: ignore
import plotly.express as px # type: ignore
import streamlit.components.v1 as components # type: ignore

from datetime import datetime as dt, timedelta

import util


st.set_page_config(
    page_title="Zugló időjárás dashboard",
    layout="wide"
)

# 1 óránként automatikus frissítés
components.html(
    """
    <script>
        setTimeout(function() {
            window.parent.location.reload();
        }, 3600000);
    </script>
    """,
    height=0,
)


PARAMS = {
    "temperature_c": {
        "attribute": "temperature_c",
        "value": "Hőmérséklet",
        "measure": "°C",
        "title": "Hőmérséklet összehasonlító idősor",
        "bin_calc": 1,
    },
    "humidity_pct": {
        "attribute": "humidity_pct",
        "value": "Páratartalom",
        "measure": "%",
        "title": "Páratartalom összehasonlító idősor",
        "bin_calc": 5,
    },
    "pressure_hpa": {
        "attribute": "pressure_hpa",
        "value": "Légnyomás",
        "measure": "hPa",
        "title": "Légnyomás összehasonlító idősor",
        "bin_calc": 1,
    },
}


@st.cache_data(ttl=3600, show_spinner=False)
def load_data() -> pd.DataFrame:
    df = util.get_silver_zuglo()
    df_clean = util.clean(df).copy()
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


def compare_chart(df_clean: pd.DataFrame, weather_dict: dict):
    today = dt.today().date()
    yesterday = today - timedelta(days=1)
    date_threshold = today - timedelta(days=6)

    attr = weather_dict["attribute"]

    hours = pd.DataFrame({"hour": list(range(24))})

    hist_df = df_clean[
        (df_clean["date"] <= yesterday) &
        (df_clean["date"] > date_threshold)
    ].copy()

    past_5_day_mean = (
        hist_df.groupby("hour", as_index=False)
        .agg({attr: "mean"})
    )

    today_set = (
        df_clean[df_clean["date"] == today]
        .groupby("hour", as_index=False)
        .agg({attr: "mean"})
    )

    yesterday_set = (
        df_clean[df_clean["date"] == yesterday]
        .groupby("hour", as_index=False)
        .agg({attr: "mean"})
    )

    merged = hours.merge(past_5_day_mean, on="hour", how="left")
    merged = merged.merge(today_set, on="hour", how="left", suffixes=("_5d", ""))
    merged = merged.merge(yesterday_set, on="hour", how="left", suffixes=("", "_yesterday"))

    base_col = f"{attr}_5d"
    today_col = attr
    yest_col = f"{attr}_yesterday"

    fig = px.line(
        merged,
        x="hour",
        y=[base_col, today_col, yest_col],
        title=weather_dict["title"],
        labels={
            "hour": "Óra",
            "value": weather_dict["value"],
            "variable": "Időszak",
        },
    )
    
    fig.update_layout(
        height = 320,
        margin = dict(l=40, r=20, t=50, b=40),
        legend_title_text="Időszak",
        legend = dict(
            orientation = "h",
            yanchor = "bottom",
            y = -0.6,
            xanchor = "center",
            x = 0.5
        )
    )

    

    fig.data[0].name = "5 nap átlaga"
    fig.data[1].name = weather_dict["value"]
    fig.data[2].name = f"Tegnapi {weather_dict['value']}"

    fig.data[0].line = dict(color="gray", dash="dash", width=1)
    fig.data[1].line = dict(color="red", width=2)
    fig.data[2].line = dict(color="black", width=1)

    unit = weather_dict["measure"]
    value_name = weather_dict["value"]

    fig.data[0].hovertemplate = (
        f"Óra: %{{x}}<br>{value_name}: %{{y:.1f}} {unit}"
        "<br>Időszak: 5 nap átlaga<extra></extra>"
    )
    fig.data[1].hovertemplate = (
        f"Óra: %{{x}}<br>{value_name}: %{{y:.1f}} {unit}"
        f"<br>Időszak: {weather_dict['value']}<extra></extra>"
    )
    fig.data[2].hovertemplate = (
        f"Óra: %{{x}}<br>{value_name}: %{{y:.1f}} {unit}"
        f"<br>Időszak: Tegnapi {weather_dict['value']}<extra></extra>"
    )

    return fig


def histogram_chart(df_clean: pd.DataFrame, params: dict, current_hour) -> px.histogram:
    past_10_date = dt.today().date() - timedelta(days=10)

    yy = df_clean[df_clean["date"] >= past_10_date][["time", "hour", params["attribute"]]].copy()
    yy = yy[yy["time"] == current_hour].copy()
    yy = yy.dropna(subset=[params["attribute"]])

    if yy.empty:
        fig = px.histogram(title=f"{params['value']} hisztogram")
        fig.add_annotation(
            text="Nincs elég adat az aktuális órára.",
            showarrow=False,
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
        )
        fig.update_layout(height=320, margin=dict(l=40, r=20, t=50, b=40))
        return fig

    value_range = yy[params["attribute"]].max() - yy[params["attribute"]].min()
    bins = max(1, int(value_range / params["bin_calc"]))

    fig = px.histogram(
        yy,
        x=params["attribute"],
        title=f"{params['value']} eloszlás az aktuális órában, az elmúlt 10 napban.",
        labels={
            params["attribute"]: f"{params['value']} ({params['measure']})",
        },
    )
    

    fig.update_layout(
        height=320,
        margin=dict(l=40, r=20, t=50, b=40),
        bargap=0.1,
    )
    fig.update_yaxes(title_text="Darab")
    fig.update_traces(
        nbinsx=bins,
        marker_color="royalblue",
        hovertemplate=(
            f"{params['value']}: %{{x:.1f}} {params['measure']}"
            "<br>Darab: %{y}<extra></extra>"
        ),
    )

    return fig


def daynight_chart(df_clean: pd.DataFrame, params: dict) -> px.line:
    day_night = (
        df_clean.groupby(["date", "is_day"], as_index=False)
        .agg({params["attribute"]: "mean"})
    )

    pivot_df = (
        day_night.pivot(index="date", columns="is_day", values=params["attribute"])
        .reset_index()
        .sort_values("date")
    )

    # Biztonság kedvéért legyenek meg az oszlopok
    if True not in pivot_df.columns:
        pivot_df[True] = None
    if False not in pivot_df.columns:
        pivot_df[False] = None

    fig = px.line(
        pivot_df,
        x="date",
        y=[True, False],
        title=f"Nappali vs éjszakai {params['value']}",
        labels={
            "value": params["value"],
            "date": "Dátum",
            "variable": "Időszak",
        },
    )
    

    fig.update_layout(
        height=360,
        margin=dict(l=40, r=20, t=50, b=40),
        legend_title_text="Időszak",
        legend = dict(
            orientation = "h",
            yanchor = "bottom",
            y = -0.6,
            xanchor = "center",
            x = 0.5
        )
    )

    fig.data[0].name = "Nappal"
    fig.data[1].name = "Éjszaka"
    fig.data[0].line = dict(color="red", width=2)
    fig.data[1].line = dict(color="blue", width=2)

    unit = params["measure"]
    value_name = params["value"]

    fig.data[0].hovertemplate = (
        f"Dátum: %{{x|%Y-%m-%d}}<br>{value_name}: %{{y:.1f}} {unit}"
        "<br>Időszak: Nappal<extra></extra>"
    )
    fig.data[1].hovertemplate = (
        f"Dátum: %{{x|%Y-%m-%d}}<br>{value_name}: %{{y:.1f}} {unit}"
        "<br>Időszak: Éjszaka<extra></extra>"
    )

    return fig


def render_tab(df_clean: pd.DataFrame, params: dict) -> None:
    current_hour = pd.Timestamp.now().floor("h").time()

    top_fig = daynight_chart(df_clean, params)
    compare_fig = compare_chart(df_clean, params)
    hist_fig = histogram_chart(df_clean, params, current_hour)

    

    st.plotly_chart(top_fig, use_container_width=True, config={"displayModeBar": False})

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.plotly_chart(compare_fig, use_container_width=True, config={"displayModeBar": False})

    with col_right:
        st.plotly_chart(hist_fig, use_container_width=True, config={"displayModeBar": False})



def main():
    st.title("Zugló időjárás dashboard")
    st.write(
        "Ez a dashboard Zugló aktuális és közelmúltbeli időjárási mintáit mutatja be. "
        "A nézet az utolsó ismert mérésre, valamint a hőmérséklet, páratartalom és légnyomás "
        "összehasonlító grafikonjaira épül."
    )
    

    try:
        df_clean = load_data()

        if df_clean.empty:
            st.warning("Nincs megjeleníthető adat.")
            return

        time_col = get_time_column(df_clean)
        last_row = get_last_record(df_clean)
        last_record_str = format_last_record_time(last_row, time_col)

        st.caption(f"Utolsó ismert rekord: {last_record_str} (magyar idő)")

        kpi_col1, kpi_col2, kpi_col3 = st.columns(3)

        with kpi_col1:
            st.metric(
                "Hőmérséklet",
                f"{last_row['temperature_c']:.1f} °C" if pd.notna(last_row["temperature_c"]) else "N/A"
            )

        with kpi_col2:
            st.metric(
                "Páratartalom",
                f"{last_row['humidity_pct']:.0f} %" if pd.notna(last_row["humidity_pct"]) else "N/A"
            )

        with kpi_col3:
            st.metric(
                "Légnyomás",
                f"{last_row['pressure_hpa']:.0f} hPa" if pd.notna(last_row["pressure_hpa"]) else "N/A"
            )

        tab1, tab2, tab3 = st.tabs(["Hőmérséklet", "Páratartalom", "Légnyomás"])

        with tab1:
            render_tab(df_clean, PARAMS["temperature_c"])

        with tab2:
            render_tab(df_clean, PARAMS["humidity_pct"])

        with tab3:
            render_tab(df_clean, PARAMS["pressure_hpa"])

    except Exception as e:
        st.error(f"Hiba történt a dashboard betöltése közben: {e}")


if __name__ == "__main__":
    main()