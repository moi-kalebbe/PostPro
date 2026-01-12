import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.projects.models import Project
from apps.authentication.models import Agency

def create_projects():
    # Get the first agency (assuming one exists, or created by default admin)
    agency = Agency.objects.first()
    if not agency:
        print("No Agency found. Please create an agency or superuser first.")
        return

    projects_data = [
        {
            "name": "Tech Innovation Daily",
            "wordpress_url": "https://tech-innovation-daily.com",
            "wordpress_app_password": "app-password-123",
            "wordpress_username": "admin"
        },
        {
            "name": "Organic Health Tips",
            "wordpress_url": "https://organic-health-tips.net",
            "wordpress_app_password": "app-password-456",
            "wordpress_username": "editor"
        },
        {
            "name": "Crypto Market Watch",
            "wordpress_url": "https://crypto-market-watch.org",
            "wordpress_app_password": "app-password-789",
            "wordpress_username": "trader"
        },
        {
            "name": "Global Travel Guide",
            "wordpress_url": "https://globaltravelguide.com",
            "wordpress_app_password": "app-password-000",
            "wordpress_username": "traveler"
        }
    ]

    created_count = 0
    for data in projects_data:
        project, created = Project.objects.get_or_create(
            name=data["name"],
            agency=agency,
            defaults={
                "wordpress_url": data["wordpress_url"],
                "wordpress_app_password": data["wordpress_app_password"],
                "wordpress_username": data["wordpress_username"],
                "status": "active"
            }
        )
        if created:
            print(f"Created project: {project.name}")
            created_count += 1
        else:
            print(f"Project already exists: {project.name}")

    print(f"\nSuccessfully created {created_count} new projects.")

if __name__ == "__main__":
    create_projects()
