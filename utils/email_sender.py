# utils/email_sender.py
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def send_email_report(report_body: str):
    sender_email = os.getenv("GMAIL_USER")
    sender_password = os.getenv("GMAIL_APP_PASSWORD")
    recipient_email = sender_email  # send to self

    if not sender_email or not sender_password:
        raise ValueError("GMAIL_USER and GMAIL_APP_PASSWORD must be set in .env")

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = "🛍️ EcomAI Analyst: Chat Summary Report"

    msg.attach(MIMEText(report_body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)