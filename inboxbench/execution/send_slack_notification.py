import sys
import os
import requests
import json
import logging
from datetime import datetime

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.utils import setup_logging

def send_slack_notification(webhook_url, full_report):
    """Sends a summary notification to Slack."""
    setup_logging()
    
    if not webhook_url or webhook_url == "YOUR_SLACK_WEBHOOK_URL":
        logging.error("Invalid or missing Slack Webhook URL.")
        return False

    # Calculate summary stats
    total_clients = len(full_report.get("client_reports", []))
    total_accounts = sum(c["summary"]["total_accounts"] for c in full_report.get("client_reports", []))
    total_issues = sum(c["summary"]["accounts_with_issues"] for c in full_report.get("client_reports", []))
    
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    message = {
        "text": f"InboxBench Daily Summary - {date_str}",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "InboxBench Daily Summary"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":white_check_mark: Report for {date_str} is complete.\n"
                            f":office: Monitored {total_clients} clients and {total_accounts} accounts.\n"
                            f":warning: Found {total_issues} critical issues."
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "<https://docs.google.com/spreadsheets|View Detailed Report>" 
                    # Note: We should ideally link to the actual sheet if we have the ID.
                }
            }
        ]
    }

    try:
        response = requests.post(webhook_url, json=message)
        response.raise_for_status()
        logging.info("Slack notification sent successfully.")
        return True
    except Exception as e:
        logging.error(f"Failed to send Slack notification: {e}")
        return False
