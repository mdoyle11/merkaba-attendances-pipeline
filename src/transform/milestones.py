# src/transform/milestones.py
import pandas as pd
from src.config import Config
from src.transform.leaderboard import normalize_id
from src.utils.logger import logger

DEFAULT_MILESTONES = Config.MILESTONES


def check_milestone_crossings(
    df_old: pd.DataFrame,
    df_new: pd.DataFrame,
    milestones: list[int] = DEFAULT_MILESTONES,
) -> list[dict]:
  """Compares previous and current lifetime attendances to detect milestone crossings."""
  if df_old is None or df_old.empty:
    logger.warning(
        "Previous leaderboard DataFrame is empty or None. Skipping milestone"
        " checks."
    )
    return []

  if df_new is None or df_new.empty:
    logger.warning("New leaderboard DataFrame is empty. No milestones to check.")
    return []

  logger.info("Evaluating milestone crossings between previous and current run...")

  old_df = df_old.copy()
  new_df = df_new.copy()

  # Ensure expected columns exist
  for df, name in [(old_df, "old"), (new_df, "new")]:
    for col in ["ID", "Customer", "Email", "Lifetime Attendances"]:
      if col not in df.columns:
        df[col] = ""

  # 1. Normalize IDs and attendance counts
  old_df["clean_id"] = normalize_id(old_df["ID"])
  new_df["clean_id"] = normalize_id(new_df["ID"])

  old_df["clean_email"] = (
      old_df["Email"].astype(str).str.strip().str.lower()
  )
  new_df["clean_email"] = (
      new_df["Email"].astype(str).str.strip().str.lower()
  )

  old_df["Lifetime Attendances"] = (
      pd.to_numeric(old_df["Lifetime Attendances"], errors="coerce")
      .fillna(0)
      .astype(int)
  )
  new_df["Lifetime Attendances"] = (
      pd.to_numeric(new_df["Lifetime Attendances"], errors="coerce")
      .fillna(0)
      .astype(int)
  )

  # 2. Build lookups for historical counts (Primary: ID, Fallback: Email)
  id_map = {}
  email_map = {}

  for _, row in old_df.iterrows():
    cid = str(row["clean_id"]).strip()
    email = str(row["clean_email"]).strip()
    count = row["Lifetime Attendances"]

    if cid:
      id_map[cid] = count
    if email and email not in {"", "none", "null", "no email associated"}:
      email_map[email] = count

  new_achievers = []

  # 3. Check for milestones
  for _, row in new_df.iterrows():
    cid = str(row["clean_id"]).strip()
    email = str(row["clean_email"]).strip()
    new_count = row["Lifetime Attendances"]

    # Match by ID first, then fallback to Email
    old_count = None
    if cid and cid in id_map:
      old_count = id_map[cid]
    elif email and email in email_map:
      old_count = email_map[email]

    if old_count is None or new_count <= old_count:
      continue

    for ms in sorted(milestones):
      if old_count < ms <= new_count:
        achiever = {
            "customer": row["Customer"],
            "email": row["Email"],
            "milestone": ms,
            "previous": old_count,
            "current": new_count,
        }
        new_achievers.append(achiever)
        logger.info(
            f"🎉 Milestone Detected: {achiever['customer']} reached {ms} classes!"
            f" ({old_count} -> {new_count})"
        )

  logger.info(
      f"Milestone check finished. Total milestones crossed in this run:"
      f" {len(new_achievers)}"
  )
  return new_achievers