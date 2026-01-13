import os
import sys
import json
import logging

# Add project root to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from inboxbench.execution.update_google_sheet import create_and_share_sheet, update_client_sheet, get_credentials

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_recovery():
    print("--- Starting Recovery Test ---")
    
    # 1. Create Data
    dummy_data = {
        "client_name": "TEST RECOVERY",
        "formatted_date": "2026-01-12",
        "total_sent": 100,
        "total_leads": 10,
        "total_replies": 5,
        "total_opportunities": 1,
        "campaigns": [],
        "accounts": []
    }

    # 2. Try to Create New Sheet directly
    print("Attempting to create NEW sheet...")
    try:
        new_id, new_url = create_and_share_sheet("InboxBench - AUTO RECOVERY TEST")
        print(f"✅ SUCCESS! Created Sheet: {new_url}")
        
        # 3. Try Update
        print(f"Attempting to write to {new_id}...")
        success, err = update_client_sheet(dummy_data, new_id)
        if success:
            print("✅ WRITE SUCCESSFUL")
        else:
            print(f"❌ WRITE FAILED: {err}")

    except Exception as e:
        print(f"❌ CREATION FAILED: {e}")

if __name__ == "__main__":
    # Ensure credentials.json is found
    if not os.path.exists("credentials.json") and not os.path.exists("../credentials.json"):
        print("WARNING: credentials.json not found in obvious paths.")
    
    test_recovery()
