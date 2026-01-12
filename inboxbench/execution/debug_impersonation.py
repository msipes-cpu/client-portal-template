import os
import json
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build

logging.basicConfig(level=logging.INFO)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
IMPERSONATED_USER = 'msipes@sipesautomation.com'

def test_impersonation():
    json_creds = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if not json_creds:
        print("ERROR: GOOGLE_CREDENTIALS_JSON not found")
        return

    try:
        info = json.loads(json_creds)
        creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        print(f"Service Account: {creds.service_account_email}")
        
        # ATTEMPT IMPERSONATION
        print(f"Attempting to impersonate: {IMPERSONATED_USER}")
        delegated_creds = creds.with_subject(IMPERSONATED_USER)
        
        # Test Drive API as Michael
        drive_service = build('drive', 'v3', credentials=delegated_creds)
        print("Listing files as Michael...")
        results = drive_service.files().list(pageSize=5, fields="files(id, name, owners)").execute()
        files = results.get('files', [])
        
        if not files:
            print("Auth successful (No files found, but no error).")
        else:
             print("Auth SUCCESS! Found files:")
             for f in files:
                 owner = f.get('owners', [{}])[0].get('emailAddress', 'Unknown')
                 print(f" - {f['name']} (Owner: {owner})")

        # Test Creation as Michael
        print("Attempting to CREATE file as Michael...")
        file_metadata = {
            'name': 'Debug Sheet (Impersonated)',
            'mimeType': 'application/vnd.google-apps.spreadsheet'
        }
        res = drive_service.files().create(body=file_metadata, fields='id').execute()
        print(f"CREATION SUCCESS! ID: {res.get('id')}")
        
        # Cleanup
        drive_service.files().delete(fileId=res.get('id')).execute()
        print("Cleanup successful.")

    except Exception as e:
        print(f"Impersonation Failed: {e}")

if __name__ == "__main__":
    test_impersonation()
