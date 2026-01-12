import sys
import os
import requests
# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inboxbench.lib.instantly_api import InstantlyAPI

REQUIRED_TAGS = [
    "status-active",
    "status-warming",
    "status-benched",
    "status-sick",
    "status-dead"
]

def init_tags(api_key):
    api = InstantlyAPI(api_key)
    
    print("--- Checking Existing Tags ---")
    existing_tags = api.list_custom_tags()
    existing_labels = []
    if isinstance(existing_tags, dict):
        items = existing_tags.get("items", [])
        existing_labels = [t.get('label') for t in items]
    elif isinstance(existing_tags, list):
        existing_labels = [t.get('label') for t in existing_tags]
    
    print(f"Found: {existing_labels}")
    
    for tag in REQUIRED_TAGS:
        if tag in existing_labels:
            print(f"✅ {tag} exists.")
        else:
            print(f"Creating {tag}...")
            # Endpoint for creating tag: POST /custom-tags
            # Payload: {"label": "status-active", "color": "#HEX"}
            try:
                # Basic implementation since lib might not have create_tag
                url = f"{api.base_url}/custom-tags"
                resp = requests.post(url, headers=api.headers, json={"label": tag})
                if resp.status_code in [200, 201]:
                    print(f"✅ Created {tag}")
                else:
                    print(f"❌ Failed to create {tag}: {resp.text}")
            except Exception as e:
                print(f"❌ Error creating {tag}: {e}")

if __name__ == "__main__":
    # Hardcoded key from debug previous step since env not reliable
    key = "YTA5NTM0NzgtZTgzNC00OGFmLWJlZmMtNzdiMzkxZDg1ZGE2OkRFaWx2aG1hU3d5aQ=="
    init_tags(key)
