"""
Fix config.html template - Django template syntax issues
Combines multi-line {% if %} tags into single lines
"""

import re

template_path = r'templates\agencies\landing\config.html'

with open(template_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix pattern: {% if\n   something %} -> {% if something %}
# This regex finds cases where {% if is followed by newline and spaces, then the condition

# Pattern 1: {% if\n whitespace variable %} -> single line
content = re.sub(
    r'\{% if\s+\n\s+(\S+)\s+%\}',
    r'{% if \1 %}',
    content
)

# Pattern 2: More specific - checkbox line
content = re.sub(
    r'class="form-checkbox"\s*\{% if\s*\n\s*landing_page\.is_published\s*%\}checked\{% endif %\}',
    r'class="form-checkbox" {% if landing_page.is_published %}checked{% endif %}',
    content
)

# Pattern 3: Fix any label split across lines  
content = re.sub(
    r'Publicar landing\s*\n\s*page',
    r'Publicar landing page',
    content
)

# Write back
with open(template_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print("✅ Fixed config.html template successfully!")
