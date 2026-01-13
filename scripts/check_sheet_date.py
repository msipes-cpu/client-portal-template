import os
import sys
import logging
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Add project root to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from inboxbench.execution.update_google_sheet import get_credentials

logging.basicConfig(level=logging.INFO)

def check_sheet():
    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)
    
    # 1. Check the "New" Sheet
    new_sheet_id = "1ZTjA6k486z2Rt5cQLgx1bc_P4bgLWAIfz0QqFpK6BPk"
    print(f"\n--- Checking Sheet: {new_sheet_id} ---")
    try:
        # Read Data (Daily Snapshot) - Range A1:B20 to see summary
        result = service.spreadsheets().values().get(
            spreadsheetId=new_sheet_id, range="'Daily Snapshot'!A1:B20").execute()
        values = result.get('values', [])
        print("Data Sample (Daily Snapshot - Top 20 rows):")
        for row in values:
            print(row)
            
        # Check Title
        meta = service.spreadsheets().get(spreadsheetId=new_sheet_id).execute()
        print(f"Title: {meta.get('properties', {}).get('title')}")
        
    except Exception as e:
        print(f"Error reading new sheet: {e}")

    # 2. List ALL Sheets visible to SA (to find 'malak')
    # Use Drive API
    print(f"\n--- Searching for 'InboxBench - malak' ---")
    try:
        drive_service = build('drive', 'v3', credentials=creds)
        # Search for files with name containing 'malak' and mimeType spreadsheet
        query = "name contains 'malak' and mimeType='application/vnd.google-apps.spreadsheet'"
        results = drive_service.files().list(q=query, pageSize=10, fields="nextPageToken, files(id, name, owners)").execute()
        items = results.get('files', [])
        
        if not items:
            print("No sheets found matching 'malak'.")
        else:
            print("Found potential matches:")
            for item in items:
                print(f"Name: {item['name']} | ID: {item['id']} | Owner: {item['owners'][0]['emailAddress'] if item.get('owners') else 'Unknown'}")
                # Try to write? No, just identifying for now.
    except Exception as e:
        print(f"Drive Search Error: {e}")

if __name__ == "__main__":
    check_sheet()
