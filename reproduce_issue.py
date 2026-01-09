
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.projects.models import Project
from apps.agencies.models import Agency
from apps.accounts.models import User

# Check ENCRYPTION_KEY
print(f"ENCRYPTION_KEY from settings: '{settings.ENCRYPTION_KEY}'")
print(f"Type of ENCRYPTION_KEY: {type(settings.ENCRYPTION_KEY)}")

try:
    from cryptography.fernet import Fernet

    # Test the key from docker-stack.yml (Corrected)
    stack_key = "6EeY6lQX3tDtH64kPw9zNmB2xR5vK8jL0qS1uT4yWaE="
    try:
        print(f"Testing docker-stack key: {stack_key}")
        Fernet(stack_key.encode())
        print("Docker stack key is VALID.")
    except Exception as e:
        print(f"Docker stack key is INVALID: {e}")

    if settings.ENCRYPTION_KEY:
        print("Validating ENCRYPTION_KEY from settings...")
        try:
            f = Fernet(settings.ENCRYPTION_KEY.encode())
            print("Fernet initialized successfully with provided key.")
        except Exception as e:
            print(f"CRITICAL: Fernet initialization failed with provided key: {e}")
    else:
        print("ENCRYPTION_KEY is empty. Project model will generate random keys on the fly (This causes data loss but not immediate crash usually).")

except ImportError:
    print("cryptography not installed?")

print("Attempting to simulate project creation...")

try:
    # We won't save to DB to avoid messing up data, just mimic the flow
    # actually we need to save to test DB constraints, but let's try to just instantiate and set password first
    
    print("Attempting to fetch agency...")
    agency = Agency.objects.first()
    if not agency:
        print("No agency found! Creating one...")
        # Create dummy user and agency if needed, or just fail
        # For reproduction, we assume data exists. If not, that's another issue.
        # But let's try to be robust
        u = User.objects.create(email='test@example.com', username='testuser')
        agency = Agency.objects.create(owner=u, name='Test Agency')

    print(f"Using agency: {agency}")
    
    p = Project()
    p.name = "Test Project Saved"
    p.agency = agency
    
    print("Setting password...")
    p.set_wordpress_password("testpassword123")
    
    print("Saving project...")
    p.save()
    print("Project saved successfully!")
    
    # cleanup
    p.delete()
    print("Cleanup done.")

except Exception as e:
    print(f"CRITICAL: Crash during simulation: {e}")
    import traceback
    traceback.print_exc()
