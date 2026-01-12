import re
import os

file_path = r'c:\Users\olx\OneDrive\Desktop\PROJETOS 2026\PostPro\templates\projects\detail.html'

print(f"Reading file: {file_path}")
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to find {% if ... %} tags split across lines
# We look for {% if, then content until newline, then content until %}
# Using greedy match inside but constrained by delimiters? 
# Better: re.sub with a function to process matches

def collapse_match(match):
    full_tag = match.group(0)
    # Remove newlines and extra spaces inside the tag
    cleaned = re.sub(r'\s*\n\s*', ' ', full_tag)
    print(f"Collapsing:\n{full_tag}\nTo:\n{cleaned}\n")
    return cleaned

# Regex: {% if (anything not containing %}) %} where dot matches newlines?
# No, we only want to match tags that ARE split.
# r'{% if .*? %}' with re.DOTALL would match everything.
# We want to match cases where there IS a newline.

pattern = re.compile(r'{% if [^%]*?\n[^%]*?%}', re.DOTALL)
# limit to checks inside the tag to avoid greedy matching across tags?
# {% if ... %} usually doesn't nest {% inside it. So [^%]* is safe-ish, unless string contains %.
# Django tags don't usually contain %.

new_content = pattern.sub(collapse_match, content)

# Also fix the specific known broken line if regex missed specific whitespace
# Line 118 also looks suspicious in the screenshot/file view ("or not rss_settings" split)
# "or not rss_settings %}selected{% endif %}" -> newline before %}

if content != new_content:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Fixed multiline tags.")
else:
    print("No multiline tags found matching pattern.")
