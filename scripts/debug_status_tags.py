import sys
import os
import json
# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inboxbench.lib.instantly_api import InstantlyAPI

def debug_status_tags(api_key):
    api = InstantlyAPI(api_key)
    
    print("--- 1. Fetching Accounts (Sample) ---")
    accounts_data = api.list_accounts()
    if isinstance(accounts_data, list):
        accounts = accounts_data
    else:
        accounts = accounts_data.get("items", [])
    
    if accounts:
        for acc in accounts:
            print(f"Email: {acc.get('email')}")
            print(f"Status V2: {acc.get('status_v2')}")
            print(f"Status (legacy): {acc.get('status')}")
            print(f"Raw Tags field: {acc.get('tags')}")
            print("-" * 20)
    else:
        print("No accounts found.")

    print("\n--- 2. Fetching Custom Tags ---")
    tags_data = api.list_custom_tags()
    print(f"Raw Tags Response Type: {type(tags_data)}")
    if isinstance(tags_data, dict):
        print(f"Keys: {tags_data.keys()}")
        items = tags_data.get("items", [])
        print(f"Found {len(items)} tags.")
        for t in items:
            print(f"ID: {t.get('id')} -> Label: {t.get('label')}")
    elif isinstance(tags_data, list):
        print(f"Found {len(tags_data)} tags (List format).")
        for t in tags_data:
             print(f"ID: {t.get('id')} -> Label: {t.get('label')}")
    else:
        print(f"Unknown tags format: {tags_data}")

if __name__ == "__main__":
    # Load API Key from env if available (or use hardcoded for debug if env missing)
    # We will try to parse from command line or env
    key = os.environ.get("INSTANTLY_API_KEY")
    if len(sys.argv) > 1:
        key = sys.argv[1]
    
    if not key:
        print("Please provide API Key as arg or env var.")
        sys.exit(1)
        
    debug_status_tags(key)
