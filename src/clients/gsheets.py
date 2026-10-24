import os
import gspread
import pandas as pd
from src.config import Config

class SheetsClient:

    WRITE_SHEETS = {"TeamUp Attendance", "Lifetime Leaderboard"}

    def __init__(self, worksheet_id: str = None):
        self.sheet_id = worksheet_id or Config.SHEET_ID

        if os.path.exists("secrets/credentials.json"):
            self.gc = gspread.service_account(filename="secrets/credentials.json")
        else:
            self.gc = gspread.service_account_auto()

        self.spreadsheet = self.gc.open_by_key(self.sheet_id)

    def read_studiobookings_attendances(self):
        history = self.spreadsheet.worksheet("StudioBookings History")
        records = history.get_all_records()
        if not records:
            raise ValueError("Missing StudioBookings attendances")

        df = pd.DataFrame(records)
        return df

    def overwrite_sheet(self, sheet_name: str, df: pd.DataFrame):
        if sheet_name not in self.WRITE_SHEETS:
            raise PermissionError(f"Protected tab: Cannot overwrite StudioBookings sheet: {sheet_name}.")
        tab = self.spreadsheet.worksheet(sheet_name)
        data_matrix = [df.columns.values.tolist()] + df.values.tolist()
        try:
            tab.clear()
            tab.update(range_name="A1", values=data_matrix)
        except Exception as e:
            print(f"Failed to update sheet: {e}")

        print(f"Successfully updated sheet: {sheet_name}")

if __name__ == "__main__":
    from src.clients.teamup import TeamUpClient
    teamup_client = TeamUpClient()
    attendances = teamup_client.get_attendances()
    df = pd.DataFrame(attendances)
    df = df.sort_values(by="count", ascending=False)
    sheets_client = SheetsClient()
    sheets_client.overwrite_sheet("TeamUp Attendance", df)