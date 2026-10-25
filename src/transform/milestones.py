# src/transformers/attendance.py
import pandas as pd
from src.config import Config
from src.transform.leaderboard import normalize_id

DEFAULT_MILESTONES = Config.MILESTONES


def check_milestone_crossings(
    df_old: pd.DataFrame,
    df_new: pd.DataFrame,
    milestones: list[int] = DEFAULT_MILESTONES,
) -> list[dict]:
    """Compares previous and current lifetime attendances using normalized ID."""
    if df_old is None or df_old.empty:
        return []

    old_df = df_old.copy()
    new_df = df_new.copy()

    # 1. Normalize IDs and attendance counts
    old_df["clean_id"] = normalize_id(old_df["ID"])
    new_df["clean_id"] = normalize_id(new_df["ID"])

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

    # 2. Build ID map - ONLY for non-empty, truthy IDs
    id_map = {}
    for _, row in old_df.iterrows():
        cid = str(row["clean_id"]).strip()
        if cid:  # Strictly ignores empty strings, NaNs, and whitespace
            id_map[cid] = row["Lifetime Attendances"]

    new_achievers = []

    # 3. Check for milestones
    for _, row in new_df.iterrows():
        cid = str(row["clean_id"]).strip()

        # Skip members without a valid ID
        if not cid or cid not in id_map:
            continue

        old_count = id_map[cid]
        new_count = row["Lifetime Attendances"]

        if new_count <= old_count:
            continue

        for ms in sorted(milestones):
            if old_count < ms <= new_count:
                new_achievers.append({
                    "customer": row["Customer"],
                    "email": row["Email"],
                    "milestone": ms,
                    "previous": old_count,
                    "current": new_count,
                })

    return new_achievers