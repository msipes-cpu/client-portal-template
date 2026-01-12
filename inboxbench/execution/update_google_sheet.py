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
    """Locate and load service account credentials from env var."""
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if not creds_json:
        logging.error("GOOGLE_CREDENTIALS_JSON environment variable not found.")
        return None
    try:
        creds_dict = json.loads(creds_json)
        creds = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=SCOPES)
        return creds
    except Exception as e:
        logging.error(f"Error loading credentials from env: {e}")
        return None

def update_client_sheet(client_data, spreadsheet_id):
    """
    Updates the Google Sheet for a specific client.
    
    Args:
        client_data (dict): The report data for a single client.
        spreadsheet_id (str): The Google Sheet ID for this client.
    """
    if not spreadsheet_id:
        logging.warning(f"No Google Sheet ID provided for client {client_data.get('client_name')}. Skipping sheet update.")
        return

    creds = get_credentials()
    if not creds:
        return

    try:
        service = build('sheets', 'v4', credentials=creds)
        
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
        account_header = ["Email", "Status", "Daily Limit", "Warmup Score"]
        account_rows = []
        for acc in client_data.get('accounts', []):
            account_rows.append([
                acc.get('email', 'Unknown'),
                acc.get('status', 'Unknown'),
                acc.get('daily_limit', 0),
                f"{acc.get('warmup_score', 'N/A')}"
            ])

        # Batch Update Request
        # We will clear the sheet first or just overwrite. Overwriting is safer to preserve other tabs if they exist.
        # But for simplicity, we'll clear 'Sheet1' (or whatever main tab) and write.
        
        # Let's assume a 'Report' tab. If not exists, write to first tab.
        range_name = 'Sheet1!A1' 

        # Construct the full list of values to write
        # Overview
        final_values = []
        final_values.extend(overview_data)
        final_values.append([]) # Spacer

        # Campaigns
        final_values.append(["CAMPAIGN PERFORMANCE"])
        final_values.append(campaign_header)
        final_values.extend(campaign_rows)
        final_values.append([]) # Spacer

        # Accounts
        final_values.append(["ACCOUNT HEALTH"])
        final_values.append(account_header)
        final_values.extend(account_rows)

        body = {
            'values': final_values
        }

        # Clear existing content first to avoid artifacts
        service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id, range='Sheet1'
        ).execute()

        # Update
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption='RAW', body=body
        ).execute()

        logging.info(f"{result.get('updatedCells')} cells updated for client: {client_data.get('client_name')}")
        return True

    except HttpError as err:
        logging.error(f"Google Sheets API Error: {err}")
        return False

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
