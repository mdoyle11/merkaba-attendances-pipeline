import httpx
import pandas as pd
from src.config import Config
from src.utils.logger import logger


class TeamUpClient:

  def __init__(self, m2m_token: str = None):
    self.token = m2m_token or Config.M2M_TOKEN
    self.url = "https://goteamup.com/api/v2/reports/attendances.grouped/data"
    self.headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {self.token}",
    }

  def get_attendances(self) -> pd.DataFrame:
    """Fetches and paginates through all attended customer counts from TeamUp API."""
    next_url = self.url
    params = [("columns", "customer"), ("attendance_status[]", "attended")]
    attendances = []
    page_count = 0

    logger.info("Initiating TeamUp API attendance extraction...")

    with httpx.Client() as client:
      while next_url:
        page_count += 1
        logger.info(f"Fetching TeamUp attendance page {page_count}...")

        try:
          response = client.get(
              url=next_url,
              headers=self.headers,
              params=params if next_url == self.url else None,
              timeout=30.0,
          )
          response.raise_for_status()
        except httpx.HTTPStatusError as err:
          logger.error(
              f"TeamUp API HTTP Error ({err.response.status_code}):"
              f" {err.response.text}"
          )
          raise
        except httpx.RequestError as err:
          logger.error(f"TeamUp API Network Request failed: {err}")
          raise

        data = response.json()
        rows = data.get("rows", [])
        if not rows:
          logger.info("Reached end of TeamUp pagination (no more rows).")
          break

        for row in rows:
          customer_obj = row.get("customer", {})
          cust_id = (
              customer_obj.get("id")
              or row.get("customer.id")
              or "ID Not Found"
          )
          name = (
              customer_obj.get("name")
              or row.get("customer.name")
              or "Unknown Customer"
          )
          email = (
              customer_obj.get("email")
              or row.get("customer.email")
              or "No Email Associated"
          )
          count = row.get("count", 0)

          attendances.append({
              "ID": cust_id,
              "Customer": name,
              "Email": email,
              "Attendances": count,
          })

        next_url = data.get("next")

    if not attendances:
      logger.warning("TeamUp API returned zero attendance records.")
      return pd.DataFrame(columns=["ID", "Customer", "Email", "Attendances"])

    df_attendances = pd.DataFrame(attendances)
    logger.info(
        f"Successfully extracted {len(df_attendances)} records across"
        f" {page_count} pages from TeamUp."
    )
    return df_attendances


if __name__ == "__main__":
  client = TeamUpClient()
  attendances = client.get_attendances()
  print(attendances.head())