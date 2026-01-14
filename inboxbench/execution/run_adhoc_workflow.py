import argparse
import json
import logging
import sys
import os
from datetime import datetime
from zoneinfo import ZoneInfo

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

def run_adhoc_report(api_key, sheet_url, report_email=None, warmup_threshold=70, bench_percent=0, ignore_customer_tags=True):
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
    
    # --- HYDRATE TAGS & MAPS ---
    logging.info(f"Hydrating account tags... (Ignore Customer Tags: {ignore_customer_tags})")
    
    # Helper to identify Customer Tag (Non-Status)
    def get_customer_tag(tags_list):
        """Returns the first tag that is NOT a system status tag."""
        valid_status = {"Sending", "Sick", "Warming", "Benched", "Active", "Dead", "Completed", "Paused", "Inactive"}
        for t in tags_list:
            if t not in valid_status and not t.startswith("status-"):
                return t
        return "-"

    # Fetch Tag Map EARLY so campaigns can use it
    try:
        all_tag_map = api.get_all_tags_map()
    except Exception as e:
        logging.warning(f"Failed to fetch tag map: {e}")
        all_tag_map = {}

    # --- FETCH HIDDEN TAG MAPPINGS (V2 Fix) ---
    logging.info("Fetching hidden tag mappings for resources...")
    try:
        # Collect IDs/Emails
        r_ids = []
        # Campaign IDs
        c_map = {c.get("id"): c for c in campaigns if c.get("id")}
        r_ids.extend(list(c_map.keys()))
        
        # Account Emails (as IDs)
        a_map = {a.get("email"): a for a in accounts if a.get("email")}
        r_ids.extend(list(a_map.keys()))
        
        mappings = api.get_custom_tag_mappings(r_ids)
        logging.info(f"Found {len(mappings)} hidden tag associations.")
        
        for m in mappings:
            rid = m.get("resource_id")
            tid = m.get("tag_id")
            if not tid: continue
            
            # Check Campaign Match
            if rid in c_map:
                tgt = c_map[rid]
                if "tags" not in tgt: tgt["tags"] = []
                if tid not in tgt["tags"]: tgt["tags"].append(tid)
                
            # Check Account Match
            elif rid in a_map:
                tgt = a_map[rid]
                if "tags" not in tgt: tgt["tags"] = []
                # Ensure we don't duplicate if already present
                if tid not in tgt["tags"]: tgt["tags"].append(tid)
                
    except Exception as e:
        logging.warning(f"Failed to fetch hidden mappings: {e}")

    relevant_status_tags = ["Sending", "Sick", "Warming", "Benched", "Active", "Dead"]
    email_to_acc_map = {acc['email']: acc for acc in accounts}
    
    # Hydrate Account Tags (Resolve IDs to Names)
    # Also manual hydration for status tags if API didn't return them in list_accounts
    for t_name in relevant_status_tags:
        t_id = api.get_tag_id_by_name(t_name)
        if t_id:
            # unique list of accounts with this tag
            tagged_accs_data = api.list_accounts(tag_ids=[t_id])
            if isinstance(tagged_accs_data, list):
                 for t_acc in tagged_accs_data:
                     email = t_acc.get('email')
                     if email in email_to_acc_map:
                         if 'tags' not in email_to_acc_map[email]:
                             email_to_acc_map[email]['tags'] = []
                         # Avoid dupes
                         if t_id not in email_to_acc_map[email]['tags']:
                             email_to_acc_map[email]['tags'].append(t_id)

    # Pre-resolve tags for ALL accounts now, so we can use them
    # DEBUG: Print Tag Map sample
    logging.info(f"Tag Map Keys: {list(all_tag_map.keys())[:5]}")
    logging.info(f"Tag Map Values: {list(all_tag_map.values())[:5]}")
    
    for acc in accounts:
        t_ids = acc.get("tags", [])
        acc["tags_resolved"] = [all_tag_map.get(tid, str(tid)) for tid in t_ids]
        acc["customer_tag"] = get_customer_tag(acc["tags_resolved"])
        
        # DEBUG specific account
        if "powersipesautomation" in acc.get("email", ""):
            logging.info(f"debug_acc: {acc.get('email')} | tags: {t_ids} | resolved: {acc['tags_resolved']} | customer: {acc['customer_tag']}")


    total_sent = 0
    total_replies = 0
    total_leads = 0
    
    processed_campaigns = []
    
    count = 0
    max_camps = 15
    camps_to_process = campaigns[:max_camps]
    total_camps_count = len(camps_to_process)

    for camp in camps_to_process:
        count += 1
        progress_val = 30 + int((count / total_camps_count) * 40)
        emit_status("analyzing_campaign", f"Analyzing campaign: {camp.get('name')}...", progress_val)
        
        camp_id = camp.get("id")
        camp_name = camp.get("name")
        
        # Resolve Campaign Tags
        c_t_ids = camp.get("tags", [])
        c_tags_resolved = [all_tag_map.get(tid, str(tid)) for tid in c_t_ids]
        camp_customer_tag = get_customer_tag(c_tags_resolved)

        # Fetch summary
        success_stats = {"sent": 0, "opens": 0, "replies": 0, "leads": 0}
        try:
            summary = api.get_campaign_summary(camp_id)
            if summary:
                # Robust extraction: check keys found in debug (`emails_sent_count`, etc.)
                # User preference: "Sent" column should show "Sequence Started" (unique leads contacted)
                success_stats["sent"] = summary.get("new_leads_contacted_count", summary.get("contacted_count", 0))
                
                # User preference: "Replies" matching UI (20) which is manual (4) + auto (16)
                manual_replies = summary.get("reply_count", summary.get("replies", 0))
                auto_replies = summary.get("reply_count_automatic", 0)
                success_stats["replies"] = manual_replies + auto_replies
                
                success_stats["opens"] = summary.get("open_count", summary.get("opens", 0))
                success_stats["leads"] = summary.get("leads_count", summary.get("opportunities", 0))
                
                # Check for zero stats warning
                if success_stats["sent"] == 0:
                     logging.info(f"Campaign {camp_name} returned 0 contacted. Keys: {list(summary.keys())}")

        except Exception as e:
            logging.warning(f"Failed to fetch stats for {camp_name}: {e}")

        total_sent += success_stats["sent"]
        total_replies += success_stats["replies"]
        total_leads += success_stats["leads"]

        # Campaign Status Mapping
        raw_status = camp.get("status_v2", camp.get("status"))
        c_status_map = {1: "Active", 2: "Paused", 3: "Completed", 0: "Inactive"}
        final_status = c_status_map.get(raw_status, str(raw_status))

        processed_campaigns.append({
            "name": camp_name,
            "status": final_status,
            "customer_tag": camp_customer_tag,
            "sent": success_stats["sent"],
            "opens": success_stats["opens"],
            "replies": success_stats["replies"],
            "click_rate": 0, 
            "reply_rate": 0
        })

    # Initialize Decision Engine
    from execution.decision_engine import DecisionEngine
    engine_config = {
        "warmup_threshold": warmup_threshold,
        "bench_percent": bench_percent
    }
    engine = DecisionEngine(api, config=engine_config) # Tag map is passed or fetched internally? Engine might need update

    processed_accounts = []
    actions_log = [] 

    emit_status("running_engine", f"Running Decision Engine on {len(accounts)} accounts...", 40)
    
    # Status Mapping
    STATUS_MAP = {
        1: "Active",
        2: "Paused",
        3: "Completed",
        0: "Inactive"
    }

    # Pre-calculate Rotation Plan
    bench_percent = engine_config.get("bench_percent", 0)
    force_map = {}
    
    if bench_percent > 0:
        # Determine Buckets
        if ignore_customer_tags:
            buckets = {"Global": {"accounts": accounts, "campaigns": campaigns}}
        else:
            # Group Accounts using pre-calculated customer_tag
            buckets = {}
            for acc in accounts:
                b_key = acc.get("customer_tag", "General")
                if b_key not in buckets: buckets[b_key] = {"accounts": [], "campaigns": []}
                buckets[b_key]["accounts"].append(acc)
            
            # Map Campaigns to Buckets
            # We already calculated tags for processed_campaigns, but "campaigns" list might be raw
            # Need to ensure global campaigns list has 'customer_tag' or resolve it again
            for camp in campaigns:
                # Quick resolve for rotation logic if not processed above
                if "tags_resolved" not in camp:
                     c_t_ids = camp.get("tags", [])
                     camp["tags_resolved"] = [all_tag_map.get(tid, str(tid)) for tid in c_t_ids]
                
                b_key = get_customer_tag(camp["tags_resolved"])
                if b_key not in buckets: buckets[b_key] = {"accounts": [], "campaigns": []}
                buckets[b_key]["campaigns"].append(camp)

        logging.info(f"Running Rotation Logic on {len(buckets)} buckets (Ignore Tags: {ignore_customer_tags})")

        for b_name, b_data in buckets.items():
            b_accs = b_data["accounts"]
            b_camps = b_data["campaigns"]
            
            active_candidates = []
            benched_candidates = []
            
            for acc in b_accs:
                tags = acc.get("tags_resolved", [])
                if "Sending" in tags:
                    active_candidates.append(acc)
                elif "Benched" in tags:
                    benched_candidates.append(acc)
            
            total_pool = len(active_candidates) + len(benched_candidates)
            if total_pool > 0:
                has_campaigns = len(b_camps) > 0
                if ignore_customer_tags: has_campaigns = True 
                
                if not has_campaigns and b_name != "General":
                    target_bench_count = total_pool
                    logging.info(f"Bucket '{b_name}': No campaigns found. Forcing 100% Bench.")
                else:
                    target_bench_count = int(total_pool * bench_percent / 100)
                
                current_bench_count = len(benched_candidates)
                
                logging.info(f"Rotation ({b_name}): Total={total_pool}, Target Bench={target_bench_count}, Current={current_bench_count}")
                
                if current_bench_count < target_bench_count:
                    # Deficit: Bench some Actives
                    needed = target_bench_count - current_bench_count
                    active_candidates.sort(key=lambda x: int(x.get('stat_warmup_score', 100) or 0))
                    to_bench = active_candidates[:needed]
                    for a in to_bench: force_map[a['email']] = "Benched"
                    logging.info(f"Rotation ({b_name}): Forcing BENCH for {len(to_bench)} accounts.")
    
                elif current_bench_count > target_bench_count:
                    # Surplus: Activate some Benched
                    release = current_bench_count - target_bench_count
                    benched_candidates.sort(key=lambda x: int(x.get('stat_warmup_score', 0) or 0), reverse=True)
                    to_activate = benched_candidates[:release]
                    for a in to_activate: force_map[a['email']] = "Sending"
                    logging.info(f"Rotation ({b_name}): Forcing SENDING for {len(to_activate)} accounts.")

    count = 0
    total_accounts = len(accounts)
    
    # Conflict List
    CONFLICT_TAGS = {"Active", "Dead", "Sending", "Sick", "Warming", "Benched"}

    for acc in accounts:
        count += 1
        # Deep fetch (Analytics) - Placeholder for now
        analytics = api.get_account_analytics(acc.get("email"))
        
        # Evaluate Rules
        force_status = force_map.get(acc.get("email"))
        action = engine.evaluate_account(acc, analytics, force_status=force_status)
        
        # Default status/tags from current state
        final_tags = list(acc.get("tags_resolved", [])) # Make a mutable copy
        
        raw_status = acc.get("status_v2", acc.get("status"))
        final_status = STATUS_MAP.get(raw_status, str(raw_status))

        # DEBUG: Emit status for target account to see engine internals
        email = acc.get("email")
        if "michael" in email.lower() and "shift" in email.lower():
             # Re-evaluate to dump state
             d_tags = acc.get("tags_resolved", [])
             d_score = acc.get("stat_warmup_score", 0)
             d_found = [t for t in d_tags if t in ["Sick", "Benched", "Sending", "Warming"]]
             emit_status("warning", f"DEBUG: {email} | Tags={d_tags} | Found={d_found} | Score={d_score} | Threshold={warmup_threshold} | Action={action}", 55)

        if action:
            # Prepare log entry
            email = action['email']
            reason = action['reason']
            new_tag = action['new_tag']
            
            logging.info(f"ACTION REQUIRED: {email} -> {new_tag} ({reason})")
            
            # Execute Action (Update Instantly)
            # SAFE METHOD: Use add/remove instead of set_tags to preserve hidden tags
            
            acc_id = acc.get("id") # Need ID for toggle-resource
            # If no ID (rare), we might have to skip or try lookup? List accounts returns IDs.
            if not acc_id:
                logging.warning(f"Account {email} has no ID inside logic. Skipping tag updates.")
            else:
                # 1. Remove Conflicts
                for c_tag_name in CONFLICT_TAGS:
                    if c_tag_name != new_tag and c_tag_name in final_tags:
                        t_id_to_remove = api.get_tag_id_by_name(c_tag_name)
                        if t_id_to_remove:
                            logging.info(f"Removing conflict tag '{c_tag_name}' for {email}")
                            api.remove_account_tag(acc_id, t_id_to_remove)
                            if c_tag_name in final_tags: final_tags.remove(c_tag_name)
                
                # 2. Add New Tag
                if new_tag not in final_tags:
                    t_id_to_add = api.get_tag_id_by_name(new_tag)
                    if t_id_to_add:
                        logging.info(f"Adding tag '{new_tag}' for {email}")
                        api.add_account_tag(acc_id, t_id_to_add)
                        final_tags.append(new_tag)
                    else:
                        logging.warning(f"Could not resolve ID for new tag '{new_tag}'")

            # Update local state for report (visuals only)
            
            # 2. Update Status/Warmup (if needed)
            if action.get("warmup") is False:
                # api.set_warmup_status(email, False)
                pass

            actions_log.append([
                datetime.now(ZoneInfo("US/Mountain")).strftime('%Y-%m-%d %H:%M:%S'),
                acc.get("customer_tag", "Unknown Client"), 
                email,
                final_status, 
                new_tag,
                reason,
                "-",
                "-"
            ])
            
            # Change Display Logic
            change_display = f"-> {new_tag}"
        else:
            change_display = "-"
        
        # 3. Format Strings for Sheet
        tags_str = ", ".join(final_tags)
        
        # Robust Daily Limit
        daily_limit = acc.get("limit", acc.get("daily_limit", 0))

        processed_accounts.append({
            "email": acc.get("email"),
            "status": final_status,
            "daily_limit": daily_limit,
            "warmup_score": f"{acc.get('stat_warmup_score', 0)}/100",
            "tags": tags_str,
            "customer_tag": acc.get("customer_tag", "-"),
            "change": change_display
        })

    report_data = {
        "client_name": "Ad-Hoc Run",
        "formatted_date": datetime.now(ZoneInfo("US/Mountain")).strftime('%Y-%m-%d %H:%M'),
        "total_sent": total_sent,
        "total_leads": total_leads,
        "total_replies": total_replies,
        "total_opportunities": 0,
        "campaigns": processed_campaigns,
        "accounts": processed_accounts,
        "share_email": report_email,  # Pass for fallback sharing
        "report_email": report_email
    }
    
    # 4. Generate Transition Summary (for Sheet & Email)
    transition_counts = {} # Only counts changes
    global_counts = {
        "Sending": 0, "Sick": 0, "Warming": 0, "Benched": 0
    }

    # Calculate Global Counts (Current State of All Accounts)
    for acc in processed_accounts:
        # Derived from tags string or logic
        tags_list = acc.get("tags", "").split(", ")
        primary = "Unknown"
        # Priority Order
        if "Sick" in tags_list: primary = "Sick"
        elif "Warming" in tags_list: primary = "Warming"
        elif "Benched" in tags_list: primary = "Benched"
        elif "Sending" in tags_list: primary = "Sending"
        
        if primary in global_counts:
            global_counts[primary] += 1

    transition_list = []
    
    for log in actions_log:
        # log format: [time, client, email, prev, new, reason, ...]
        new_status = log[4]
        # Clean key
        key = new_status.replace("status-", "").capitalize()
        transition_counts[key] = transition_counts.get(key, 0) + 1
        transition_list.append(f"{log[2]} -> {log[4]} ({log[5]})")

    # Add Summary to Report Data
    report_data["run_summary"] = {
        "total_actions": len(actions_log),
        "transitions": transition_list,
        "counts": global_counts, # Use GLOBAL counts for sheet
        "transition_counts": transition_counts 
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
                sheet_updated, result_val = update_client_sheet(report_data, sheet_id)
                
                # Check if fallback occurred (Success + URL returned)
                if sheet_updated and result_val and "https" in str(result_val):
                     # Parse new Sheet ID to ensure Action Log goes to the right place
                     try:
                         sheet_id = result_val.split("/d/")[1].split("/")[0]
                         logging.info(f"Failed to write to original. Created NEW Sheet: {sheet_id}")
                         emit_status("warning", f"Original sheet locked. Created NEW Sheet -> {result_val}", 82)
                         # Store this to return in result so main result shows the switch
                         sheet_error = f"Created NEW Sheet: {result_val}" 
                     except:
                         logging.warning("Could not parse new ID")

                elif not sheet_updated:
                     sheet_error = result_val

                # Update Action Log (Append)
                if actions_log and sheet_updated:
                    logging.info(f"Appending {len(actions_log)} actions to log...")
                    # Re-instantiate service 
                    creds = get_credentials()
                    if creds:
                        service = build('sheets', 'v4', credentials=creds)
                        try:
                            write_to_tab(service, sheet_id, "Action Log", actions_log, mode="APPEND")
                        except Exception as e:
                            logging.warning(f"Failed to append logs: {e}")
                
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
    parser.add_argument("--bench_percent", type=int, default=0, help="Target Bench %% (Default 0)")
    parser.add_argument("--ignore_customer_tags", action="store_true", help="Ignore (preserve) non-system tags")
    args = parser.parse_args()
    
    try:
        result = run_adhoc_report(args.key, args.sheet, args.report_email, args.warmup_threshold, args.bench_percent, args.ignore_customer_tags)
        # Final output for the API to capture as the "Result"
        print(json.dumps({"type": "result", "data": result}), flush=True)
    except Exception as e:
        # Catch-all for top-level script errors
        error_json = {"type": "error", "message": f"Critical Script Crash: {str(e)}"}
        print(json.dumps(error_json), flush=True)
        sys.exit(1)
