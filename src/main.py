import sys
from src.clients.email import EmailClient
from src.clients.gsheets import SheetsClient
from src.clients.teamup import TeamUpClient
from src.config import Config
from src.transform.leaderboard import build_lifetime_leaderboard
from src.transform.milestones import check_milestone_crossings
from src.utils.logger import logger


def run_pipeline() -> None:
  """Executes the Attendance ETL Pipeline end-to-end."""
  logger.info("Initializing Attendance ETL pipeline run...")

  # 1. Configuration & Validation
  logger.info("Validating configuration tokens and sheet parameters...")
  Config.ensure_token()
  Config.ensure_sheet()

  # 2. Initialize Clients
  logger.info("Initializing API clients (TeamUp, Google Sheets, Email)...")
  teamup_client = TeamUpClient()
  sheets_client = SheetsClient()
  email_client = EmailClient()

  # 3. Extract Data
  logger.info(
      "Extracting StudioBookings history from Google Sheets and fetching TeamUp"
      " attendances..."
  )
  df_sb = sheets_client.read_sheet(sheet_name="StudioBookings History")
  df_tu = teamup_client.get_attendances()
  logger.info(
      f"Extracted {len(df_sb)} StudioBookings records and {len(df_tu)} TeamUp"
      " attendance records."
  )

  # 4. Process and Overwrite TeamUp Attendance Sheet
  logger.info("Sorting TeamUp attendance data and updating Google Sheets...")
  df_tu = df_tu.sort_values(by="Attendances", ascending=False)
  sheets_client.overwrite_sheet(sheet_name="TeamUp Attendance", df=df_tu)

  # 5. Build Leaderboard & Check Milestones
  logger.info("Reading current Lifetime Leaderboard state for comparison...")
  df_old_leaderboard = sheets_client.read_sheet(
      sheet_name="Lifetime Leaderboard"
  )

  logger.info(
      "Building new combined Lifetime Leaderboard and checking milestone"
      " crossings..."
  )
  df_new_leaderboard = build_lifetime_leaderboard(df_sb=df_sb, df_tu=df_tu)
  milestones_achieved = check_milestone_crossings(
      df_old=df_old_leaderboard, df_new=df_new_leaderboard
  )
  logger.info(
      f"Leaderboard build complete ({len(df_new_leaderboard)} members)."
      f" Milestones achieved in this run: {len(milestones_achieved)}"
  )

  # 6. Update Leaderboard Sheet
  logger.info("Overwriting Lifetime Leaderboard sheet with updated counts...")
  sheets_client.overwrite_sheet(
      sheet_name="Lifetime Leaderboard", df=df_new_leaderboard
  )

  # 7. Send Notifications
  logger.info("Sending pipeline execution summary email report...")
  email_client.send_pipeline_report(
      df_lifetime=df_new_leaderboard, milestones_achieved=milestones_achieved
  )

  logger.info("Attendance ETL pipeline completed successfully!")


if __name__ == "__main__":
  try:
    run_pipeline()
    sys.exit(0)
  except Exception as e:
    logger.error(
        f"ETL Pipeline execution failed due to an unhandled error: {e}",
        exc_info=True,
    )
    sys.exit(1)