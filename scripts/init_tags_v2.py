import os
import sys
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from inboxbench.lib.instantly_api import InstantlyAPI

logging.basicConfig(level=logging.INFO, format='%(message)s')

def init_tags_v2():
    api_key = "YTA5NTM0NzgtZTgzNC00OGFmLWJlZmMtNzdiMzkxZDg1ZGE2OkRFaWx2aG1hU3d5aQ=="
    api = InstantlyAPI(api_key)
    print("--- Initializing Instantly Tags (v2) ---\n")
    
    # 1. Fetch Existing
    existing_tags = api.list_custom_tags()
    items = existing_tags.get("items", []) if isinstance(existing_tags, dict) else existing_tags
    if not items: items = []
    
    existing_map = {t.get("label"): t.get("id") for t in items}
    print(f"Current Tags: {list(existing_map.keys())}")
    
    # 2. Define New "Simple" Tags
    new_tags = [
        {"label": "Active", "color": "#10B981"},    # Emerald Green
        {"label": "Warming", "color": "#3B82F6"},   # Blue
        {"label": "Sick", "color": "#EF4444"},      # Red
        {"label": "Benched", "color": "#6B7280"},   # Gray
        {"label": "Dead", "color": "#111827"}       # Black
    ]
    
    # 3. Create New Tags
    for tag in new_tags:
        label = tag["label"]
        if label not in existing_map:
            print(f"Creating '{label}'...")
            try:
                resp = api.create_custom_tag(label, tag["color"])
                print(f"✅ Created.")
            except Exception as e:
                print(f"❌ Failed to create {label}: {e}")
        else:
            print(f"✓ '{label}' already exists.")

    # 4. Delete Old "status-" Tags (Validation)
    legacy_prefixes = ["status-"]
    
    print("\n--- Cleanup Legacy Tags ---")
    for label, tid in existing_map.items():
        if any(label.startswith(p) for p in legacy_prefixes):
            print(f"Deleting legacy tag: {label} ({tid})...")
            try:
                if api.delete_custom_tag(tid):
                    print("✅ Deleted.")
                else:
                    print("❌ Failed delete API call.")
            except Exception as e:
                print(f"❌ Exception: {e}")
    
    print("\n--- Complete ---")

if __name__ == "__main__":
    init_tags_v2()
