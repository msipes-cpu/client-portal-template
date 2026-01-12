import argparse
import json
import logging
import sys
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Setup logging
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='%(levelname)s: %(message)s')

# Constants
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
IMPERSONATED_USER = "msipes@sipesautomation.com"

# Locate credentials
def get_credentials():
    auth_debug = []
    
    # Try env var for raw JSON content first
    json_creds = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if json_creds:
        try:
            info = json.loads(json_creds)
            creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
            creds = creds.with_subject(IMPERSONATED_USER)
            return creds
        except Exception as e:
            auth_debug.append(f"Env var load failed: {str(e)}")
            logging.warning(f"Failed to load creds from env var: {e}")
    else:
        auth_debug.append("GOOGLE_CREDENTIALS_JSON not set")

    # Try multiple locations for credentials file
    candidates = [
        "credentials.json",
        "../credentials.json",
        "/Users/michaelsipes/Coding/SA Workspace/credentials.json",
        os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    ]
    
    creds = None
    for c in candidates:
        if c and os.path.exists(c):
            try:
                creds = service_account.Credentials.from_service_account_file(c, scopes=SCOPES)
                # Impersonate user to own the file
                creds = creds.with_subject(IMPERSONATED_USER)
                break
            except Exception as e:
                auth_debug.append(f"File {c} load failed: {str(e)}")
                logging.warning(f"Failed to load creds from {c}: {e}")
                continue
        else:
            auth_debug.append(f"File {c} not found")
    
    if not creds:
        logging.error("Could not find valid credentials.json")
        return {"error": "Authentication failed", "debug": auth_debug}
    
    return creds

def create_sheet(title):
    creds_result = get_credentials()
    if isinstance(creds_result, dict) and "error" in creds_result:
         return {"success": False, "error": creds_result["error"], "debug": creds_result.get("debug")}
    
    creds = creds_result
    service = build('sheets', 'v4', credentials=creds)

    try:
        logging.info(f"Creating sheet '{title}' as {IMPERSONATED_USER}...")
        spreadsheet = {
            'properties': {
                'title': title
            }
        }
        spreadsheet = service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId,spreadsheetUrl').execute()
        
        sheet_id = spreadsheet.get('spreadsheetId')
        sheet_url = spreadsheet.get('spreadsheetUrl')
        
        logging.info(f"Created: {sheet_url}")
        
        return {
            "success": True, 
            "sheet_id": sheet_id, 
            "sheet_url": sheet_url,
            "owner": IMPERSONATED_USER,
            # We don't return creds directly in JSON, but helper function returns it
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", default="InboxBench Verification Report")
    parser.add_argument("--share_email", help="Email address to share the sheet with")
    args = parser.parse_args()
    
    result = create_sheet(args.title)
    
    if result["success"] and args.share_email:
        # We need credentials again to share
        creds_result = get_credentials()
        # Assume it succeeds since create_sheet succeeded (unless transient)
        if hasattr(creds_result, 'with_subject'): # It's a credential object
             creds = creds_result
             try:
                drive_service = build('drive', 'v3', credentials=creds) 
                
                permission = {
                    'type': 'user',
                    'role': 'writer',
                    'emailAddress': args.share_email
                }
                
                drive_service.permissions().create(
                    fileId=result["sheet_id"],
                    body=permission,
                    fields='id',
                    sendNotificationEmail=True
                ).execute()
                
                result["shared_with"] = args.share_email
                logging.info(f"Shared with {args.share_email}")
                
             except Exception as share_error:
                logging.error(f"Failed to share: {share_error}")
                result["share_error"] = str(share_error)

    print(json.dumps(result))
