import sys
import os
import json
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.utils import load_config

def create_master_sheet(creds_path, config_path):
    print(f"Using credentials from: {creds_path}")
    
    try:
        creds = service_account.Credentials.from_service_account_file(
            creds_path, scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        )
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return

    try:
        service = build('sheets', 'v4', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)
        
        # Create Sheet
        spreadsheet = {
            'properties': {
                'title': 'InboxBench Master Report'
            }
        }
        spreadsheet = service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId').execute()
        sheet_id = spreadsheet.get('spreadsheetId')
        print(f"Created Spreadsheet ID: {sheet_id}")

        # Share with user if email is known
        config = load_config(config_path)
        user_email = config.get("reporting_email") if config else None
        
        if user_email:
            print(f"Sharing with {user_email}...")
            try:
                drive_service.permissions().create(
                    fileId=sheet_id,
                    body={'type': 'user', 'role': 'writer', 'emailAddress': user_email}
                ).execute()
                print("Shared successfully.")
            except Exception as share_err:
                print(f"Warning: Could not share sheet: {share_err}")
                print("You may need to manually share it from the service account if domain restricted.")
        
        # Update Config
        if config:
            config["google_sheet_id"] = sheet_id
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            print("Updated config.json with new Sheet ID.")

    except Exception as e:
        print(f"API Error: {e}")

if __name__ == "__main__":
    # Assume credentials.json is in root or inboxbench root
    # Try finding it
    candidates = [
        "credentials.json", 
        "../credentials.json", 
        "/Users/michaelsipes/Coding/SA Workspace/credentials.json"
    ]
    
    found_creds = None
    for c in candidates:
        if os.path.exists(c):
            found_creds = c
            break
            
    if not found_creds:
        print("credentials.json not found in common locations.")
        sys.exit(1)
        
    config_file = "config/config.json"
    if not os.path.exists(config_file):
        config_file = "../config/config.json"
        
    create_master_sheet(found_creds, config_file)
