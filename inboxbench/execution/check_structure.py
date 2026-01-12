import sys
import os
import json
import logging
# Add parent dir
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.instantly_api import InstantlyAPI
from lib.utils import load_config

config = load_config()
api_key = config.get("instantly_api_key")
api = InstantlyAPI(api_key)

print("--- CAMPAIGN TAGS CHECK ---")
campaigns = api.list_campaigns().get('items', [])
if campaigns:
    c = campaigns[0]
    print(f"Name: {c.get('name')}")
    print(f"email_tag_list: {c.get('email_tag_list')}")
    # Check if there is any other tag field
    print(f"Full Keys: {list(c.keys())}")

print("\n--- ACCOUNT DETAILS CHECK ---")
accounts = api.list_accounts().get('items', [])
if accounts:
    acc = accounts[0]
    acc_id = acc.get('email') # Wait, ID is email? Or 'id'?
    # In list output, I saw 'email', but not 'id'? 
    # Let's check listing again. The previous output keys:
    # ['email', 'timestamp_created', ..., 'organization', ...]
    # No 'id' key? Usually email is the ID for accounts in Instantly? Or it's missing from my print?
    # I'll check if 'id' is in keys.
    
    # Try fetching details using email as ID or finding ID
    # If API V2 /accounts returns items, they should have ID.
    # Previous output keys: ['email', 'timestamp_created', ...]. NO 'id'.
    # That's strange. Maybe 'email' IS the identifier for V2 endpoints?
    # Let's try GET /accounts/{email}
    
    print(f"Fetching details for {acc.get('email')}...")
    try:
        # Try using email
        details = api._get(f"/accounts/{acc.get('email')}")
        print("Details Keys:", list(details.keys()) if details else "None")
        print("Details Tags:", details.get('tags'))
    except:
        print("Failed with email as ID.")

