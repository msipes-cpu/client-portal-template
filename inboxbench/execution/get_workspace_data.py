import sys
import os
import json
import logging

# Add the parent directory to sys.path to allow imports from lib
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.utils import load_config, setup_logging
from lib.instantly_api import InstantlyAPI

def get_workspace_data(api_key):
    """
    Fetches all campaigns and accounts from Instantly.
    Returns: dict with 'campaigns' and 'accounts' lists.
    """
    api = InstantlyAPI(api_key)
    
    logging.info("Fetching campaigns...")
    c_data = api.list_campaigns()
    # V2 returns {"items": [...], "meta": ...} usually
    if isinstance(c_data, dict) and "items" in c_data:
        campaigns = c_data["items"]
    elif isinstance(c_data, list):
        campaigns = c_data
    else:
        campaigns = []
        logging.warning("Unknown Campaign response structure")

    logging.info("Fetching accounts...")
    a_data = api.list_accounts()
    if isinstance(a_data, dict) and "items" in a_data:
        accounts = a_data["items"]
    elif isinstance(a_data, list):
        accounts = a_data
    else:
        accounts = []
        logging.warning("Unknown Account response structure")

    if not campaigns: 
        logging.warning("List is empty or failed.")
    
    if not accounts: 
        logging.warning("List is empty or failed.")

    return {
        "campaigns": campaigns,
        "accounts": accounts
    }

if __name__ == "__main__":
    setup_logging()
    
    config = load_config()
    if not config:
        sys.exit(1)
        
    api_key = config.get("instantly_api_key")
    if not api_key:
        logging.error("Invalid or missing Instantly API Key in config.")
        sys.exit(1)

    data = get_workspace_data(api_key)
    
    # Output to stdout
    print(json.dumps(data, indent=2))
