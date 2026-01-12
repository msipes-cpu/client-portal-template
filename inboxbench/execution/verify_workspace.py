import argparse
import json
import logging
import sys
import time
import requests
from datetime import datetime

# Add project root to path
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging to stderr so it doesn't pollute stdout JSON
logging.basicConfig(stream=sys.stderr, level=logging.INFO)

def verify_workspace(api_key):
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # 1. READ TEST: List Accounts & Org Info
    base_url = "https://api.instantly.ai/api/v2"
    
    try:
        # Fetch Organization Info for correct Workspace Name
        org_name = "Instantly Workspace"
        try:
             # Try listing organizations
             org_resp = requests.get(f"{base_url}/organizations", headers=headers)
             if org_resp.status_code == 200:
                 org_data = org_resp.json()
                 # Handle { items: [...] } or [...]
                 orgs = org_data.get("items", []) if isinstance(org_data, dict) else org_data
                 
                 # If list, take first
                 if isinstance(orgs, list) and len(orgs) > 0:
                     org_name = orgs[0].get("name", org_name)
                 elif isinstance(orgs, dict): # Fallback if single object
                     org_name = orgs.get("name", org_name)
        except Exception as e:
            logging.warning(f"Could not fetch org name: {e}")

        # Fetch Accounts (for count and tag scavenging)
        resp = requests.get(f"{base_url}/accounts", headers=headers, params={"limit": 100})
        if resp.status_code != 200:
            return {"success": False, "error": f"Read failed: {resp.status_code} - {resp.text}"}
            
        data = resp.json()
        accounts = data.get("items", []) if isinstance(data, dict) else data
        account_count = len(accounts)
        
        # 3. TAG EXISTENCE CHECK
        # Hybrid approach: Check global definitions AND scan actual accounts
        tag_status = {
            "Warming": False,
            "Sending": False,
            "Benched": False,
            "Sick": False
        }
        
        found_labels = set()

        # A. Scan fetched accounts for tags (in case custom-tags endpoint fails)
        for acc in accounts:
            acc_tags = acc.get("tags", [])
            if acc_tags and isinstance(acc_tags, list):
                for t in acc_tags:
                    if isinstance(t, dict):
                        found_labels.add(t.get("label", ""))
                    elif isinstance(t, str):
                        found_labels.add(t)

        # B. List all custom tags from endpoint with pagination
        try:
            tags_url = f"{base_url}/custom-tags"
            params = {"limit": 100}
            
            while True:
                tags_resp = requests.get(tags_url, headers=headers, params=params)
                
                if tags_resp.status_code == 200:
                    tags_data = tags_resp.json()
                    # Handle { items: [...] } or [...]
                    page_items = tags_data.get("items", []) if isinstance(tags_data, dict) else tags_data
                    
                    if isinstance(page_items, list):
                        for t in page_items:
                            found_labels.add(t.get("label", ""))
                            
                    # Check for pagination
                    next_cursor = tags_data.get("next_starting_after") if isinstance(tags_data, dict) else None
                    if next_cursor:
                        params["starting_after"] = next_cursor
                    else:
                        break # No more pages
                else:
                    logging.warning(f"Failed to list tags page: {tags_resp.status_code}")
                    break
                    
        except Exception as e:
            logging.warning(f"Tag list error: {e}")
            
        # Check against found labels (normalize for "Bench" vs "Benched")
        for label in found_labels:
            if label == "Warming": tag_status["Warming"] = True
            if label == "Sending": tag_status["Sending"] = True
            if label == "Sick": tag_status["Sick"] = True
            if label in ["Bench", "Benched"]: tag_status["Benched"] = True

    except Exception as e:
        return {"success": False, "error": f"Read Error: {str(e)}"}

    # 2. WRITE TEST: Create and Delete Tag
    tag_name = f"IB_VERIFY_{int(time.time())}"
    tag_id = None
    
    try:
        # Create Tag
        create_resp = requests.post(
            f"{base_url}/custom-tags", 
            headers=headers, 
            json={"label": tag_name, "description": "Temporary verification tag"}
        )
        
        if create_resp.status_code in [200, 201]:
            tag_data = create_resp.json()
            tag_id = tag_data.get("id")
            logging.info(f"Write successful, created tag ({tag_id})")
        else:
             return {
                "success": False, 
                "error": f"Write failed (Create Tag): {create_resp.status_code}",
                "account_count": account_count,
                "read_access": True,
                "write_access": False
            }

        # Delete Tag
        if tag_id:
            del_resp = requests.delete(f"{base_url}/custom-tags/{tag_id}", headers=headers)
            if del_resp.status_code == 200:
                 logging.info("Cleanup successful")
            else:
                 logging.warning(f"Failed to delete temp tag {tag_id}")

    except Exception as e:
        return {
            "success": False, 
            "error": f"Write Error: {str(e)}",
            "account_count": account_count,
            "read_access": True,
            "write_access": False
        }

    return {
        "success": True,
        "workspace_name": org_name,
        "account_count": account_count,
        "tags": tag_status,
        "read_access": True,
        "write_access": True
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=True, help="Instantly API Key")
    args = parser.parse_args()
    
    result = verify_workspace(args.key)
    print(json.dumps(result))
