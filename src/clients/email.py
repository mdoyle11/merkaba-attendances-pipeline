# src/clients/email.py
import smtplib
from email.message import EmailMessage
import pandas as pd
from src.config import Config


class EmailClient:
    """Delivers automated pipeline email reports via Gmail SMTP."""

    def __init__(self):
        self.sender_email = Config.SENDER_EMAIL
        self.sender_password = Config.APP_PASSWORD
        self.recipient_email = Config.RECIPIENT_EMAIL
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 465

    def send_pipeline_report(
        self, df_lifetime: pd.DataFrame
    ) -> None:
        """Sends an HTML email report with top stats and a direct link to Google Sheets."""
        msg = EmailMessage()
        msg["Subject"] = "📊 Attendance Leaderboard Sync Weekly Summary"
        msg["From"] = self.sender_email
        msg["To"] = self.recipient_email

        sheet_url = f"https://docs.google.com/spreadsheets/d/{Config.SHEET_ID}"
        top_10_html = df_lifetime.head(10).to_html(index=False, border=0)

        html_content = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <h2>Lifetime Attendance Summary</h2>
            <p>The latest attendance records have been merged into the master spreadsheet.</p>
            <h3>Top 10 Lifetime Attendance</h3>
            {top_10_html}
            <br>
            <p><a href="{sheet_url}">👉 <strong>Open Master Google Sheet</strong></a></p>
          </body>
        </html>
        """
        msg.add_alternative(html_content, subtype="html")

        # Authenticate and send
        with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)

        print("[EmailClient] Email report sent successfully!")