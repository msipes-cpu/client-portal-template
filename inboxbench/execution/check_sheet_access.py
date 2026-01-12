import argparse
import json
import logging
import sys
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Setup logging
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='%(levelname)s: %(message)s')

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_credentials():
    json_creds = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if json_creds:
        try:
            info = json.loads(json_creds)
            return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        except Exception:
            pass
    return None

def check_access(sheet_url):
    creds = get_credentials()
    if not creds:
        return {"success": False, "error": "Server missing credentials"}

    try:
        service = build('sheets', 'v4', credentials=creds)
        
        # Extract ID
        if "/d/" not in sheet_url:
             return {"success": False, "error": "Invalid URL format"}
        
        sheet_id = sheet_url.split("/d/")[1].split("/")[0]

        # Try to read metadata first (Viewer check)
        sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        title = sheet_metadata.get('properties', {}).get('title')
        
        # Try to update a dummy cell (Editor check)
        # We'll update a safe cell like Z1000 with empty content or same content
        # Actually, appending to a temporary made-up range is safer/easier to undo?
        # A simple update to A1 with existing value is also fine, or just batchUpdate with no requests?
        # A dummy batchUpdate is a good way to check write permissions without changing data.
        
        body = {
            "requests": []
        }
        service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body=body).execute()

        return {
            "success": True,
            "title": title,
            "service_account": creds.service_account_email
        }

    except HttpError as err:
        if err.resp.status == 403:
            return {
                "success": False, 
                "error": "Permission Denied. Please share sheet with service account.",
                "service_account": creds.service_account_email
            }
        return {"success": False, "error": str(err), "service_account": creds.service_account_email}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    args = parser.parse_args()
    
    print(json.dumps(check_access(args.url)))
