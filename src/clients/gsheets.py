import json
import os
import gspread
import pandas as pd
from src.config import Config
from src.utils.logger import logger


class SheetsClient:

  WRITE_SHEETS = {"TeamUp Attendance", "Lifetime Leaderboard"}

  def __init__(self, worksheet_id: str = None):
    self.sheet_id = worksheet_id or Config.SHEET_ID
    creds_json = os.getenv("GSPREAD_CREDENTIALS_JSON")

    if creds_json:
      # Load directly from environment variable string (Docker & Cloud Run)
      creds_dict = json.loads(creds_json)
      self.gc = gspread.service_account_from_dict(creds_dict)
    else:
      # Fall back to default local JSON file path for local runs
      local_path = os.getenv(
          "GOOGLE_APPLICATION_CREDENTIALS", "secrets/credentials.json"
      )
      self.gc = gspread.service_account(filename=local_path)

    logger.info(f"Opening Google Spreadsheet by ID: {self.sheet_id}")
    self.spreadsheet = self.gc.open_by_key(self.sheet_id)

  def read_sheet(self, sheet_name: str) -> pd.DataFrame:
    """Reads all records from a specified worksheet into a pandas DataFrame."""
    logger.info(f"Reading worksheet: '{sheet_name}'")
    try:
      sheet = self.spreadsheet.worksheet(sheet_name)
      records = sheet.get_all_records()
    except Exception as err:
      logger.error(f"Failed to read worksheet '{sheet_name}': {err}")
      raise

    if not records and sheet_name == "StudioBookings History":
      logger.error(f"Sheet '{sheet_name}' is unexpectedly empty.")
      raise ValueError(f"Sheet '{sheet_name}' unexpectedly empty, aborting...")

    df = pd.DataFrame(records)
    logger.info(
        f"Successfully read {len(df)} rows from worksheet '{sheet_name}'."
    )
    return df

  def overwrite_sheet(self, sheet_name: str, df: pd.DataFrame) -> None:
    """Sanitizes data and overwrites the target worksheet."""
    if sheet_name not in self.WRITE_SHEETS:
      logger.error(
        f"Attempted write to protected tab '{sheet_name}'. Action blocked."
      )
      raise PermissionError(
          f"Protected tab: Cannot overwrite sheet '{sheet_name}'."
      )

    tab = self.spreadsheet.worksheet(sheet_name)

    # Sanitize string representations of nulls and NA values
    df = df.fillna("")
    df = df.astype(str).replace({
        "<NA>": "",
        "NaN": "",
        "nan": "",
        "None": "",
        "null": "",
        "#N/A": "",
    })

    data_matrix = [df.columns.values.tolist()] + df.values.tolist()

    try:
      logger.info(
          f"Clearing and updating worksheet '{sheet_name}' with"
          f" {len(df)} rows..."
      )
      tab.clear()
      tab.update(range_name="A1", values=data_matrix)
      logger.info(f"Successfully updated worksheet '{sheet_name}'.")
    except Exception as e:
      logger.error(f"Failed to update worksheet '{sheet_name}': {e}")
      raise


if __name__ == "__main__":
  from src.clients.teamup import TeamUpClient

  teamup_client = TeamUpClient()
  attendances = teamup_client.get_attendances()
  sheets_client = SheetsClient()
  sheets_client.overwrite_sheet("TeamUp Attendance", attendances)