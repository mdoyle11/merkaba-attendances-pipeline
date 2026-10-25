import pandas as pd
from src.utils.logger import logger


def normalize_id(series: pd.Series) -> pd.Series:
  """Scrubs floats, NaNs, and Excel/Sheets <NA> strings into clean integer strings or empty strings."""
  if series is None or series.empty:
    return pd.Series(dtype=str)

  return (
      series.astype(str)
      .str.strip()
      .str.replace(r"\.0$", "", regex=True)
      .replace(
          {"<NA>": "", "NaN": "", "nan": "", "None": "", "null": "", "#N/A": ""}
      )
  )


def build_lifetime_leaderboard(
    df_sb: pd.DataFrame, df_tu: pd.DataFrame
) -> pd.DataFrame:
  """Merges StudioBookings history and TeamUp attendance into a unified Lifetime Leaderboard."""
  logger.info("Building Lifetime Leaderboard from StudioBookings & TeamUp...")

  df_sb = df_sb.copy()
  df_tu = df_tu.copy()

  # Ensure expected ID columns exist
  if "TeamUp ID" not in df_sb.columns:
    df_sb["TeamUp ID"] = ""
  if "ID" not in df_tu.columns:
    df_tu["ID"] = ""

  df_sb["clean_id"] = normalize_id(df_sb["TeamUp ID"])
  df_tu["clean_id"] = normalize_id(df_tu["ID"])

  logger.info(
      f"Merging {len(df_sb)} StudioBookings records with {len(df_tu)} TeamUp"
      " records..."
  )

  df_merged = pd.merge(
      df_sb,
      df_tu,
      on="clean_id",
      how="outer",
      suffixes=("_studiobookings", "_teamup"),
  )

  # Calculate combined attendance
  df_merged["Attendances_studiobookings"] = (
      df_merged.get("Attendances_studiobookings", pd.Series(dtype=float))
      .fillna(0)
      .astype(int)
  )
  df_merged["Attendances_teamup"] = (
      df_merged.get("Attendances_teamup", pd.Series(dtype=float))
      .fillna(0)
      .astype(int)
  )

  df_merged["Lifetime Attendances"] = (
      df_merged["Attendances_studiobookings"] + df_merged["Attendances_teamup"]
  )

  # Coalesce customer demographics
  df_merged["ID"] = df_merged["clean_id"]

  cust_tu = df_merged.get(
      "Customer_teamup", pd.Series(index=df_merged.index, dtype=str)
  )
  cust_sb = df_merged.get(
      "Customer_studiobookings", pd.Series(index=df_merged.index, dtype=str)
  )
  df_merged["Customer"] = cust_tu.combine_first(cust_sb)

  email_tu = df_merged.get(
      "Email_teamup", pd.Series(index=df_merged.index, dtype=str)
  )
  email_sb = df_merged.get(
      "Email_studiobookings", pd.Series(index=df_merged.index, dtype=str)
  )
  df_merged["Email"] = email_tu.combine_first(email_sb)

  # Filter and sort
  lifetime_leaderboard = df_merged[[
      "ID",
      "Customer",
      "Email",
      "Attendances_studiobookings",
      "Attendances_teamup",
      "Lifetime Attendances",
  ]].sort_values(by="Lifetime Attendances", ascending=False)

  logger.info(
      "Lifetime Leaderboard build complete."
      f" Total unique members: {len(lifetime_leaderboard)}"
  )
  return lifetime_leaderboard