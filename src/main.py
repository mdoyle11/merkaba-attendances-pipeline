import pandas as pd
from src.config import Config
from src.clients.teamup import TeamUpClient
from src.clients.gsheets import SheetsClient
from src.clients.email import EmailClient
from src.transform.leaderboard import build_lifetime_leaderboard
from src.transform.milestones import check_milestone_crossings

Config.ensure_token()
Config.ensure_sheet()

teamup_client = TeamUpClient()
sheets_client = SheetsClient()
email_client = EmailClient()

df_sb = sheets_client.read_sheet(sheet_name="StudioBookings History")
df_tu = teamup_client.get_attendances()

df_tu = df_tu.sort_values(by="Attendances", ascending=False)
sheets_client.overwrite_sheet(sheet_name="TeamUp Attendance", df=df_tu)

df_old_leaderboard = sheets_client.read_sheet(sheet_name="Lifetime Leaderboard")
df_old_lifetime = sheets_client.read_sheet(sheet_name="Lifetime Leaderboard")
# print("[Debug] Old Sheet Head:\n", df_old_lifetime.head(2))
# print("[Debug] Old Sheet Columns:", list(df_old_lifetime.columns))
# print("[Debug] Old Sheet Data Types:\n", df_old_lifetime.dtypes)
df_new_leaderboard = build_lifetime_leaderboard(df_sb=df_sb, df_tu=df_tu)

milestones_achieved = check_milestone_crossings(df_old=df_old_leaderboard, df_new=df_new_leaderboard)

sheets_client.overwrite_sheet(sheet_name="Lifetime Leaderboard", df=df_new_leaderboard)

email_client.send_pipeline_report(df_lifetime=df_new_leaderboard, milestones_achieved=milestones_achieved)