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
        self, df_lifetime: pd.DataFrame, milestones_achieved: list[dict] = None
    ) -> None:
        """Sends an HTML email report with top stats and a direct link to Google Sheets."""
        msg = EmailMessage()
        msg["Subject"] = "📊 Attendance Leaderboard Weekly Summary"
        msg["From"] = self.sender_email
        msg["To"] = self.recipient_email

        sheet_url = f"https://docs.google.com/spreadsheets/d/{Config.SHEET_ID}"
        top_10_html = df_lifetime.head(10).to_html(index=False, border=0)

# Format milestone section
        milestone_html = ""
        if milestones_achieved:
            items = "".join([
                f"<li><strong>{m['customer']}</strong> reached <strong>{m['milestone']} classes</strong>! (Previous: {m['previous']} → Current: {m['current']})</li>"
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
            <h2>TeamUp & StudioBookings Attendance Sync</h2>
            {milestone_html}
            <h3>Top 10 Lifetime Attendance</h3>
            {top_10_html}
            <br>
            <p><a href="{sheet_url}">👉 <strong>Open Master Google Sheet</strong></a></p>
          </body>
        </html>
        """
        msg.add_alternative(html_content, subtype="html")

        with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)

        print("[EmailClient] Email report sent successfully!")