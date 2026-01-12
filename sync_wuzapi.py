import os
import django
import requests
import secrets
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.agencies.models import Agency

print("=== Syncing Agency with Wuzapi (Fixed) ===")

agency = Agency.objects.first()
if not agency:
    print("No agency found!")
    exit(1)

print(f"Agency: {agency.name}")
print(f"Agency ID: {agency.id}")

base_url = agency.wuzapi_instance_url.rstrip('/')
admin_token = settings.WUZAPI_ADMIN_TOKEN

headers = {
    'Content-Type': 'application/json',
    'Authorization': admin_token
}

# Get users from Wuzapi
print(f"\nFetching users from Wuzapi...")
resp = requests.get(f"{base_url}/admin/users", headers=headers, timeout=10)

if resp.status_code != 200:
    print(f"Error fetching users: {resp.status_code}")
    exit(1)

data = resp.json()
users = data.get('data', [])  # Correct parsing

print(f"Found {len(users)} users")

agency_user_name = f'agency_{agency.id}'
found_user = None

for user in users:
    print(f"  - {user.get('name')}")
    if user.get('name') == agency_user_name:
        found_user = user
        break

if found_user:
    print(f"\n✅ Found matching user in Wuzapi!")
    print(f"  ID: {found_user.get('id')}")
    print(f"  Name: {found_user.get('name')}")
    
    # Update agency
    agency.wuzapi_user_id = found_user.get('id')
    agency.wuzapi_token = found_user.get('token')
    agency.save(update_fields=['wuzapi_user_id', 'wuzapi_token'])
    
    print(f"\n✅ Agency updated in database!")
else:
    print(f"\n⚠️ No user found with name '{agency_user_name}'.")
    print(f"Creating new user...")
    
    # Create new user
    token = secrets.token_hex(32)
    site_url = getattr(settings, 'SITE_URL', '').rstrip('/')
    webhook_url = f"{site_url}/api/v1/webhook/wuzapi/{agency.id}/"
    
    payload = {
        'name': agency_user_name,
        'token': token,
        'webhook': webhook_url,
        'events': 'Message,ReadReceipt'
    }
    
    resp = requests.post(f"{base_url}/admin/users", json=payload, headers=headers, timeout=10)
    
    if resp.status_code == 200:
        result = resp.json()
        if result.get('success'):
            user_data = result.get('data', {})
            agency.wuzapi_user_id = user_data.get('id')
            agency.wuzapi_token = token
            agency.save(update_fields=['wuzapi_user_id', 'wuzapi_token'])
            print(f"✅ User created and agency updated!")
        else:
            print(f"❌ Creation failed: {result}")
    else:
        print(f"❌ HTTP Error: {resp.status_code}")
        print(resp.text)

print(f"\nFinal agency state:")
print(f"  wuzapi_user_id: {agency.wuzapi_user_id}")
print(f"  wuzapi_token: {agency.wuzapi_token[:20] if agency.wuzapi_token else 'N/A'}...")
