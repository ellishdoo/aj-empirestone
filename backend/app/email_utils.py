import os
import resend


def send_lead_notification(lead_id: int, lead) -> bool:
    """
    Sends an email notification when a new quote request is submitted.

    Returns True if the email was sent.
    Returns False if email settings are missing or sending fails.
    """

    resend_api_key = os.getenv("RESEND_API_KEY")
    notify_to_email = os.getenv("NOTIFY_TO_EMAIL")
    from_email = os.getenv("RESEND_FROM_EMAIL", "AJ Empirestone <onboarding@resend.dev>")
    admin_leads_url = os.getenv("ADMIN_LEADS_URL", "Not configured")

    if not all([resend_api_key, notify_to_email, from_email]):
        print("Email notification skipped: missing Resend settings.")
        return False

    resend.api_key = resend_api_key

    subject = f"New AJ Empirestone Quote Request #{lead_id}"

    text_body = f"""
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

    html_body = f"""
    <h2>New AJ Empirestone Quote Request</h2>

    <p><strong>Lead ID:</strong> {lead_id}</p>

    <h3>Customer Information</h3>
    <p>
      <strong>Name:</strong> {lead.full_name}<br>
      <strong>Phone:</strong> {lead.phone}<br>
      <strong>Email:</strong> {lead.email or "Not provided"}<br>
      <strong>Project City:</strong> {lead.project_city or "Not provided"}<br>
      <strong>Project Type:</strong> {lead.project_type or "Not provided"}
    </p>

    <h3>Project Details</h3>
    <p>{lead.message or "No additional details provided."}</p>

    <p>
      <strong>Admin View:</strong><br>
      {admin_leads_url}
    </p>
    """

    try:
        resend.Emails.send({
            "from": from_email,
            "to": [notify_to_email],
            "subject": subject,
            "html": html_body,
            "text": text_body,
        })

        print(f"Email notification sent for lead #{lead_id}.")
        return True

    except Exception as error:
        print("Email notification failed:", error)
        return False