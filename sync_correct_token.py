import os
import django
import requests
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.agencies.models import Agency

agency = Agency.objects.first()
base_url = agency.wuzapi_instance_url.rstrip('/')
admin_token = settings.WUZAPI_ADMIN_TOKEN

headers = {
    'Content-Type': 'application/json',
    'Authorization': admin_token
}

# Get all users from admin API
resp = requests.get(f"{base_url}/admin/users", headers=headers, timeout=10)
data = resp.json()
users = data.get('data', [])

agency_user_name = f'agency_{agency.id}'

for user in users:
    if user.get('name') == agency_user_name:
        correct_token = user.get('token')
        user_id = user.get('id')
        print(f"Found user: {user.get('name')}")
        print(f"User ID: {user_id}")
        print(f"Correct Token: {correct_token[:30]}...")
        
        agency.wuzapi_user_id = user_id
        agency.wuzapi_token = correct_token
        agency.save(update_fields=['wuzapi_user_id', 'wuzapi_token'])
        print("SAVED!")
        exit(0)

print(f"User {agency_user_name} not found!")
print(f"Available users: {[u.get('name') for u in users]}")
