
import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.automation.models import BatchJob

def diagnose():
    print("--- Diagnosing Latest Batch Jobs ---")
    
    # Get last 5 failed jobs
    jobs = BatchJob.objects.filter(status='failed').order_by('-created_at')[:5]
    
    if not jobs.exists():
        print("No failed jobs found.")
        return

    for job in jobs:
        print(f"\nJob ID: {job.id}")
        print(f"File: {job.original_filename}")
        print(f"Created At: {job.created_at}")
        print(f"Status: {job.status}")
        print(f"Error Log: {job.error_log}")
        
        # Check if error matches old or new logic
        if job.error_log:
            err = str(job.error_log)
            if "csv.Sniffer" in err:  # Unlikely to appear in error log, but checking context
                print("-> Hints at NEW code usage (if traceback included)")
            elif "utf-8" in err and "decode" in err:
                print("-> Possible encoding issue (OLD code characteristic)")
            else:
                print("-> parsing error")

if __name__ == "__main__":
    diagnose()
