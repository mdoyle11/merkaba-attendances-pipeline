# src/utils/logger.py
import logging
import os


def setup_logger(name: str = "attendance_etl") -> logging.Logger:
  """Configures logging for Google Cloud Logging with local fallback."""
  log_instance = logging.getLogger(name)
  log_instance.setLevel(logging.INFO)

  # Prevent adding duplicate handlers if logger is called multiple times
  if log_instance.handlers:
    return log_instance

  # Check if running in GCP Cloud Run or container with GCP credentials
  if os.getenv("K_SERVICE") or os.getenv("GSPREAD_CREDENTIALS_JSON"):
    try:
      import google.cloud.logging

      client = google.cloud.logging.Client()
      # Attaches GCP handler to root Python logger
      client.setup_logging()
      return logging.getLogger(name)
    except Exception:
      # Fallback to standard console logging if GCP client fails to initialize
      pass

  # Standard console logger for local development / testing
  handler = logging.StreamHandler()
  formatter = logging.Formatter(
      "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  )
  handler.setFormatter(formatter)
  log_instance.addHandler(handler)

  return log_instance


# Export global logger instance for imports like: from src.utils.logger import logger
logger = setup_logger()