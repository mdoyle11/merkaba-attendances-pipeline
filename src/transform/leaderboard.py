import pandas as pd

# src/transformers/attendance.py

def normalize_id(series: pd.Series) -> pd.Series:
    """Scubs floats, NaNs, and Excel/Sheets <NA> strings into clean integer strings or empty strings."""
    if series is None or series.empty:
        return pd.Series(dtype=str)

    return (
        series.astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .replace({"<NA>": "", "NaN": "", "nan": "", "None": "", "null": "", "#N/A": ""})
    )

def build_lifetime_leaderboard(df_sb: pd.DataFrame, df_tu: pd.DataFrame) -> pd.DataFrame:

    df_sb = df_sb.copy()
    df_tu = df_tu.copy()

    df_sb["clean_id"] = normalize_id(df_sb["TeamUp ID"])
    df_tu["clean_id"] = normalize_id(df_tu["ID"])

    df_merged = pd.merge(
        df_sb,
        df_tu,
        on="clean_id",
        how="outer",
        suffixes=("_studiobookings", "_teamup")
    )

    df_merged["Attendances_studiobookings"] = df_merged["Attendances_studiobookings"].fillna(0).astype(int)
    df_merged["Attendances_teamup"] = df_merged["Attendances_teamup"].fillna(0).astype(int)
    df_merged["Lifetime Attendances"] = df_merged["Attendances_studiobookings"] + df_merged["Attendances_teamup"]
    df_merged["Lifetime Attendances"] = df_merged["Lifetime Attendances"].fillna(0).astype(int)

    df_merged["ID"] = normalize_id(df_merged["clean_id"])
    df_merged["ID"] = df_merged["clean_id"]
    df_merged["Customer"] = df_merged["Customer_teamup"].combine_first(df_merged["Customer_studiobookings"])
    df_merged["Email"] = df_merged["Email_teamup"].combine_first(df_merged["Email_studiobookings"])
    lifetime_leaderboard = df_merged[
                                    ["ID", "Customer", "Email", "Attendances_studiobookings", "Attendances_teamup", "Lifetime Attendances"]
                                    ].sort_values(by="Lifetime Attendances", ascending=False)
    return lifetime_leaderboard