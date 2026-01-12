import sys
import os
import json
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.instantly_api import InstantlyAPI
from lib.utils import load_config

config = load_config()
api = InstantlyAPI(config.get("instantly_api_key"))

print("Fetching custom tags...")
tags = api.list_custom_tags()
# Handle V2 response structure
items = []
if isinstance(tags, dict) and "items" in tags:
    items = tags["items"]
elif isinstance(tags, list):
    items = tags

if not items:
    print("No tags found.")
else:
    print(f"Found {len(items)} tags:")
    for t in items:
        print(f"- {t.get('label')} (ID: {t.get('id')})")
