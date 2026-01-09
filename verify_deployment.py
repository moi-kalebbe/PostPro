
import requests
import json
import sys

# Production URL
API_URL = "https://postpro.nuvemchat.com/api/v1"

# License Key from the user's screenshot/context (or redundant if we can't get it)
# User provided screenshot has: 6ed125ed-b659-4a29-b576-f527a03fca22
LICENSE_KEY = "6ed125ed-b659-4a29-b576-f527a03fca22"

print(f"Testing Production API: {API_URL}")

HEADERS = {
    "X-License-Key": LICENSE_KEY,
    "Content-Type": "application/json"
}

# 1. Test Sync Profile with PUSH data (New Feature)
print("\n--- Verifying Deployment (Sync Profile) ---")
sync_data = {
    "site_title": "Deployment Verification",
    "categories": [{"name": "Test", "slug": "test", "count": 1}]
}

try:
    resp = requests.post(f"{API_URL}/project/sync-profile", headers=HEADERS, json=sync_data, timeout=10)
    print(f"Status: {resp.status_code}")
    
    try:
        data = resp.json()
        print(f"Message: {data.get('message')}")
        
        if "pushed" in data.get('message', '').lower():
            print("\n✅ SUCCESS: New code is active! (Push sync detected)")
        else:
            print("\n❌ FAILURE: Old code is active. (Push sync ignored)")
            
    except:
        print(f"Raw Response: {resp.text}")

except Exception as e:
    print(f"Request Failed: {e}")

# 2. Test Post Keywords (Bug Fix check)
print("\n--- Verifying Keyword Saving ---")
keywords_data = {
    "keywords": ["debug_deploy_1", "debug_deploy_2", "debug_deploy_3", "debug_deploy_4", "debug_deploy_5"]
}
try:
    resp = requests.post(f"{API_URL}/project/keywords", headers=HEADERS, json=keywords_data, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Keywords Request Failed: {e}")
