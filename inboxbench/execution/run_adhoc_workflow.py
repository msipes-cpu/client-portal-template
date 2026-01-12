import argparse
import json
import logging
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.instantly_api import InstantlyAPI
from execution.update_google_sheet import update_client_sheet

# Setup logging
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='%(levelname)s: %(message)s')

def run_adhoc_report(api_key, sheet_url):
    """
    Runs a report for ALL accounts in the workspace associated with the API key.
    Updates the Google Sheet if provided.
    """
    logging.info("Starting Ad-Hoc Report Workflow...")
    
    api = InstantlyAPI(api_key)
    
    # 1. Fetch ALL Accounts
    # We skip tag filtering to support "whole workspace" view for this ad-hoc tool
    try:
        logging.info("Fetching accounts...")
        accounts_data = api.list_accounts()
        accounts = accounts_data.get("items", []) if isinstance(accounts_data, dict) else accounts_data
        if not accounts: accounts = []
        logging.info(f"Found {len(accounts)} accounts.")
        
        # 2. Fetch ALL Campaigns
        logging.info("Fetching campaigns...")
        campaigns_data = api.list_campaigns()
        campaigns = campaigns_data.get("items", []) if isinstance(campaigns_data, dict) else campaigns_data
        if not campaigns: campaigns = []
        logging.info(f"Found {len(campaigns)} campaigns.")

    except Exception as e:
        return {"success": False, "error": f"API Fetch Failed: {e}"}

    # 3. Analyze Data
    total_sent = 0
    total_replies = 0
    total_leads = 0
    
    processed_campaigns = []
    for camp in campaigns:
        # Get analytics (might be expensive for many campaigns, limits apply)
        # For ad-hoc, maybe we just take summary if available or skip detailed analytics
        # to avoid timeouts. The UI expects a quick response.
        # Let's try fetching summary for top 5 active or just basic info
        
        # Simple parsing
        processed_campaigns.append({
            "name": camp.get("name"),
            "status": camp.get("status_v2", camp.get("status")),
            "sent": 0, # Placeholder to avoid N+1 API calls delay
            "opens": 0,
            "replies": 0,
            "click_rate": 0,
            "reply_rate": 0
        })

    processed_accounts = []
    for acc in accounts:
        processed_accounts.append({
            "email": acc.get("email"),
            "status": acc.get("status_v2", acc.get("status")),
            "daily_limit": acc.get("limit", 0),
            "warmup_score": f"{acc.get('stat_warmup_score', 0)}/100"
        })

    report_data = {
        "client_name": "Ad-Hoc Run",
        "formatted_date": datetime.now().strftime('%Y-%m-%d %H:%M'),
        "total_sent": total_sent,
        "total_leads": total_leads,
        "total_replies": total_replies,
        "total_opportunities": 0,
        "campaigns": processed_campaigns,
        "accounts": processed_accounts
    }
    
    # 4. Update Sheet
    sheet_updated = False
    if sheet_url:
        # Extract ID from URL
        # https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit...
        try:
            if "/d/" in sheet_url:
                sheet_id = sheet_url.split("/d/")[1].split("/")[0]
                logging.info(f"Updating Sheet ID: {sheet_id}")
                sheet_updated = update_client_sheet(report_data, sheet_id)
            else:
                logging.warning("Invalid Sheet URL format.")
        except Exception as e:
            logging.error(f"Sheet Update Error: {e}")

    return {
        "success": True,
        "accounts_count": len(accounts),
        "campaigns_count": len(campaigns),
        "sheet_updated": sheet_updated
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=True)
    parser.add_argument("--sheet", required=False)
    args = parser.parse_args()
    
    result = run_adhoc_report(args.key, args.sheet)
    print(json.dumps(result))
