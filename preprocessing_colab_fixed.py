from __future__ import annotations

from pathlib import Path
import pandas as pd


# -----------------------------------------------------------------------------
# 1) PATHS
# -----------------------------------------------------------------------------
# Set this path in Colab, e.g.:
# BASE = Path("/content/drive/MyDrive/your_folder/data_raw/brfss")
BASE = Path(r"C:\Users\Radek\Documents\New project\data_raw\brfss")

FILES = {
    2022: BASE / "LLCP2022.XPT",
    2023: BASE / "LLCP2023.XPT",
    2024: BASE / "LLCP2024.XPT",
}


def validate_files(files: dict[int, Path]) -> None:
    missing = [f"{y}: {p}" for y, p in files.items() if not p.exists()]
    if missing:
        msg = "Missing files:\n" + "\n".join(missing)
        raise FileNotFoundError(msg)


def load_data(file_path: Path, n_rows: int = 50_000, chunk_size: int = 10_000) -> pd.DataFrame:
    """Load only first n_rows from a SAS XPT file."""
    reader = pd.read_sas(file_path, format="xport", chunksize=chunk_size)
    parts: list[pd.DataFrame] = []
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


def decode_bytes_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Convert b'...' columns to readable strings for display in Colab."""
    out = df.copy()
    for col in out.columns:
        if out[col].dtype == "object":
            out[col] = out[col].map(
                lambda x: x.decode("utf-8", "ignore") if isinstance(x, (bytes, bytearray)) else x
            )
    return out


def clean_missing(series: pd.Series) -> pd.Series:
    """
    BRFSS missing cleanup:
    - standard survey missing codes (7/8/9 variants)
    - very small SAS special-missing float artifacts from XPT readers
    """
    s = series.replace([7, 8, 9, 77, 88, 99, 777, 888, 999], pd.NA)
    if pd.api.types.is_numeric_dtype(s):
        s = s.mask((s.abs() > 0) & (s.abs() < 1e-70), pd.NA)
    return s


def build_merged_dataset(files: dict[int, Path], n_rows: int = 50_000) -> pd.DataFrame:
    d2022 = load_data(files[2022], n_rows=n_rows)
    d2023 = load_data(files[2023], n_rows=n_rows)
    d2024 = load_data(files[2024], n_rows=n_rows)

    d2022["year"] = 2022
    d2023["year"] = 2023
    d2024["year"] = 2024

    # Intersection across all years to avoid KeyError later.
    common_cols = sorted(set(d2022.columns) & set(d2023.columns) & set(d2024.columns))
    all_data = pd.concat(
        [d2022[common_cols], d2023[common_cols], d2024[common_cols]],
        ignore_index=True,
    )
    return all_data


def add_target_columns(all_data: pd.DataFrame) -> tuple[pd.DataFrame, list[str], list[str]]:
    data = all_data.copy()

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

    mental_present = [c for c in mental_candidates if c in data.columns]
    chronic_present = [c for c in chronic_candidates if c in data.columns]

    if "MENTHLTH" in data.columns:
        m = clean_missing(data["MENTHLTH"])
        data["mental_low"] = (m >= 14).astype("Int64")
    elif "_MENT14D" in data.columns:
        m14 = clean_missing(data["_MENT14D"])
        data["mental_low"] = (m14 == 1).astype("Int64")
    else:
        raise ValueError("Brak MENTHLTH i _MENT14D - nie mozna zbudowac mental_low.")

    if not chronic_present:
        raise ValueError("Brak kolumn chorob przewleklych w merged dataset.")

    flags = []
    for col in chronic_present:
        s = clean_missing(data[col])
        flags.append((s == 1).fillna(False))

    data["chronic_any"] = pd.concat(flags, axis=1).any(axis=1).astype("Int64")
    data["target"] = ((data["mental_low"] == 1) & (data["chronic_any"] == 1)).astype("Int64")

    return data, mental_present, chronic_present


def build_model_table(
    data_with_target: pd.DataFrame,
    mental_present: list[str],
    chronic_present: list[str],
) -> tuple[pd.DataFrame, list[str]]:
    base_candidates = [
        "_AGEG5YR",
        "_SEX",
        "_RACE",
        "EDUCA",
        "INCOME3",
        "EMPLOY1",
        "MARITAL",
        "_BMI5",
        "_RFSMOK3",
        "_RFDRHV8",
        "_TOTINDA",
        "_FRTLT1A",
        "_VEGLT1A",
        "_PASTRNG",
        "_SLEEP",
        "_STATE",
        "_URBSTAT",
        "CHECKUP1",
        "HLTHPLN1",
        "GENHLTH",
    ]

    extra_candidates = [
        "PHYSHLTH",
        "SLEPTIM1",
        "CHILDREN",
        "RENTHOM1",
        "MEDCOST1",
        "PERSDOC3",
        "EXERANY2",
        "FRUIT2",
        "VEGETAB1",
        "_RFHLTH",
        "_PA150R4",
        "_RFBING6",
        "_DRDXAR2",
        "_RFHYPE6",
    ]

    data = data_with_target.copy()
    features = [c for c in base_candidates if c in data.columns]

    forbidden = set(["target", "year", "mental_low", "chronic_any"] + mental_present + chronic_present)
    available_extras = [c for c in extra_candidates if c in data.columns and c not in features and c not in forbidden]

    target_feature_count = 18
    need = max(0, target_feature_count - len(features))
    selected_extras = available_extras[:need]
    features = features + selected_extras

    model_data = data[features + ["target", "year"]].copy()
    for col in features:
        if pd.api.types.is_numeric_dtype(model_data[col]):
            model_data[col] = clean_missing(model_data[col])

    return model_data, features


def run_pipeline(n_rows: int = 50_000) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    validate_files(FILES)

    all_data = build_merged_dataset(FILES, n_rows=n_rows)
    data_with_target, mental_present, chronic_present = add_target_columns(all_data)
    model_data, features = build_model_table(data_with_target, mental_present, chronic_present)

    print("all_data shape:", all_data.shape)
    print("data_with_target shape:", data_with_target.shape)
    print("model_data shape:", model_data.shape)
    print("features:", features)
    print("target distribution:")
    print(model_data["target"].value_counts(dropna=False))
    print("target rate (%):", round(model_data["target"].mean() * 100, 2))

    # For Colab readability: decode byte columns in raw sample.
    all_data_display = decode_bytes_columns(all_data)

    return all_data_display, model_data, features


if __name__ == "__main__":
    all_data_display_df, model_data_df, feature_list = run_pipeline()
    print("\nSample BEFORE (decoded):")
    print(all_data_display_df.head(3))
    print("\nSample AFTER:")
    print(model_data_df.head(3))
