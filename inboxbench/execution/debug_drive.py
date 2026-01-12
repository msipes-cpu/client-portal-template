import sys
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime

def test_drive_write(creds_path):
    print(f"Testing Drive API WRITE access with {creds_path}")
    try:
        # Request full Drive scope
        creds = service_account.Credentials.from_service_account_file(
            creds_path, scopes=['https://www.googleapis.com/auth/drive']
        )
        service = build('drive', 'v3', credentials=creds)
        
        # Try creating a file
        file_metadata = {'name': f'inboxbench_test_{datetime.datetime.now()}.txt'}
        file = service.files().create(body=file_metadata, fields='id').execute()
        
        print(f"Drive Write Success! Created file ID: {file.get('id')}")
        
        # Clean up
        service.files().delete(fileId=file.get('id')).execute()
        print("Cleaned up test file.")
        return True
    except Exception as e:
        print(f"Drive Write Failed: {e}")
        return False

if __name__ == "__main__":
    test_drive_write("../credentials.json")
