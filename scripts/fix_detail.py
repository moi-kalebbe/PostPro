import os

file_path = r'c:\Users\olx\OneDrive\Desktop\PROJETOS 2026\PostPro\templates\projects\detail.html'

print(f"Reading file: {file_path}")
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = [
    ('rss_settings.check_interval_minutes==30', 'rss_settings.check_interval_minutes == 30'),
    ('rss_settings.check_interval_minutes==60', 'rss_settings.check_interval_minutes == 60'),
    ('rss_settings.check_interval_minutes==120', 'rss_settings.check_interval_minutes == 120'),
    ('rss_settings.check_interval_minutes==360', 'rss_settings.check_interval_minutes == 360'),
    ('rss_settings.max_posts_per_day==3', 'rss_settings.max_posts_per_day == 3'),
    ('rss_settings.max_posts_per_day==5', 'rss_settings.max_posts_per_day == 5'),
    ('rss_settings.max_posts_per_day==10', 'rss_settings.max_posts_per_day == 10'),
    ('rss_settings.max_posts_per_day==20', 'rss_settings.max_posts_per_day == 20'),
]

new_content = content
count = 0
for old, new in replacements:
    if old in new_content:
        new_content = new_content.replace(old, new)
        count += 1
        print(f"Fixed: {old}")

if count > 0:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Successfully fixed {count} issues in detail.html")
else:
    print("No issues found to fix (patterns already match or not found).")
