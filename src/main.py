import pandas as pd
from src.config import Config
from src.clients.teamup import TeamUpClient
from src.clients.gsheets import SheetsClient

Config.ensure_token()
Config.ensure_sheet()

teamup_client = TeamUpClient()
sheets_client = SheetsClient()

df_sb = sheets_client.read_studiobookings_attendances()

teamup_attendances = teamup_client.get_attendances()
df_tu = pd.DataFrame(teamup_attendances)
df_tu = df_tu.sort_values(by="Attendances", ascending=False)
sheets_client.overwrite_sheet(sheet_name="TeamUp Attendance", df=df_tu)

df_tu["ID"] = df_tu["ID"].astype(str).str.strip()
df_sb["TeamUp ID"] = df_sb["TeamUp ID"].astype(str).str.strip()

df_merged = pd.merge(
    df_sb,
    df_tu,
    left_on="TeamUp ID",
    right_on="ID",
    how="outer",
    suffixes=("_studiobookings", "_teamup")
)

df_merged["Attendances_studiobookings"] = df_merged["Attendances_studiobookings"].fillna(0).astype(int)
df_merged["Attendances_teamup"] = df_merged["Attendances_teamup"].fillna(0).astype(int)
df_merged["Lifetime Attendances"] = df_merged["Attendances_studiobookings"] + df_merged["Attendances_teamup"]
df_merged["Lifetime Attendances"] = df_merged["Lifetime Attendances"].fillna(0).astype(int)

df_merged["Customer"] = df_merged["Customer_teamup"].combine_first(df_merged["Customer_studiobookings"])
df_merged["Email"] = df_merged["Email_teamup"].combine_first(df_merged["Email_studiobookings"])
lifetime_leaderboard = df_merged[
                                ["ID", "Customer", "Email", "Attendances_studiobookings", "Attendances_teamup", "Lifetime Attendances"]
                                ].sort_values(by="Lifetime Attendances", ascending=False)
sheets_client.overwrite_sheet(sheet_name="Lifetime Leaderboard", df=lifetime_leaderboard)