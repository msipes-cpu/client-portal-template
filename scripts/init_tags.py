import os
import sys
import logging

# Add project root to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from inboxbench.lib.instantly_api import InstantlyAPI

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def init_tags():
    # Load API Key (Try locally hardcoded for this session, or from env)
    # Using the one from debug script for reliability in this manual run
    api_key = "YTA5NTM0NzgtZTgzNC00OGFmLWJlZmMtNzdiMzkxZDg1ZGE2OkRFaWx2aG1hU3d5aQ=="
    
    api = InstantlyAPI(api_key)
    print("--- Initializing Instantly Tags ---\n")
    
    # 1. Fetch Existing
    existing_tags = api.list_custom_tags()
    items = existing_tags.get("items", []) if isinstance(existing_tags, dict) else existing_tags
    if not items: items = []
    
    existing_labels = [t.get("label") for t in items]
    print(f"Found {len(items)} existing tags: {existing_labels}")
    
    # 2. Define Required Tags
    required_tags = [
        {"label": "status-active", "color": "#10B981"}, # Emerald Green
        {"label": "status-warming", "color": "#3B82F6"}, # Blue
        {"label": "status-sick", "color": "#EF4444"},    # Red
        {"label": "status-benched", "color": "#6B7280"}  # Gray
    ]
    
    # 3. Create Missing
    for tag in required_tags:
        label = tag["label"]
        if label not in existing_labels:
            print(f"Creating '{label}'...")
            try:
                resp = api.create_custom_tag(label, tag["color"])
                print(f"✅ Created: {resp}")
            except Exception as e:
                print(f"❌ Failed to create {label}: {e}")
        else:
            print(f"✓ '{label}' already exists.")

    print("\n--- Tag Initialization Complete ---")

if __name__ == "__main__":
    init_tags()
