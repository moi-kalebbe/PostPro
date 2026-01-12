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

print(f"Base URL: {base_url}")
print(f"Admin Token: {admin_token}")

headers = {
    'Content-Type': 'application/json',
    'Authorization': admin_token
}

print(f"\nGET {base_url}/admin/users")
resp = requests.get(f"{base_url}/admin/users", headers=headers, timeout=10)
print(f"Status: {resp.status_code}")
print(f"Raw Response Text:")
print(resp.text)
