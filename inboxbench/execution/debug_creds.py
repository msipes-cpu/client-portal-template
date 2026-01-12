import os
import json
import logging
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build

logging.basicConfig(level=logging.INFO)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

def test_creds():
    json_creds = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if not json_creds:
        print("ERROR: GOOGLE_CREDENTIALS_JSON not found in env")
        return

    try:
        info = json.loads(json_creds)
        creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        print(f"Service Account Email: {creds.service_account_email}")
        print(f"Project ID: {creds.project_id}")
    except Exception as e:
        print(f"ERROR: Failed to load creds: {e}")
        return

    # Test Drive API
    try:
        drive_service = build('drive', 'v3', credentials=creds)
        print("Testing Drive API (List files)...")
        results = drive_service.files().list(pageSize=1, fields="files(id, name)").execute()
        print("Drive API Success. Files found:", results.get('files', []))
    except Exception as e:
        print(f"Drive API Failed: {e}")

    # Test Sheets API
    try:
        sheets_service = build('sheets', 'v4', credentials=creds)
        print("Testing Sheets API (Create Sheet)...")
        spreadsheet = {
            'properties': {
                'title': 'Debug Sheet'
            }
        }
        # Dry run not directly supported, but we'll try to create and expect success or 403
        res = sheets_service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId').execute()
        print(f"Sheets API Success. Created ID: {res.get('spreadsheetId')}")
        
        # Cleanup
        # drive_service.files().delete(fileId=res.get('spreadsheetId')).execute()
        # print("Cleaned up debug sheet.")
        
    except Exception as e:
        print(f"Sheets API Failed: {e}")

if __name__ == "__main__":
    test_creds()
