# src/config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
  """Centralized configuration and secret validation."""

  # API & Sheet Identifiers
  M2M_TOKEN = os.getenv("M2M_TOKEN").strip()
  SHEET_ID = os.getenv("SHEET_ID").strip()

  # Email / Notification Credentials
  APP_PASSWORD = os.getenv("APP_PASSWORD")
  SENDER_EMAIL = os.getenv("SENDER_EMAIL")
  RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

  # Attendance Milestones
  MILESTONES = [25, 50, 75, 100, 150, 200, 250, 500]

  @classmethod
  def ensure_token(cls) -> str:
    """Ensures TeamUp M2M token is present."""
    if not cls.M2M_TOKEN:
      raise ValueError("Missing M2M Token.")
    return cls.M2M_TOKEN

  @classmethod
  def ensure_sheet(cls) -> str:
    """Ensures Google Sheet ID is present."""
    if not cls.SHEET_ID:
      raise ValueError("Missing Google Sheet ID.")
    return cls.SHEET_ID