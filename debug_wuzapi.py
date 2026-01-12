import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from services.wuzapi import WuzapiService
from apps.agencies.models import Agency

print("=== Wuzapi Debug Info ===")
print(f"Settings WUZAPI_ADMIN_TOKEN: '{settings.WUZAPI_ADMIN_TOKEN}'")

try:
    agency = Agency.objects.first()
    if agency:
        print(f"Agency found: {agency.name}")
        print(f"Agency Wuzapi URL: '{agency.wuzapi_instance_url}'")
        print(f"Agency Wuzapi Token: '{agency.wuzapi_token}'")
        
        # Try a direct test request if possible
        print("\nTesting connection to Wuzapi...")
        service = WuzapiService(agency)
        # We manually construct a request to /admin/users to check admin token validity
        # This endpoint requires the admin token
        url = f"{service.base_url}/admin/users"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': settings.WUZAPI_ADMIN_TOKEN
        }
        print(f"Requesting GET {url}")
        print(f"Headers: {headers}")
        
        import requests
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            print(f"Response Status: {resp.status_code}")
            print(f"Response Body: {resp.text[:200]}...")
        except Exception as e:
            print(f"Request failed: {e}")

    else:
        print("No agency found.")

except Exception as e:
    print(f"Error during debug: {e}")
