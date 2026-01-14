import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../inboxbench/execution')))

from update_google_sheet import create_and_share_sheet, update_client_sheet, get_credentials

# Setup Logging
logging.basicConfig(level=logging.INFO)

def test_sheet_logic():
    print("--- Starting Sheet Write Test ---")
    
    # 1. Test Credentials
    creds = get_credentials()
    if not creds:
        print("❌ Could not load credentials.")
        return
    print("✅ Credentials loaded.")

    # 2. Create & Share (Simulate Fallback)
    print("Attempting to Create and Share Sheet...")
    # Use a dummy email or the user's email if we knew it. 
    # Since I don't know the user's email for sure (dashboard input), I'll use a placeholder 
    # or skip sharing if I want to just test writing. 
    # BUT the user's issue might be related to the sharing breaking permissions?
    # I'll use a safe test email or just relying on the SA.
    
    target_email = "msipes@sipesautomation.com" # Using the admin email as test target
    
    try:
        sheet_id, sheet_url = create_and_share_sheet("InboxBench Debug Sheet", share_email=target_email)
        print(f"✅ Created Sheet: {sheet_url} (ID: {sheet_id})")
    except Exception as e:
        print(f"❌ Creation Failed: {e}")
        return

    # 3. Prepare Dummy Data
    client_data = {
        "client_name": "Debug Client",
        "formatted_date": "2024-01-14",
        "total_sent": 100,
        "total_leads": 10,
        "total_replies": 5,
        "total_opportunities": 1,
        "campaigns": [],
        "accounts": [],
        "run_summary": {
            "counts": {"Sending": 5, "Warming": 2},
            "transitions": []
        },
        "share_email": target_email 
    }

    # 4. Attempt Update
    print("Attempting Update...")
    # This calls the logic that ignores the return value of write_to_tab
    # But write_to_tab prints warnings to logging.
    
    success, result = update_client_sheet(client_data, sheet_id)
    
    if success:
        print("✅ update_client_sheet returned SUCCESS")
    else:
        print(f"❌ update_client_sheet returned FAILURE: {result}")

if __name__ == "__main__":
    test_sheet_logic()
