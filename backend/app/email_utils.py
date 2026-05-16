import os
import smtplib
from email.message import EmailMessage


def send_lead_notification(lead_id: int, lead) -> bool:
    """
    Sends an email notification when a new quote request is submitted.

    Returns True if the email was sent.
    Returns False if email settings are missing or sending fails.
    """

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    notify_to_email = os.getenv("NOTIFY_TO_EMAIL")
    from_email = os.getenv("FROM_EMAIL", smtp_username)
    admin_leads_url = os.getenv("ADMIN_LEADS_URL", "Not configured")

    if not all([smtp_host, smtp_username, smtp_password, notify_to_email, from_email]):
        print("Email notification skipped: missing SMTP settings.")
        return False

    subject = f"New AJ Empirestone Quote Request #{lead_id}"

    body = f"""
New AJ Empirestone Quote Request

Lead ID: {lead_id}

Customer Information
Name: {lead.full_name}
Phone: {lead.phone}
Email: {lead.email or "Not provided"}
Project City: {lead.project_city or "Not provided"}
Project Type: {lead.project_type or "Not provided"}

Project Details
{lead.message or "No additional details provided."}

Admin View:
{admin_leads_url}
"""

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_email
    message["To"] = notify_to_email
    message.set_content(body)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)

        print(f"Email notification sent for lead #{lead_id}.")
        return True

    except Exception as error:
        print("Email notification failed:", error)
        return False