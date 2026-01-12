import os
import django
import requests
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.agencies.models import Agency

agency = Agency.objects.first()
base_url = agency.wuzapi_instance_url.rstrip('/')
token = agency.wuzapi_token

print(f"Base URL: {base_url}")
print(f"Token: {token[:20]}..." if token else "Token: EMPTY!")

# Use 'Token' header as per Wuzapi docs
headers = {
    'Content-Type': 'application/json',
    'Token': token  # Changed from 'Authorization' to 'Token'
}

# Step 1: Check status
print("\n=== Step 1: Check Status ===")
resp = requests.get(f"{base_url}/session/status", headers=headers, timeout=10)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text[:500]}")

# Step 2: Connect
print("\n=== Step 2: Connect ===")
resp = requests.post(f"{base_url}/session/connect", 
    json={'Subscribe': ['Message'], 'Immediate': False},
    headers=headers, timeout=30)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text[:500]}")

# Step 3: Get QR Code
print("\n=== Step 3: Get QR Code ===")
resp = requests.get(f"{base_url}/session/qr", headers=headers, timeout=10)
print(f"Status: {resp.status_code}")
# Only print first 200 chars to avoid huge base64 dump
print(f"Response: {resp.text[:200]}...")
