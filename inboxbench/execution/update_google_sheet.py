import os
import json
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = '../../credentials.json'

def get_credentials():
    """Locate and load service account credentials from env var or local file."""
    creds = None
    
    # 1. Try Environment Variable
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        try:
            creds_dict = json.loads(creds_json)
            creds = service_account.Credentials.from_service_account_info(
                creds_dict, scopes=SCOPES)
        except Exception as e:
            logging.error(f"Failed to load credentials from ENV: {e}")

    # 2. Try Local File (Fallback)
    if not creds:
        # Resolve path relative to this script
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, '../../credentials.json')
        
        # Check absolute path fallback (common in workspace)
        if not os.path.exists(file_path):
             # Try workspace root if we are in a subdirectory structure
             file_path = os.path.abspath(os.path.join(base_dir, "../../../credentials.json"))

        if os.path.exists(file_path):
            try:
                logging.info(f"Loading credentials from file: {file_path}")
                creds = service_account.Credentials.from_service_account_file(
                    file_path, scopes=SCOPES)
            except Exception as e:
                logging.error(f"Failed to load credentials from file: {e}")
        else:
             logging.warning(f"Credentials file not found at: {file_path}")

    if not creds:
        logging.error("No valid Google Cloud credentials found (ENV or File).")
        return None

    # 3. Apply Impersonation (CRITICAL)
    try:
        delegated_creds = creds.with_subject('msipes@sipesautomation.com')
        # Test the delegation by making a lightweight call or just assume success?
        # Typically we just return the object. Access errors happen at usage time.
        logging.info("Impersonating msipes@sipesautomation.com for sheet update...")
        return delegated_creds
    except Exception as e:
        # This catch block rarely fires for just *creating* the object, 
        # errors usually happen when making a request.
        logging.warning(f"Impersonation setup failed (fallback to SA): {e}")
        return creds

def update_client_sheet(client_data, spreadsheet_id):
    """
    Updates the Google Sheet for a specific client.
    
    Args:
        client_data (dict): The report data for a single client.
        spreadsheet_id (str): The Google Sheet ID for this client.
    """
    if not spreadsheet_id:
        msg = f"No Google Sheet ID provided for client {client_data.get('client_name')}"
        logging.warning(msg)
        return False, msg

    creds = get_credentials()
    if not creds:
        return False, "Failed to load credentials"

    try:
        service = build('sheets', 'v4', credentials=creds)
        
        # dynamic tab name resolution
        sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = sheet_metadata.get('sheets', [])
        
        target_sheet_title = 'Sheet1' # Default fallback
        if sheets:
            # logic: look for 'Report', else use the first one
            titles = [s['properties']['title'] for s in sheets]
            if 'Report' in titles:
                target_sheet_title = 'Report'
            elif 'Sheet1' in titles:
                target_sheet_title = 'Sheet1'
            else:
                target_sheet_title = titles[0] # Use the very first sheet if defaults mismatch
        
        logging.info(f"Targeting sheet tab: '{target_sheet_title}'")
        
        # Prepare data for the distinct tables
        # 1. Overview
        overview_data = [
            ["Metric", "Value"],
            ["Client Name", client_data.get('client_name', 'N/A')],
            ["Date", client_data.get('formatted_date', 'N/A')],
            ["Total Sent", client_data.get('total_sent', 0)],
            ["Total Leads", client_data.get('total_leads', 0)],
            ["Replies", client_data.get('total_replies', 0)],
            ["Opportunities", client_data.get('total_opportunities', 0)],
            ["Total Accounts", len(client_data.get('accounts', []))],
            ["Total Campaigns", len(client_data.get('campaigns', []))],
        ]

        # 2. Campaign Performance
        campaign_header = ["Campaign Name", "Status", "Sent", "Opens", "Replies", "Click Rate", "Reply Rate"]
        campaign_rows = []
        for camp in client_data.get('campaigns', []):
            campaign_rows.append([
                camp.get('name', 'Unknown'),
                camp.get('status', 'Unknown'),
                camp.get('sent', 0),
                camp.get('opens', 0),
                camp.get('replies', 0),
                f"{camp.get('click_rate', 0)}",
                f"{camp.get('reply_rate', 0)}"
            ])
        
        # 3. Account Health
        account_header = ["Email", "Status", "Daily Limit", "Warmup Score", "Tags"]
        account_rows = []
        for acc in client_data.get('accounts', []):
            account_rows.append([
                acc.get('email', 'Unknown'),
                acc.get('status', 'Unknown'),
                acc.get('daily_limit', 0),
                f"{acc.get('warmup_score', 'N/A')}",
                acc.get('tags', '')
            ])

        # Prepare Data for Tabs
        
        # TAB 1: Daily Snapshot (Overview + Accounts)
        # Combine overview and account list into one readable sheet?
        # User requested specific tabs: "Daily Snapshot", "Action Log", "Client Summary", "Domain Health"
        # For now, let's stick to the existing "Report" format for the main tab, but rename it "Daily Snapshot"
        # and add logic to update other tabs if data is provided.
        
        # Snapshot Data Construction
        snapshot_values = []
        snapshot_values.extend(overview_data)
        snapshot_values.append([])
        snapshot_values.append(["CAMPAIGN PERFORMANCE"])
        snapshot_values.extend([campaign_header] + campaign_rows)
        snapshot_values.append([])
        snapshot_values.append(["ACCOUNT HEALTH"])
        snapshot_values.extend([account_header] + account_rows)
        
        # Write Snapshot (Overwrite)
        write_to_tab(service, spreadsheet_id, "Daily Snapshot", snapshot_values, mode="OVERWRITE")

        logging.info(f"Updated Daily Snapshot for {client_data.get('client_name')}")
        return True, None

    except HttpError as err:
        logging.error(f"Google Sheets API Error: {err}")
        return False, str(err)
    except Exception as e:
        logging.error(f"Unexpected error in update_client_sheet: {e}")
        return False, str(e)

