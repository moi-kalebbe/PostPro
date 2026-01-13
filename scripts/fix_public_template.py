"""
Fix public.html template - Multiple Django syntax issues
"""

template_path = r'templates\landing_page\public.html'

# Read file
with open(template_path, 'r', encoding='utf-8') as f:
    content = f.read()

# The :root CSS section has broken Django template tags
# Fix: Replace the broken CSS variables section with proper inline syntax

old_css_vars = """        :root {
            --primary-color: {
                    {
                    agency.primary_color|default: '#FF6B35'
                }
            }

            ;

            --secondary-color: {
                    {
                    agency.secondary_color|default: '#004E89'
                }
            }

            ;"""

new_css_vars = """        :root {
            --primary-color: {{ agency.primary_color|default:'#FF6B35' }};
            --secondary-color: {{ agency.secondary_color|default:'#004E89' }};"""

content = content.replace(old_css_vars, new_css_vars)

# Fix the broken {% if is_preview %} in CSS
old_preview_css = """        /* Preview Banner */
            {
            % if is_preview %
        }

        .preview-banner {
            background: var(--error);
            color: var(--white);
            padding: 0.5rem;
            text-align: center;
            font-weight: 600;
        }

            {
            % endif %
        }"""

new_preview_css = """        /* Preview Banner */
        .preview-banner {
            background: var(--error);
            color: var(--white);
            padding: 0.5rem;
            text-align: center;
            font-weight: 600;
        }"""

content = content.replace(old_preview_css, new_preview_css)

# Fix the about section with linebreaks filter split across lines
old_about = '''            <div class="about-content">
                {{ landing_page.about_section|linebreaks|default:"Entre em contato para saber mais sobre nossos
                serviços." }}
            </div>'''

new_about = '''            <div class="about-content">
                {{ landing_page.about_section|linebreaks|default:"Entre em contato para saber mais sobre nossos serviços." }}
            </div>'''

content = content.replace(old_about, new_about)

# Fix the hero subtitle if it's also split
old_hero_sub = '''            <p>{{ landing_page.hero_subtitle|default:"Geramos conteúdo otimizado para SEO de forma 100% automática com
                inteligência artificial." }}</p>'''

new_hero_sub = '''            <p>{{ landing_page.hero_subtitle|default:"Geramos conteúdo otimizado para SEO de forma 100% automática com inteligência artificial." }}</p>'''

content = content.replace(old_hero_sub, new_hero_sub)

# Write back
with open(template_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print("✅ Fixed public.html template successfully!")
