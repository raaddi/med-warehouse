from pathlib import Path
import pandas as pd


BASE = Path(r"C:\Users\Radek\Documents\New project\data_raw\brfss")
OUT = Path(r"C:\Users\Radek\Documents\New project\data_processed")
OUT.mkdir(parents=True, exist_ok=True)

FILES = {
    2022: BASE / "LLCP2022.XPT",
    2023: BASE / "LLCP2023.XPT",
    2024: BASE / "LLCP2024.XPT",
}


def load_data(file_path: Path, n_rows: int = 50_000, chunk_size: int = 10_000) -> pd.DataFrame:
    reader = pd.read_sas(file_path, format="xport", chunksize=chunk_size)
    parts = []
    loaded = 0
    for chunk in reader:
        need = n_rows - loaded
        if need <= 0:
            break
        part = chunk.head(need).copy()
        parts.append(part)
        loaded += len(part)
    if not parts:
        return pd.DataFrame()
    return pd.concat(parts, ignore_index=True)


def clean_missing(series: pd.Series) -> pd.Series:
    # Generic BRFSS special/missing codes used in this project.
    return series.replace([7, 8, 9, 77, 88, 99, 777, 888, 999], pd.NA)


def build_dataset() -> tuple[pd.DataFrame, pd.DataFrame]:
    data_2022 = load_data(FILES[2022], n_rows=50_000)
    data_2023 = load_data(FILES[2023], n_rows=50_000)
    data_2024 = load_data(FILES[2024], n_rows=50_000)

    data_2022["year"] = 2022
    data_2023["year"] = 2023
    data_2024["year"] = 2024

    common_cols = sorted(
        set(data_2022.columns) & set(data_2023.columns) & set(data_2024.columns)
    )
    all_data = pd.concat(
        [
            data_2022[common_cols],
            data_2023[common_cols],
            data_2024[common_cols],
        ],
        ignore_index=True,
    )
    return all_data, pd.DataFrame({"common_cols": common_cols})


def preprocessing(all_data: pd.DataFrame) -> pd.DataFrame:
    mental_candidates = ["MENTHLTH", "_MENT14D"]
    chronic_candidates = [
        "DIABETE4",
        "DIABETE3",
        "DIABETE5",
        "CVDCRHD4",
        "CVDINFR4",
        "CVDSTRK3",
        "CHCCOPD3",
        "CHCKDNY2",
        "HAVARTH5",
        "HAVARTH4",
        "ASTHMS1",
    ]

    mental_present = [c for c in mental_candidates if c in all_data.columns]
    chronic_present = [c for c in chronic_candidates if c in all_data.columns]

    if "MENTHLTH" in all_data.columns:
        m = clean_missing(all_data["MENTHLTH"])
        all_data["mental_low"] = (m >= 14).astype("Int64")
    elif "_MENT14D" in all_data.columns:
        all_data["mental_low"] = (clean_missing(all_data["_MENT14D"]) == 1).astype("Int64")
    else:
        raise ValueError("Missing both MENTHLTH and _MENT14D.")

    if not chronic_present:
        raise ValueError("No chronic disease columns found.")

    flags = []
    for col in chronic_present:
        s = clean_missing(all_data[col])
        flags.append((s == 1).fillna(False))

    all_data["chronic_any"] = pd.concat(flags, axis=1).any(axis=1).astype("Int64")
    all_data["target"] = (
        (all_data["mental_low"] == 1) & (all_data["chronic_any"] == 1)
    ).astype("Int64")

    feature_candidates = [
        "_AGEG5YR",
        "_SEX",
        "EDUCA",
        "INCOME3",
        "EMPLOY1",
        "MARITAL",
        "_BMI5",
        "_RFSMOK3",
        "_TOTINDA",
        "_STATE",
        "_URBSTAT",
        "CHECKUP1",
        "GENHLTH",
        "PHYSHLTH",
        "CHILDREN",
        "RENTHOM1",
        "MEDCOST1",
        "PERSDOC3",
    ]
    features = [c for c in feature_candidates if c in all_data.columns]

    model_data = all_data[features + ["year", "mental_low", "chronic_any", "target"]].copy()
    for col in features:
        if pd.api.types.is_numeric_dtype(model_data[col]):
            model_data[col] = clean_missing(model_data[col])

    return model_data


def main() -> None:
    all_data, common_cols_df = build_dataset()

    # BEFORE: raw merged sample (same rows used later for AFTER)
    sample_idx = all_data.sample(5000, random_state=42).index
    before_df = all_data.loc[sample_idx].copy()

    # AFTER: preprocessed sample for direct comparison
    model_data = preprocessing(all_data.copy())
    after_df = model_data.loc[sample_idx].copy()

    before_xlsx = OUT / "brfss_before_preprocessing_sample.xlsx"
    after_xlsx = OUT / "brfss_after_preprocessing_sample.xlsx"
    common_cols_csv = OUT / "common_cols.csv"
    before_csv = OUT / "brfss_before_preprocessing_sample.csv"
    after_csv = OUT / "brfss_after_preprocessing_sample.csv"

    before_df.to_excel(before_xlsx, index=False)
    after_df.to_excel(after_xlsx, index=False)
    before_df.to_csv(before_csv, index=False, sep=";")
    after_df.to_csv(after_csv, index=False, sep=";")
    common_cols_df.to_csv(common_cols_csv, index=False)

    print("Saved:")
    print(before_xlsx)
    print(after_xlsx)
    print(before_csv)
    print(after_csv)
    print(common_cols_csv)
    print("Shapes:")
    print("before_df:", before_df.shape)
    print("after_df :", after_df.shape)


if __name__ == "__main__":
    main()

