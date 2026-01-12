import sys
import os
import django

# Add parent directory to path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.projects.models import ProjectRSSSettings, RSSFeed

def migrate_rss_v2():
    print("Starting RSS V2 Data Migration...")
    
    # Find settings with legacy feed_url
    settings_list = ProjectRSSSettings.objects.exclude(feed_url__isnull=True).exclude(feed_url='')
    
    migrated_count = 0
    skipped_count = 0
    
    for settings in settings_list:
        try:
            # Check for duplicates
            if RSSFeed.objects.filter(project=settings.project, feed_url=settings.feed_url).exists():
                print(f"[SKIP] Feed already exists for {settings.project.name}: {settings.feed_url[:30]}...")
                skipped_count += 1
                continue

            RSSFeed.objects.create(
                project=settings.project,
                feed_url=settings.feed_url,
                is_active=settings.is_active,
                last_checked_at=settings.last_checked_at,
                name=f"Feed Principal ({settings.project.name})"
            )
            print(f"[OK] Migrated feed for {settings.project.name}")
            migrated_count += 1
            
        except Exception as e:
            print(f"[ERROR] Failed to migrate {settings.project.name}: {e}")

    print(f"\nMigration Complete!")
    print(f"Migrated: {migrated_count}")
    print(f"Skipped: {skipped_count}")

if __name__ == '__main__':
    migrate_rss_v2()
