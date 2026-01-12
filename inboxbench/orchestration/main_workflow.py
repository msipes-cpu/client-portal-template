import sys
import os
import json
import logging
from datetime import datetime

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from execution.generate_client_report import generate_client_report
from execution.send_email_report import send_email_report
from execution.update_google_sheet import update_client_sheet
from execution.send_slack_notification import send_slack_notification

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), '../config/config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

def run_workflow():
    logging.info("Starting InboxBench Daily Workflow...")
    
    try:
        config = load_config()
        
        # 1. Setup
        client_profiles = config.get('client_profiles', [])
        instantly_api_key = config.get('instantly_api_key')
        
        if not client_profiles:
            logging.error("No client profiles found in config. Aborting.")
            return

        all_reports = []
        
        # 2. Iterate each client
        for profile in client_profiles:
            tag_name = profile.get('tag_name')
            client_name = profile.get('client_name')
            google_sheet_id = profile.get('google_sheet_id')
            
            logging.info(f"Processing client: {client_name} (Tag: {tag_name})")
            
            # 3. Generate individual report
            client_report = generate_client_report(instantly_api_key, tag_name, client_name)
            
            # 4. Update Client's Google Sheet
            if google_sheet_id:
                logging.info(f"Updating Google Sheet for {client_name}...")
                success = update_client_sheet(client_report, google_sheet_id)
                if success:
                    logging.info("Sheet update successful.")
                else:
                    logging.error("Sheet update failed.")
            else:
                logging.warning(f"No Google Sheet ID for {client_name}, skipping sheet update.")

            all_reports.append(client_report)

        # 5. Send Consolidated Email Summary
        if all_reports:
            logging.info("Sending consolidated email report via Resend...")
            resend_api_key = config.get('resend_api_key')
            recipient = config.get('reporting_email')
            agency_name = config.get('agency_name', 'My Agency')
            
            # Wrap in expected structure
            full_report = {"client_reports": all_reports}
            
            if resend_api_key and recipient:
                send_email_report(resend_api_key, recipient, agency_name, full_report)
            else:
                 logging.error("Resend API Key or Recipient missing. Cannot send email.")

        logging.info("Workflow completed successfully.")
        
    except Exception as e:
        logging.error(f"Workflow failed: {e}")
        # Optional: Send failure notification via Slack

if __name__ == "__main__":
    run_workflow()
