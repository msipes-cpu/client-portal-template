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

# Setup logging to STDERR so it doesn't interfere with STDOUT JSON stream
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='%(levelname)s: %(message)s')

def emit_status(step, message, percent):
    """Emits a JSON status update to stdout"""
    data = {
        "type": "progress",
        "step": step,
        "message": message,
        "percent": percent
    }
    print(json.dumps(data), flush=True)

def run_adhoc_report(api_key, sheet_url, report_email=None):
    """
    Runs a report for ALL accounts in the workspace.
    Streams progress updates to stdout.
    """
    emit_status("init", "Starting Ad-Hoc Report Workflow...", 5)
    
    try:
        api = InstantlyAPI(api_key)
        
        # 1. Fetch ALL Accounts
        emit_status("fetch_accounts", "Fetching accounts from Instantly...", 10)
        accounts_data = api.list_accounts()
        accounts = accounts_data.get("items", []) if isinstance(accounts_data, dict) else accounts_data
        if not accounts: accounts = []
        logging.info(f"Found {len(accounts)} accounts.")
        
        # 2. Fetch ALL Campaigns
        emit_status("fetch_campaigns", f"Fetching campaigns (Found {len(accounts)} accounts)...", 20)
        campaigns_data = api.list_campaigns()
        campaigns = campaigns_data.get("items", []) if isinstance(campaigns_data, dict) else campaigns_data
        if not campaigns: campaigns = []
        logging.info(f"Found {len(campaigns)} campaigns.")

    except Exception as e:
        err_msg = f"API Fetch Failed: {e}"
        logging.error(err_msg)
        return {"success": False, "error": err_msg}

    # 3. Analyze Data
    emit_status("analyzing", f"Analyzing {len(campaigns)} campaigns...", 30)
    total_sent = 0
    total_replies = 0
    total_leads = 0
    
    processed_campaigns = []
    # Limit to top 15 campaigns to avoid timeout
    
    count = 0
    max_camps = 15
    camps_to_process = campaigns[:max_camps]
    total_camps_count = len(camps_to_process)

    for camp in camps_to_process:
        count += 1
        # Update progress within the analysis phase (30% to 70%)
        progress_val = 30 + int((count / total_camps_count) * 40)
        emit_status("analyzing_campaign", f"Analyzing campaign: {camp.get('name')}...", progress_val)
        
        camp_id = camp.get("id")
        camp_name = camp.get("name")
        
        # Fetch summary
        success_stats = {"sent": 0, "opens": 0, "replies": 0, "leads": 0}
        try:
            summary = api.get_campaign_summary(camp_id)
            if summary:
                success_stats["sent"] = summary.get("contacts_contacted", summary.get("emails_sent", 0))
                success_stats["opens"] = summary.get("opens", 0)
                success_stats["replies"] = summary.get("replies", 0)
                success_stats["leads"] = summary.get("leads_count", summary.get("opportunities", 0))
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
    sheet_error = None
    if sheet_url:
        emit_status("updating_sheet", "Writing data to Google Sheet...", 80)
        try:
            if "/d/" in sheet_url:
                sheet_id = sheet_url.split("/d/")[1].split("/")[0]
                logging.info(f"Updating Sheet ID: {sheet_id}")
                sheet_updated, sheet_error = update_client_sheet(report_data, sheet_id)
                if not sheet_updated:
                    # If explicitly returned false, ensure we pass the error
                    if not sheet_error: sheet_error = "Unknown writing error"
                    emit_status("warning", f"Sheet Update Failed: {sheet_error}", 85)
            else:
                logging.warning("Invalid Sheet URL format.")
                sheet_error = "Invalid Sheet URL format"
                emit_status("warning", "Skipped Sheet Update: Invalid URL format", 85)
        except Exception as e:
            logging.error(f"Sheet Update Error: {e}")
            sheet_error = str(e)
    
    # 5. Send Email Report
    email_sent = False
    email_error = None
    if report_email:
        emit_status("sending_email", f"Sending report to {report_email}...", 90)
        resend_key = os.environ.get("RESEND_API_KEY")
        if resend_key:
            full_report_struct = {
                "client_reports": [{
                    "client_name": "Ad-Hoc Run",
                    "client_tag": "All",
                    "summary": {
                        "total_accounts": len(accounts),
                        "total_campaigns": len(campaigns),
                        "accounts_with_issues": sum(1 for a in processed_accounts if "Sick" in str(a.get("status", ""))) 
                    },
                    "campaigns_data": processed_campaigns
                }]
            }
            try:
                email_sent, email_error = send_email_report(resend_key, report_email, "InboxBench User", full_report_struct)
            except Exception as e:
                logging.error(f"Email Report Logic Error: {e}")
                email_error = str(e)
        else:
             logging.warning("RESEND_API_KEY not found. Skipping email.")
             email_error = "RESEND_API_KEY not found"

    emit_status("complete", "Workflow Complete!", 100)
    
    return {
        "success": True,
        "accounts_count": len(accounts),
        "campaigns_count": len(campaigns),
        "sheet_updated": sheet_updated,
        "sheet_error": sheet_error,
        "email_sent": email_sent
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=True)
    parser.add_argument("--sheet", required=False)
    parser.add_argument("--report_email", required=False)
    args = parser.parse_args()
    
    try:
        result = run_adhoc_report(args.key, args.sheet, args.report_email)
        # Final output for the API to capture as the "Result"
        print(json.dumps({"type": "result", "data": result}), flush=True)
    except Exception as e:
        # Catch-all for top-level script errors
        error_json = {"type": "error", "message": f"Critical Script Crash: {str(e)}"}
        print(json.dumps(error_json), flush=True)
        sys.exit(1)
