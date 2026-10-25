# src/clients/email.py
from datetime import datetime
import smtplib
from email.message import EmailMessage
import pandas as pd
from src.config import Config
from src.utils.logger import logger


class EmailClient:
  """Delivers automated pipeline email reports via Gmail SMTP."""

  def __init__(self):
    self.sender_email = Config.SENDER_EMAIL
    self.sender_password = Config.APP_PASSWORD
    self.recipient_email = Config.RECIPIENT_EMAIL
    self.smtp_server = "smtp.gmail.com"
    self.smtp_port = 465

  def send_pipeline_report(
      self, df_lifetime: pd.DataFrame, milestones_achieved: list[dict] = None
  ) -> None:
    """Sends an HTML email report with top stats and a direct link to Google Sheets."""
    if not self.sender_email or not self.sender_password:
      logger.warning(
          "Email credentials not configured. Skipping email report."
      )
      return

    # Format current date (e.g., "Oct 26, 2026")
    today_str = datetime.now().strftime("%b %d, %Y")

    logger.info(
        f"Preparing pipeline report email for {self.recipient_email}..."
    )

    msg = EmailMessage()
    # Dynamic subject with run date
    msg["Subject"] = f"📊 Attendance Leaderboard Summary — {today_str}"
    msg["From"] = self.sender_email
    msg["To"] = self.recipient_email

    sheet_url = f"https://docs.google.com/spreadsheets/d/{Config.SHEET_ID}"
    top_10_html = df_lifetime.head(10).to_html(index=False, border=0)

    # Format milestone section
    milestone_html = ""
    if milestones_achieved:
      logger.info(
          f"Formatting {len(milestones_achieved)} milestone achievements for"
          " email summary."
      )
      items = "".join([
          (
              "<li>"
              f"<strong>{m['customer']}</strong> reached"
              f" <strong>{m['milestone']} classes</strong>!"
              f" (Previous: {m['previous']} → Current: {m['current']})"
              "</li>"
          )
          for m in milestones_achieved
      ])
      milestone_html = f"""
            <div style="background-color: #f0fdf4; border: 1px solid #22c55e; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                <h3 style="color: #15803d; margin-top: 0;">🎉 Milestone Achievements</h3>
                <ul>{items}</ul>
            </div>
            """

    html_content = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <h2>Weekly Lifetime Attendance Leaderboard Summary ({today_str})</h2>
            {milestone_html}
            <h3>Top 10 Lifetime Attendance</h3>
            {top_10_html}
            <br>
            <p><a href="{sheet_url}">👉 <strong>Open Master Google Sheet</strong></a></p>
          </body>
        </html>
        """
    msg.add_alternative(html_content, subtype="html")

    try:
      with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
        server.login(self.sender_email, self.sender_password)
        server.send_message(msg)
      logger.info(f"Email report successfully sent to {self.recipient_email}!")
    except Exception as e:
      logger.error(f"Failed to send pipeline report email: {e}", exc_info=True)