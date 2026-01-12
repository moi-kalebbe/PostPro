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

db_token = agency.wuzapi_token
wuzapi_token = None

for user in users:
    if user.get('name') == agency_user_name:
        wuzapi_token = user.get('token')
        break

print(f"DB Token:     '{db_token}'")
print(f"Wuzapi Token: '{wuzapi_token}'")
print(f"Match: {db_token == wuzapi_token}")
