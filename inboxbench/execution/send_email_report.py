import sys
import os
import logging
import resend
from datetime import datetime

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.utils import load_config, setup_logging

def format_email_body(full_report, agency_name):
    """Formats the email body from the report data."""
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2>InboxBench Daily Report for {agency_name}</h2>
        <p>Date: {datetime.now().strftime('%Y-%m-%d')}</p>
        <hr>
    """
    
    for client_report in full_report.get("client_reports", []):
        client_name = client_report.get("client_name")
        summary = client_report.get("summary", {})
        tag = client_report.get("client_tag")
        
        # Determine health status icon
        issues = summary.get('accounts_with_issues', 0)
        status_icon = "✅" if issues == 0 else "⚠️"
        
        html += f"""
        <h3>{client_report.get('client_name')} ({tag})</h3>
        <p><strong>Account Health ({summary.get('total_accounts')} Accounts):</strong></p>
        <ul>
            <li>{status_icon} Accounts with Issues: <strong>{issues}</strong></li>
        </ul>
        <p><strong>Campaign Performance ({summary.get('total_campaigns')} Campaigns):</strong></p>
        """
        
        # Optional: Add table of campaigns if data exists
        if client_report.get("campaigns_data"):
             html += "<ul>"
             for c in client_report["campaigns_data"]:
                 html += f"<li>{c.get('name')}: {c.get('sent')} Sent | {c.get('replies')} Replies</li>"
             html += "</ul>"
        
        html += "<hr>"
        
    html += """
    <p><small>Powered by InboxBench Automation</small></p>
    </body>
    </html>
    """
    return html

def send_email_report(api_key, recipient_email, agency_name, full_report):
    """Sends the email report via Resend."""
    setup_logging()
    
    if not api_key or api_key == "YOUR_RESEND_API_KEY":
        logging.error("Invalid or missing Resend API Key.")
        return False
        
    resend.api_key = api_key

    body = format_email_body(full_report, agency_name)
    subject = f"InboxBench Daily Report for {agency_name} - {datetime.now().strftime('%Y-%m-%d')}"
    
    params = {
        "from": f"{agency_name} Reports <onboarding@resend.dev>", # Defaulting to resend.dev for testing, user should configure domain
        "to": [recipient_email],
        "subject": subject,
        "html": body,
    }

    try:
        logging.info(f"Sending email via Resend to {recipient_email}...")
        email = resend.Emails.send(params)
        logging.info(f"Email sent successfully. ID: {email.get('id')}")
        return True
    except Exception as e:
        logging.error(f"Failed to send email via Resend: {e}")
        return False

if __name__ == "__main__":
    # Test execution
    config = load_config()
    if config:
        # Mock report
        mock_report = {"client_reports": [{"client_name": "Test Client", "client_tag": "Test", "summary": {"total_accounts": 5, "accounts_with_issues": 0, "total_campaigns": 1}}]}
        send_email_report(config.get("resend_api_key"), config.get("reporting_email"), config.get("agency_name"), mock_report)
