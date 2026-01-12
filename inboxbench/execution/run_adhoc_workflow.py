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

def run_adhoc_report(api_key, sheet_url, report_email=None, warmup_threshold=70):
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

        # Campaign Status Mapping
        raw_status = camp.get("status_v2", camp.get("status"))
        # 1=Active, 2=Paused, 3=Completed, 0=Inactive/Draft
        c_status_map = {1: "Active", 2: "Paused", 3: "Completed", 0: "Inactive"}
        final_status = c_status_map.get(raw_status, str(raw_status))

        processed_campaigns.append({
            "name": camp_name,
            "status": final_status,
            "sent": success_stats["sent"],
            "opens": success_stats["opens"],
            "replies": success_stats["replies"],
            "click_rate": 0, 
            "reply_rate": 0
        })

    # Fetch Tags Map
    try:
        tag_map = api.get_all_tags_map()
    except:
        tag_map = {}

    # Initialize Decision Engine
    from execution.decision_engine import DecisionEngine
    engine_config = {"warmup_threshold": warmup_threshold}
    engine = DecisionEngine(api, config=engine_config)

    processed_accounts = []
    actions_log = [] # For the "Action Log" tab

    emit_status("running_engine", f"Running Decision Engine on {len(accounts)} accounts...", 40)
    
    # Pre-resolve tags for engine
    for acc in accounts:
        t_ids = acc.get("tags", [])
        acc["tags_resolved"] = [tag_map.get(tid, str(tid)) for tid in t_ids]

    # Status Mapping
    STATUS_MAP = {
        1: "Active",
        2: "Paused",
        3: "Completed",
        0: "Inactive"
    }

    count = 0
    total_accounts = len(accounts)
    
    for acc in accounts:
        count += 1
        # Deep fetch (Analytics) - Placeholder for now
        analytics = api.get_account_analytics(acc.get("email"))
        
        # Evaluate Rules
        action = engine.evaluate_account(acc, analytics)
        
        # Default status/tags from current state
        final_tags = acc.get("tags_resolved", [])
        
        raw_status = acc.get("status_v2", acc.get("status"))
        final_status = STATUS_MAP.get(raw_status, str(raw_status))

        if action:
            # Prepare log entry
            email = action['email']
            reason = action['reason']
            new_tag = action['new_tag']
            
            logging.info(f"ACTION REQUIRED: {email} -> {new_tag} ({reason})")
            
            # Execute Action (Update Instantly)
            # 1. Update Tag
            tag_id = api.get_tag_id_by_name(new_tag)
            if tag_id:
                # Add new tag. (Ideally remove old status tag too, but safe add for now)
                api.add_account_tag(email, tag_id, acc.get("tags", [])) 
                # Update our local record for the report
                if new_tag not in final_tags:
                    final_tags.append(new_tag)
            
            # 2. Update Status/Warmup (if needed)
            if action.get("warmup") is False:
                # api.set_warmup_status(email, False)
                pass

            actions_log.append([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "Unknown Client", 
                email,
                final_status, # "Previous Status" roughly
                new_tag,
                reason,
                "-",
                "-"
            ])
            
            # Determine Change Display for Tab
            # Try to find previous status tag
            prev_tag = "-"
            for t in acc.get("tags_resolved", []):
                if t.startswith("status-") and t != new_tag:
                    prev_tag = t
                    break
            
            # If no previous stat tag found, maybe use mapped status?
            # Or just show "-> NewTag"
            if prev_tag == "-":
                change_display = f"-> {new_tag}"
            else:
                 # Format: status-active -> status-sick => Active -> Sick
                p_clean = prev_tag.replace("status-", "").capitalize()
                n_clean = new_tag.replace("status-", "").capitalize()
                change_display = f"{p_clean} -> {n_clean}"
        else:
            change_display = "-"
        
        # 3. Format Strings for Sheet
        tags_str = ", ".join(final_tags)

        processed_accounts.append({
            "email": acc.get("email"),
            "status": final_status,
            "daily_limit": acc.get("limit", 0),
            "warmup_score": f"{acc.get('stat_warmup_score', 0)}/100",
            "tags": tags_str,
            "change": change_display
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
    
    # 4. Generate Transition Summary (for Sheet & Email)
    summary_counts = {
        "Sick": 0, "Benched": 0, "Active": 0, "Warming": 0
    }
    transition_list = []
    
    for log in actions_log:
        # log format: [time, client, email, prev, new, reason, ...]
        new_status = log[4]
        if new_status.startswith("status-"):
            key = new_status.replace("status-", "").capitalize()
            summary_counts[key] = summary_counts.get(key, 0) + 1
        transition_list.append(f"{log[2]} -> {log[4]} ({log[5]})")

    # Add Summary to Report Data
    report_data["run_summary"] = {
        "total_actions": len(actions_log),
        "transitions": transition_list,
        "counts": summary_counts
    }

    # 5. Update Sheet
    sheet_updated = False
    sheet_error = None
    if sheet_url:
        emit_status("updating_sheet", "Writing data to Google Sheet...", 80)
        try:
            if "/d/" in sheet_url:
                sheet_id = sheet_url.split("/d/")[1].split("/")[0]
                logging.info(f"Updating Sheet ID: {sheet_id}")
                
                from execution.update_google_sheet import write_to_tab, get_credentials
                from googleapiclient.discovery import build
                
                # Update Snapshot (Main Report) + Summary Table? 
                # Ideally we append a summary table to the snapshot. 
                # For now let's keep Snapshot clean and just ensure Action Log is populated.
                sheet_updated, sheet_error = update_client_sheet(report_data, sheet_id)
                
                # Update Action Log (Append)
                if actions_log:
                    logging.info(f"Appending {len(actions_log)} actions to log...")
                    # Re-instantiate service 
                    creds = get_credentials()
                    if creds:
                        service = build('sheets', 'v4', credentials=creds)
                        write_to_tab(service, sheet_id, "Action Log", actions_log, mode="APPEND")
                
                if not sheet_updated:
                    if not sheet_error: sheet_error = "Unknown writing error"
                    emit_status("warning", f"Sheet Update Failed: {sheet_error}", 85)
            else:
                logging.warning("Invalid Sheet URL format.")
                sheet_error = "Invalid Sheet URL format"
                emit_status("warning", "Skipped Sheet Update: Invalid URL format", 85)
        except Exception as e:
            logging.error(f"Sheet Update Error: {e}")
            sheet_error = str(e)
    else:
        logging.warning("No Sheet URL provided.")
        emit_status("warning", "Skipped Sheet Update: No URL provided in settings", 85)
    
    # 6. Send Email Report
    email_sent = False
    email_error = None
    if report_email:
        emit_status("sending_email", f"Sending report to {report_email}...", 90)
        resend_key = os.environ.get("RESEND_API_KEY")
        if resend_key:
            # Build text summary of transitions
            trans_summary_text = "\n".join(transition_list[:10]) # Limit to 10
            if len(transition_list) > 10:
                trans_summary_text += f"\n...and {len(transition_list)-10} more."

            full_report_struct = {
                "client_reports": [{
                    "client_name": "Ad-Hoc Run",
                    "client_tag": "All",
                    "summary": {
                        "total_accounts": len(accounts),
                        "total_campaigns": len(campaigns),
                        "accounts_with_issues": sum(1 for a in processed_accounts if "Sick" in str(a.get("status", ""))),
                        "run_summary_text": trans_summary_text # Pass this to email template if supported
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
        "email_sent": email_sent,
        "run_summary": report_data["run_summary"] 
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=True)
    parser.add_argument("--sheet", required=False)
    parser.add_argument("--report_email", required=False)
    parser.add_argument("--warmup_threshold", type=int, default=70, help="Min Warmup Score (Default 70)")
    args = parser.parse_args()
    
    try:
        result = run_adhoc_report(args.key, args.sheet, args.report_email, args.warmup_threshold)
        # Final output for the API to capture as the "Result"
        print(json.dumps({"type": "result", "data": result}), flush=True)
    except Exception as e:
        # Catch-all for top-level script errors
        error_json = {"type": "error", "message": f"Critical Script Crash: {str(e)}"}
        print(json.dumps(error_json), flush=True)
        sys.exit(1)
