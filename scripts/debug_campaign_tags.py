import os
import sys
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from inboxbench.lib.instantly_api import InstantlyAPI

def check_campaign_tags():
    key = os.environ.get("INSTANTLY_API_KEY")
    if not key:
        print("No API Key")
        return

    api = InstantlyAPI(key)
    print("Fetching campaigns...")
    camps = api.list_campaigns()
    
    if camps and isinstance(camps, list) and len(camps) > 0:
        c = camps[0]
        print(f"Sample Campaign Keys: {list(c.keys())}")
        print(f"Tags field: {c.get('tags')}")
    else:
        print("No campaigns found or invalid format.")

if __name__ == "__main__":
    check_campaign_tags()
