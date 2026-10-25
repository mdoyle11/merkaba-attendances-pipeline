import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    M2M_TOKEN = os.getenv("M2M_TOKEN")
    SHEET_ID = os.getenv("SHEET_ID")

    APP_PASSWORD = os.getenv("APP_PASSWORD")
    SENDER_EMAIL = os.getenv("SENDER_EMAIL")
    RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

    @classmethod
    def ensure_token(cls):
        if not cls.M2M_TOKEN:
            raise ValueError("Missing M2M Token")

    @classmethod
    def ensure_sheet(cls):
        if not cls.SHEET_ID:
            raise ValueError("Missing Google Sheet ID")