from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DW_ROOT = Path(__file__).resolve().parents[1]
SOURCE_CSV = PROJECT_ROOT / "data_processed" / "model_data_preprocessed.csv"
DB_PATH = DW_ROOT / "data" / "brfss_dw.sqlite"
SCHEMA_SQL = DW_ROOT / "sql" / "create_schema.sql"
MARTS_SQL = DW_ROOT / "sql" / "create_marts.sql"


CODE_COLUMNS = [
    "_AGEG5YR",
    "_SEX",
    "EDUCA",
    "INCOME3",
    "EMPLOY1",
    "_STATE",
    "_URBSTAT",
    "CHECKUP1",
    "GENHLTH",
    "RENTHOM1",
    "MEDCOST1",
    "PERSDOC3",
    "year",
    "target",
]


def to_code_int(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    return numeric.fillna(0).astype(int)


def build_dimensions(staging_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    mappings = {
        "dim_year": ("year_code", "year_label"),
        "dim_state": ("state_code", "state_label"),
        "dim_age_group": ("age_group_code", "age_group_label"),
        "dim_sex": ("sex_code", "sex_label"),
        "dim_education": ("education_code", "education_label"),
        "dim_income": ("income_code", "income_label"),
        "dim_employment": ("employment_code", "employment_label"),
        "dim_urban": ("urban_code", "urban_label"),
    }

    labels = {
        "dim_age_group": {
            0: "Unknown",
            1: "18-24",
            2: "25-29",
            3: "30-34",
            4: "35-39",
            5: "40-44",
            6: "45-49",
            7: "50-54",
            8: "55-59",
            9: "60-64",
            10: "65-69",
            11: "70-74",
            12: "75-79",
            13: "80+",
        },
        "dim_sex": {0: "Unknown", 1: "Male", 2: "Female"},
        "dim_education": {
            0: "Unknown",
            1: "Never attended school",
            2: "Elementary",
            3: "Some high school",
            4: "High school graduate",
            5: "Some college",
            6: "College graduate",
        },
        "dim_income": {
            0: "Unknown",
            1: "< 10k",
            2: "10k-15k",
            3: "15k-20k",
            4: "20k-25k",
            5: "25k-35k",
            6: "35k-50k",
            7: "50k-75k",
            8: "75k-100k",
            9: "100k-150k",
            10: "150k-200k",
            11: ">= 200k",
        },
        "dim_employment": {
            0: "Unknown",
            1: "Employed for wages",
            2: "Self-employed",
            3: "Out of work >1 year",
            4: "Out of work <1 year",
            5: "Homemaker",
            6: "Student",
            7: "Retired",
            8: "Unable to work",
        },
        "dim_urban": {0: "Unknown", 1: "Urban", 2: "Rural"},
    }

    input_columns = {
        "dim_year": "year_code",
        "dim_state": "state_code",
        "dim_age_group": "age_group_code",
        "dim_sex": "sex_code",
        "dim_education": "education_code",
        "dim_income": "income_code",
        "dim_employment": "employment_code",
        "dim_urban": "urban_code",
    }

    dims: dict[str, pd.DataFrame] = {}
    for table_name, source_column in input_columns.items():
        value_col, label_col = mappings[table_name]
        unique_codes = sorted(staging_df[source_column].dropna().unique().tolist())
        if 0 not in unique_codes:
            unique_codes = [0] + unique_codes
        dim_df = pd.DataFrame({value_col: unique_codes})
        if table_name in labels:
            dim_df[label_col] = dim_df[value_col].map(labels[table_name]).fillna("Other")
        else:
            dim_df[label_col] = dim_df[value_col].astype(str)
        key_col = table_name.replace("dim_", "") + "_key"
        dim_df.insert(0, key_col, range(1, len(dim_df) + 1))
        dims[table_name] = dim_df
    return dims


def load_source() -> pd.DataFrame:
    if not SOURCE_CSV.exists():
        raise FileNotFoundError(f"Missing source file: {SOURCE_CSV}")
    df = pd.read_csv(SOURCE_CSV)
    missing_cols = [c for c in CODE_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in source CSV: {missing_cols}")
    return df


def prepare_staging(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    for col in CODE_COLUMNS:
        data[col] = to_code_int(data[col])

    data["respondent_id"] = range(1, len(data) + 1)
    data["bmi"] = pd.to_numeric(data["_BMI5"], errors="coerce") / 100.0
    data["phys_hlth_days"] = pd.to_numeric(data["PHYSHLTH"], errors="coerce")
    data["children_count"] = pd.to_numeric(data["CHILDREN"], errors="coerce")

    staging = data.rename(
        columns={
            "_AGEG5YR": "age_group_code",
            "_SEX": "sex_code",
            "EDUCA": "education_code",
            "INCOME3": "income_code",
            "EMPLOY1": "employment_code",
            "_STATE": "state_code",
            "_URBSTAT": "urban_code",
            "CHECKUP1": "checkup_code",
            "GENHLTH": "genhlth_code",
            "RENTHOM1": "housing_code",
            "MEDCOST1": "medcost_code",
            "PERSDOC3": "persdoc_code",
            "year": "year_code",
            "target": "target_flag",
        }
    )

    staging_cols = [
        "respondent_id",
        "year_code",
        "state_code",
        "age_group_code",
        "sex_code",
        "education_code",
        "income_code",
        "employment_code",
        "urban_code",
        "checkup_code",
        "genhlth_code",
        "housing_code",
        "medcost_code",
        "persdoc_code",
        "target_flag",
        "bmi",
        "phys_hlth_days",
        "children_count",
    ]
    return staging[staging_cols]


def create_fact_table(staging_df: pd.DataFrame, dims: dict[str, pd.DataFrame]) -> pd.DataFrame:
    fact = staging_df.copy()

    joins = [
        ("dim_year", "year_code", "year_key"),
        ("dim_state", "state_code", "state_key"),
        ("dim_age_group", "age_group_code", "age_group_key"),
        ("dim_sex", "sex_code", "sex_key"),
        ("dim_education", "education_code", "education_key"),
        ("dim_income", "income_code", "income_key"),
        ("dim_employment", "employment_code", "employment_key"),
        ("dim_urban", "urban_code", "urban_key"),
    ]

    for dim_name, code_col, key_col in joins:
        dim_df = dims[dim_name]
        dim_code_col = dim_df.columns[1]
        fact = fact.merge(dim_df[[key_col, dim_code_col]], left_on=code_col, right_on=dim_code_col, how="left")
        fact = fact.drop(columns=[dim_code_col])

    fact["respondent_count"] = 1

    fact_cols = [
        "respondent_id",
        "year_key",
        "state_key",
        "age_group_key",
        "sex_key",
        "education_key",
        "income_key",
        "employment_key",
        "urban_key",
        "target_flag",
        "checkup_code",
        "genhlth_code",
        "housing_code",
        "medcost_code",
        "persdoc_code",
        "bmi",
        "phys_hlth_days",
        "children_count",
        "respondent_count",
    ]
    return fact[fact_cols]


def execute_sql_file(conn: sqlite3.Connection, sql_path: Path) -> None:
    script = sql_path.read_text(encoding="utf-8")
    conn.executescript(script)


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    source_df = load_source()
    staging_df = prepare_staging(source_df)
    dimensions = build_dimensions(staging_df)
    fact_df = create_fact_table(staging_df, dimensions)

    with sqlite3.connect(DB_PATH) as conn:
        execute_sql_file(conn, SCHEMA_SQL)
        staging_df.to_sql("stg_brfss_model", conn, if_exists="replace", index=False)
        for table_name, dim_df in dimensions.items():
            dim_df.to_sql(table_name, conn, if_exists="replace", index=False)
        fact_df.to_sql("fact_health_survey", conn, if_exists="replace", index=False)
        execute_sql_file(conn, MARTS_SQL)

    print("Warehouse created.")
    print(f"Source rows: {len(source_df):,}")
    print(f"Fact rows:   {len(fact_df):,}")
    print(f"DB file:     {DB_PATH}")


if __name__ == "__main__":
    main()
