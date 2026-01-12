import sys
import os
import requests
import base64
import json

def test_v1_key(key, desc):
    print(f"Testing V1 {desc}: {key[:10]}...")
    url = "https://api.instantly.ai/api/v1/campaign/list"
    try:
        response = requests.get(url, params={"api_key": key, "limit": 1})
        if response.status_code == 200:
            print(f"SUCCESS: V1 {desc} worked!")
            return True, "v1", response.json()
        return False, None, None
    except:
        return False, None, None

def test_v2_key(key, desc):
    print(f"Testing V2 {desc}: {key[:10]}...")
    url = "https://api.instantly.ai/api/v2/campaigns"
    headers = {"Authorization": f"Bearer {key}"}
    try:
        response = requests.get(url, headers=headers, params={"limit": 1})
        if response.status_code == 200:
            print(f"SUCCESS: V2 {desc} worked!")
            return True, "v2", response.json()
        print(f"FAILED V2 {desc}: {response.status_code}")
        # print(response.text)
        return False, None, None
    except Exception as e:
        print(f"ERROR V2: {e}")
        return False, None, None

raw_key = "YTA5NTM0NzgtZTgzNC00OGFmLWJlZmMtNzdiMzkxZDg1ZGE2OkdFcEZHcFhZbFd6cA==".strip()
candidates = [
    (raw_key, "Raw Key"),
]

try:
    decoded = base64.b64decode(raw_key).decode('utf-8')
    candidates.append((decoded, "Decoded Full"))
    if ":" in decoded:
        parts = decoded.split(":")
        candidates.append((parts[0], "Decoded Part 1"))
        candidates.append((parts[1], "Decoded Part 2"))
except:
    pass

for key, desc in candidates:
    # Try V1
    success, version, data = test_v1_key(key, desc)
    if success:
        print(f"FOUND_KEY:{version}:{key}")
        sys.exit(0)
    
    # Try V2
    success, version, data = test_v2_key(key, desc)
    if success:
        print(f"FOUND_KEY:{version}:{key}")
        # Print valid response structure to help refactoring
        print("SAMPLE_DATA:" + json.dumps(data)[:200])
        sys.exit(0)

print("NO_WORKING_KEY_FOUND")
sys.exit(1)
