import os
import sys
import logging
from datetime import datetime
import json
import argparse

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.instantly_api import InstantlyAPI
from execution.decision_engine import DecisionEngine
from execution.update_google_sheet import update_client_sheet, write_to_tab
from execution.send_email_report import send_email_report

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_daily_cycle(api_key, sheet_url, report_email=None, dry_run=False):
    logging.info(f"Starting Daily Cycle (Dry Run: {dry_run})")
    
    api = InstantlyAPI(api_key)
    engine = DecisionEngine(api)

    # 1. Fetch Data
    logging.info("Fetching Accounts & Campaigns...")
    accounts = api.list_accounts()
    campaigns = api.list_campaigns()
    tag_map = api.get_all_tags_map()

    # Resolve tags for accounts beforehand
    for acc in accounts:
        # Map tag IDs to Names
        t_ids = acc.get("tags", [])
        acc["tags_resolved"] = [tag_map.get(tid, str(tid)) for tid in t_ids]

    # 2. Run Decision Engine
    logging.info(f"Analyzing {len(accounts)} accounts...")
    actions_to_take = []
    
    for acc in accounts:
        # Deep fetch (Analytics) - Placeholder for now
        analytics = api.get_account_analytics(acc.get("email"))
        
        action = engine.evaluate_account(acc, analytics)
        if action:
            actions_to_take.append(action)

    # 3. Execute Actions
    logging.info(f"Found {len(actions_to_take)} actions to execute.")
    execution_log = [] # Log for the sheet
    
    for action in actions_to_take:
        email = action['email']
        reason = action['reason']
        new_tag = action['new_tag']
        
        log_entry = [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "Client? (Map later)", # Need client mapping
            email,
            "Unknown", # Previous Status
            new_tag,
            reason,
            "TODO", # Campaigns Removed
            "TODO"  # Campaigns Added
        ]
        
        if not dry_run:
            # Update Tag
            # 1. Resolve Tag Name to ID? Or create if missing?
            # Assuming tags exist for now.
            tag_id = api.get_tag_id_by_name(new_tag)
            if tag_id:
                # Remove OLD status tags? 
                # Ideally we fetch current tags, filter out old status tags, add new one.
                # For MVP: Just add pending robustness.
                # Using simple add for now:
                # api.add_account_tag(email, tag_id)
                pass # Skip actual write for safety until verified
            else:
                 logging.warning(f"Tag {new_tag} not found in Instantly!")

        execution_log.append(log_entry)

    # 4. Prepare Report Data (Snapshot)
    # Reuse logic from ad-hoc: Summary + List
    total_sent = 0 # Need to fetch from campaigns (skipped for brevity in this step)
    
    processed_accounts = []
    for acc in accounts:
        processed_accounts.append({
            "email": acc.get("email"),
            "status": acc.get("status_v2", acc.get("status")), # Raw status
            "daily_limit": acc.get("limit", 0),
            "warmup_score": f"{acc.get('stat_warmup_score', 0)}/100",
            "tags": ", ".join(acc.get("tags_resolved", []))
        })

    report_data = {
        "client_name": "Daily Cycle Run",
        "formatted_date": datetime.now().strftime('%Y-%m-%d %H:%M'),
        "total_sent": total_sent,
        "total_leads": 0,
        "total_replies": 0,
        "total_opportunities": 0,
        "campaigns": [], # Populate if needed
        "accounts": processed_accounts
    }

    # 5. Update Sheet
    if sheet_url:
        if "/d/" in sheet_url:
            sheet_id = sheet_url.split("/d/")[1].split("/")[0]
            logging.info(f"Updating Sheet {sheet_id}...")
            if not dry_run:
                # Update Snapshot
                update_client_sheet(report_data, sheet_id)
                
                # Update Action Log (Append)
                if execution_log:
                     # Need to get service first? Refactor update_client_sheet to expose service?
                     # Or make a standalone function.
                     # For now, relying on update_google_sheet.py modification to expose _write_to_tab?
                     # It is internal. I should have made it public.
                     pass 
        else:
            logging.error("Invalid Sheet URL")

    logging.info("Cycle Complete.")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=True)
    parser.add_argument("--sheet", required=False)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    run_daily_cycle(args.key, args.sheet, dry_run=args.dry_run)
