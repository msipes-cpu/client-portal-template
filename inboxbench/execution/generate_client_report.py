import sys
import os
import json
import logging
from datetime import datetime

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.instantly_api import InstantlyAPI
from lib.utils import setup_logging

def generate_client_report(api_key, tag_name, client_name):
    """
    Generates a report for a specific client.
    Fetches data directly using tag filters.
    
    Args:
        api_key (str): Instantly API Key
        tag_name (str): The tag name to filter by (e.g. "Sipes Automation")
        client_name (str): The display name for the client
    """
    api = InstantlyAPI(api_key)
    
    logging.info(f"Generating report for client: {client_name} (Tag: {tag_name})")

    # 1. Resolve Tag ID
    tag_id = api.get_tag_id_by_name(tag_name)
    if not tag_id:
        logging.warning(f"Tag '{tag_name}' not found in Instantly workspace. skipping.")
        return {
            "client_name": client_name,
            "formatted_date": datetime.now().strftime('%Y-%m-%d'),
            "error": "Tag not found",
            "campaigns": [],
            "accounts": [],
            "total_sent": 0,
            "total_leads": 0,
            "total_replies": 0,
            "total_opportunities": 0
        }
    
    # 2. Fetch filtered data
    c_data = api.list_campaigns(tag_ids=tag_id)
    a_data = api.list_accounts(tag_ids=tag_id)
    
    client_campaigns = c_data.get("items", []) if isinstance(c_data, dict) else c_data
    client_accounts = a_data.get("items", []) if isinstance(a_data, dict) else a_data
    
    if not client_campaigns: client_campaigns = []
    if not client_accounts: client_accounts = []

    # 3. Process Accounts
    processed_accounts = []
    for acc in client_accounts:
        # V2 API typically returns 'stat_warmup_score' (1-100) or 'warmup_score'
        warmup_score = acc.get("stat_warmup_score", 0)
        daily_limit = acc.get("limit", 0)
        status = acc.get("status_v2", acc.get("status", "Unknown"))
        
        processed_accounts.append({
            "email": acc.get("email"),
            "status": status,
            "daily_limit": daily_limit,
            "warmup_score": f"{warmup_score}/100"
        })

    # 4. Process Campaigns & Aggregates
    processed_campaigns = []
    total_sent = 0
    total_replies = 0
    total_leads = 0 # Need to fetch from analytics if possible, or derive
    total_opportunities = 0 # Typically requires CRM status check, simplified to 'leads' logic or 0 for now
    
    for camp in client_campaigns:
        camp_id = camp.get("id")
        name = camp.get("name")
        status = camp.get("status", "Unknown")
        
        # Get analytics summary
        summary = api.get_campaign_summary(camp_id)
        
        sent = summary.get("sent", 0) if summary else 0
        replies = summary.get("replies", 0) if summary else 0
        opens = summary.get("opens", 0) if summary else 0
        
        # Calculate rates
        reply_rate = round((replies / sent * 100), 2) if sent > 0 else 0
        click_rate = 0 # Placeholder if not in summary
        
        total_sent += sent
        total_replies += replies
        
        processed_campaigns.append({
            "name": name,
            "status": status,
            "sent": sent,
            "opens": opens,
            "replies": replies,
            "click_rate": click_rate,
            "reply_rate": reply_rate
        })

    report = {
        "client_name": client_name,
        "client_tag": tag_name,
        "formatted_date": datetime.now().strftime('%Y-%m-%d'),
        "total_sent": total_sent,
        "total_leads": total_opportunities, # Using opportunity count as leads for now
        "total_replies": total_replies,
        "total_opportunities": total_opportunities,
        "campaigns": processed_campaigns,
        "accounts": processed_accounts
    }

    return report
