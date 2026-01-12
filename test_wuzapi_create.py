import os
import django
import secrets
import requests
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.agencies.models import Agency

print("=== Wuzapi User Creation Test ===")

agency = Agency.objects.first()
if not agency:
    print("No agency found!")
    exit(1)

print(f"Agency: {agency.name}")
print(f"Agency ID: {agency.id}")
print(f"Current wuzapi_user_id: {agency.wuzapi_user_id}")

base_url = agency.wuzapi_instance_url.rstrip('/')
admin_token = settings.WUZAPI_ADMIN_TOKEN

# Test payload
token = secrets.token_hex(32)
site_url = getattr(settings, 'SITE_URL', '').rstrip('/')
webhook_url = f"{site_url}/api/v1/webhook/wuzapi/{agency.id}/"

payload = {
    'name': f'agency_{agency.id}',
    'token': token,
    'webhook': webhook_url,
    'events': 'Message,ReadReceipt'
}

print(f"\nPayload being sent:")
print(f"  name: {payload['name']}")
print(f"  token: {payload['token'][:10]}...")
print(f"  webhook: {payload['webhook']}")
print(f"  events: {payload['events']}")

print(f"\nPOST to {base_url}/admin/users")

headers = {
    'Content-Type': 'application/json',
    'Authorization': admin_token
}

try:
    resp = requests.post(f"{base_url}/admin/users", json=payload, headers=headers, timeout=10)
    print(f"\nResponse Status: {resp.status_code}")
    print(f"Response Body: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
