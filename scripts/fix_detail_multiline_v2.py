import re
import os

file_path = r'c:\Users\olx\OneDrive\Desktop\PROJETOS 2026\PostPro\templates\projects\detail.html'

print(f"Reading file: {file_path}")
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

def collapse_match(match):
    full_tag = match.group(0)
    cleaned = re.sub(r'\s*\n\s*', ' ', full_tag)
    print(f"Collapsing:\n{full_tag}\nTo:\n{cleaned}\n")
    return cleaned

# Match any Django block tag {% ... %} that contains a newline
# We ensure we don't cross a closing delimiter by excluding % from the inner match, 
# or by being non-greedy and careful. 
# Django tags don't usually contain nested %}.
pattern = re.compile(r'{%[^%]*?\n[^%]*?%}', re.DOTALL)

new_content = pattern.sub(collapse_match, content)

if content != new_content:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Fixed multiline tags.")
else:
    print("No multiline tags found matching pattern.")