def write_to_tab(service, spreadsheet_id, tab_name, data, mode="OVERWRITE"):
    """
    Helper to write data to a specific tab.
    Creates the tab if it doesn't exist.
    """
    # 1. Ensure tab exists
    try:
        sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = sheet_metadata.get('sheets', [])
        titles = [s['properties']['title'] for s in sheets]
        
        if tab_name not in titles:
            req = {'addSheet': {'properties': {'title': tab_name}}}
            service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={'requests': [req]}).execute()
    except Exception as e:
        logging.warning(f"Could not check/create tab {tab_name}: {e}")

    # 2. Write Data
    try:
        range_name = f"'{tab_name}'!A1"
        
        if mode == "OVERWRITE":
            service.spreadsheets().values().clear(spreadsheetId=spreadsheet_id, range=f"'{tab_name}'").execute()
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id, range=range_name,
                valueInputOption='RAW', body={'values': data}
            ).execute()
        elif mode == "APPEND":
            service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id, range=range_name,
                valueInputOption='RAW', insertDataOption='INSERT_ROWS', body={'values': data}
            ).execute()

    except HttpError as err:
        logging.error(f"Google Sheets API Error: {err}")
        return False, str(err)
    except Exception as e:
        logging.error(f"Unexpected error in update_client_sheet: {e}")
        return False, str(e)
    
    return True, None

if __name__ == "__main__":
    # Test with dummy data and config
    config_path = os.path.join(os.path.dirname(__file__), '../config/config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Mock data based on the structure we expect
    mock_client_data = {
        "client_name": "Sipes Automation (Test)",
        "formatted_date": "2024-01-09",
        "total_sent": 120,
        "total_leads": 5,
        "total_replies": 2,
        "total_opportunities": 1,
        "campaigns": [
             {"name": "Test Campaign 1", "status": "Active", "sent": 100, "opens": 50, "replies": 2, "click_rate": 5, "reply_rate": 2}
        ],
        "accounts": [
             {"email": "test@example.com", "status": "Active", "daily_limit": 50, "warmup_score": "98/100"}
        ]
    }
    
    # Get first profile's sheet ID
    profiles = config.get('client_profiles', [])
    if profiles:
        test_sheet_id = profiles[0].get('google_sheet_id')
        print(f"Testing update for Sheet ID: {test_sheet_id}")
        update_client_sheet(mock_client_data, test_sheet_id)
    else:
        print("No client profiles found in config.")
