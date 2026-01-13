import re

with open('templates/components/sidebar.html', 'r', encoding='utf-8') as f:
    content = f.read()

new_section = '''        <div class="sidebar-section">
            <div class="sidebar-section-title">Captação</div>

            <a href="{% url 'dashboard:landing_config' %}"
                class="sidebar-link {% if 'landing' in request.path %}active{% endif %}">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
                    <line x1="8" y1="21" x2="16" y2="21"></line>
                    <line x1="12" y1="17" x2="12" y2="21"></line>
                </svg>
                <span>Landing Page</span>
            </a>

            <a href="{% url 'dashboard:leads_list' %}"
                class="sidebar-link {% if 'leads' in request.path %}active{% endif %}">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                    <circle cx="9" cy="7" r="4"></circle>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                    <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                </svg>
                <span>Leads</span>
            </a>
        </div>

'''

# Find the closing of Relatórios section and insert before Configurações
pattern = r'(Uso & Custos</span>\s*</a>\s*</div>)(\s*)(<div class="sidebar-section">\s*<div class="sidebar-section-title">Configurações)'

if re.search(pattern, content, re.DOTALL):
    content = re.sub(pattern, r'\1\n\n' + new_section + r'\3', content, flags=re.DOTALL)
    with open('templates/components/sidebar.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Sidebar updated successfully!')
else:
    print('Pattern not found in sidebar.html')

