from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "brfss_dw.sqlite"


@st.cache_data
def load_years() -> list[str]:
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query("SELECT DISTINCT year FROM vw_kpi_by_year ORDER BY year", conn)
    return df["year"].tolist()


def _in_clause_params(values: list[str]) -> tuple[str, list[str]]:
    placeholders = ",".join(["?"] * len(values))
    return placeholders, values


@st.cache_data
def load_kpi(years: list[str]) -> pd.DataFrame:
    placeholders, params = _in_clause_params(years)
    query = f"""
        SELECT
            SUM(respondents) AS respondents,
            SUM(target_positive) AS target_positive,
            ROUND(100.0 * SUM(target_positive) / NULLIF(SUM(respondents), 0), 2) AS target_rate_pct
        FROM vw_kpi_by_year
        WHERE year IN ({placeholders})
    """
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn, params=params)


@st.cache_data
def load_yearly(years: list[str]) -> pd.DataFrame:
    placeholders, params = _in_clause_params(years)
    query = f"""
        SELECT year, respondents, target_positive, target_rate_pct
        FROM vw_kpi_by_year
        WHERE year IN ({placeholders})
        ORDER BY year
    """
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn, params=params)


@st.cache_data
def load_top_states(years: list[str]) -> pd.DataFrame:
    placeholders, params = _in_clause_params(years)
    query = f"""
        SELECT
            state_code,
            SUM(respondents) AS respondents,
            SUM(target_positive) AS target_positive,
            ROUND(100.0 * SUM(target_positive) / NULLIF(SUM(respondents), 0), 2) AS target_rate_pct
        FROM vw_target_by_state
        WHERE year IN ({placeholders})
        GROUP BY state_code
        HAVING state_code <> '0'
        ORDER BY target_rate_pct DESC
        LIMIT 15
    """
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn, params=params)


@st.cache_data
def load_age_sex(years: list[str]) -> pd.DataFrame:
    placeholders, params = _in_clause_params(years)
    query = f"""
        SELECT
            age_group,
            sex,
            SUM(respondents) AS respondents,
            SUM(target_positive) AS target_positive,
            ROUND(100.0 * SUM(target_positive) / NULLIF(SUM(respondents), 0), 2) AS target_rate_pct
        FROM vw_target_by_age_sex
        WHERE year IN ({placeholders})
        GROUP BY age_group, sex
        HAVING age_group <> 'Unknown' AND sex <> 'Unknown'
        ORDER BY age_group, sex
    """
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn, params=params)


def main() -> None:
    st.set_page_config(page_title="BRFSS Data Warehouse Dashboard", layout="wide")
    st.title("BRFSS - Hurtownia Danych")
    st.caption("KPI: ryzyko (target=1) na podstawie cech zdrowotnych i demograficznych")

    if not DB_PATH.exists():
        st.error(f"Brak bazy: {DB_PATH}")
        st.stop()

    all_years = load_years()
    selected_years = st.sidebar.multiselect("Wybierz lata", options=all_years, default=all_years)
    if not selected_years:
        st.warning("Wybierz przynajmniej jeden rok.")
        st.stop()

    kpi = load_kpi(selected_years).iloc[0]
    yearly = load_yearly(selected_years)
    top_states = load_top_states(selected_years)
    age_sex = load_age_sex(selected_years)

    c1, c2, c3 = st.columns(3)
    c1.metric("Respondenci", f"{int(kpi['respondents']):,}")
    c2.metric("Target pozytywny", f"{int(kpi['target_positive']):,}")
    c3.metric("Target rate", f"{kpi['target_rate_pct']}%")

    st.subheader("Trend roczny")
    st.line_chart(yearly.set_index("year")[["target_rate_pct"]])
    st.dataframe(yearly, use_container_width=True)

    st.subheader("Top stany wg target rate")
    st.bar_chart(top_states.set_index("state_code")["target_rate_pct"])
    st.dataframe(top_states, use_container_width=True)

    st.subheader("Target rate wg wieku i płci")
    pivot = age_sex.pivot(index="age_group", columns="sex", values="target_rate_pct").fillna(0)
    st.dataframe(pivot, use_container_width=True)


if __name__ == "__main__":
    main()
