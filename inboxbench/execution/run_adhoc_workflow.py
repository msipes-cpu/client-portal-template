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
from execution.send_email_report import send_email_report

# Setup logging
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='%(levelname)s: %(message)s')

def run_adhoc_report(api_key, sheet_url, report_email=None):
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
    # Limit to top 15 campaigns to avoid timeout
    for camp in campaigns[:15]:
        camp_id = camp.get("id")
        camp_name = camp.get("name")
        
        # Fetch summary
        success_stats = {"sent": 0, "opens": 0, "replies": 0, "leads": 0}
        try:
            summary = api.get_campaign_summary(camp_id)
            if summary:
                # API v2 might return different structure, handle safely
                success_stats["sent"] = summary.get("contacts_contacted", 0)
                success_stats["leads"] = summary.get("leads_count", 0)
                
                # If analytics endpoint returns arrays/time-series, we might need robust parsing
                # But get_campaign_summary wrapper tries to handle it.
                # Assuming summary has keys: emails_sent, opens, replies? 
                # Actually v2 /campaigns/analytics returns: { start_date, end_date, items: [{...}] }
                # Item keys: emails_sent, opens, replies, opportunities, etc.
                
                success_stats["sent"] = summary.get("emails_sent", 0)
                success_stats["opens"] = summary.get("opens", 0)
                success_stats["replies"] = summary.get("replies", 0)
                success_stats["leads"] = summary.get("opportunities", 0) # Mapping leads to opportunities or leads_count
                
        except Exception as e:
            logging.warning(f"Failed to fetch stats for {camp_name}: {e}")

        total_sent += success_stats["sent"]
        total_replies += success_stats["replies"]
        total_leads += success_stats["leads"]

        processed_campaigns.append({
            "name": camp_name,
            "status": camp.get("status_v2", camp.get("status")),
            "sent": success_stats["sent"],
            "opens": success_stats["opens"],
            "replies": success_stats["replies"],
            "click_rate": 0, # Calculate if needed
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

    # 5. Send Email Report
    email_sent = False
    if report_email:
        resend_key = os.environ.get("RESEND_API_KEY")
        if resend_key:
            # Construct a "Full Report" structure that send_email_report expects
            full_report_struct = {
                "client_reports": [{
                    "client_name": "Ad-Hoc Run",
                    "client_tag": "All",
                    "summary": {
                        "total_accounts": len(accounts),
                        "total_campaigns": len(campaigns),
                        "accounts_with_issues": sum(1 for a in processed_accounts if "Sick" in str(a.get("status", ""))) # Rough heuristic
                    },
                    "campaigns_data": processed_campaigns
                }]
            }
            email_sent = send_email_report(resend_key, report_email, "InboxBench User", full_report_struct)
        else:
             logging.warning("RESEND_API_KEY not found. Skipping email.")

    return {
        "success": True,
        "accounts_count": len(accounts),
        "campaigns_count": len(campaigns),
        "sheet_updated": sheet_updated,
        "email_sent": email_sent
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=True)
    parser.add_argument("--sheet", required=False)
    parser.add_argument("--report_email", required=False)
    args = parser.parse_args()
    
    result = run_adhoc_report(args.key, args.sheet, args.report_email)
    print(json.dumps(result))
