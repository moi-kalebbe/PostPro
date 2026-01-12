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

resp = requests.get(f"{base_url}/admin/users", headers=headers, timeout=10)
data = resp.json()
users = data.get('data', [])

agency_user_name = f'agency_{agency.id}'

for user in users:
    if user.get('name') == agency_user_name:
        agency.wuzapi_user_id = user.get('id')
        agency.wuzapi_token = user.get('token')
        agency.save(update_fields=['wuzapi_user_id', 'wuzapi_token'])
        print("SAVED OK")
        exit(0)

print("NOT FOUND")
