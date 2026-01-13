
import os
import sys

# Define the target file path
TARGET_FILE = r'c:\Users\olx\OneDrive\Desktop\PROJETOS 2026\PostPro\templates\landing_page\public_v2.html'

# The clean HTML content with CORRECT Django syntax
# All template tags are strictly single-lined.
html_content = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ landing_page.meta_title|default:agency.get_display_name }}</title>
    <meta name="description" content="{{ landing_page.meta_description }}">
    <link rel="icon" type="image/png" href="{{ agency.get_favicon_url }}">
    
    <!-- Open Graph -->
    <meta property="og:title" content="{{ landing_page.extended_content.og_title|default:landing_page.meta_title|default:agency.get_display_name }}">
    <meta property="og:description" content="{{ landing_page.extended_content.og_description|default:landing_page.meta_description }}">
    <meta property="og:type" content="website">

    <style>
        :root {
            --primary-color: {{ agency.primary_color|default:'#FF6B35' }};
            --secondary-color: {{ agency.secondary_color|default:'#004E89' }};
            --white: #ffffff;
            --gray-50: #f9fafb;
            --gray-100: #f3f4f6;
            --gray-200: #e5e7eb;
            --gray-300: #d1d5db;
            --gray-500: #6b7280;
            --gray-700: #374151;
            --gray-900: #111827;
            --success: #10b981;
            --error: #ef4444;
            --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
            --radius-sm: 0.375rem;
            --radius-md: 0.5rem;
            --radius-lg: 1rem;
        }

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: var(--font-sans); line-height: 1.6; color: var(--gray-700); background: var(--white); }
        .container { max-width: 1200px; margin: 0 auto; padding: 0 1rem; }

        /* Header */
        .header { background: var(--white); padding: 1rem 0; border-bottom: 1px solid var(--gray-200); position: sticky; top: 0; z-index: 100; }
        .header-inner { display: flex; align-items: center; justify-content: space-between; }
        .logo img { max-height: 50px; width: auto; }
        .nav-links { display: flex; gap: 2rem; list-style: none; }
        .nav-links a { color: var(--gray-700); text-decoration: none; font-weight: 500; }
        .nav-links a:hover { color: var(--primary-color); }

        /* Hero */
        .hero { background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%); color: var(--white); padding: 5rem 1rem; text-align: center; }
        .hero h1 { font-size: clamp(2rem, 5vw, 3.5rem); font-weight: 800; margin-bottom: 1.5rem; line-height: 1.2; }
        .hero p { font-size: 1.25rem; max-width: 700px; margin: 0 auto 2rem; opacity: 0.9; }
        
        .cta-btn { display: inline-block; background: var(--white); color: var(--primary-color); padding: 1rem 2.5rem; border-radius: var(--radius-md); font-weight: 700; font-size: 1.125rem; text-decoration: none; transition: transform 0.2s, box-shadow 0.2s; }
        .cta-btn:hover { transform: translateY(-2px); box-shadow: var(--shadow-lg); }

        /* Plans */
        .plans-section { padding: 5rem 1rem; background: var(--gray-50); }
        .section-title { text-align: center; font-size: 2rem; font-weight: 700; margin-bottom: 0.5rem; color: var(--gray-900); }
        .section-subtitle { text-align: center; color: var(--gray-500); margin-bottom: 3rem; }
        .plans-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 2rem; max-width: 1000px; margin: 0 auto; }
        
        .plan-card { background: var(--white); border-radius: var(--radius-lg); padding: 2rem; box-shadow: var(--shadow-md); display: flex; flex-direction: column; position: relative; border: 2px solid transparent; transition: border-color 0.2s; }
        .plan-card:hover { border-color: var(--primary-color); }
        .plan-card.highlighted { border-color: var(--primary-color); }
        .plan-card.highlighted::before { content: 'Recomendado'; position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: var(--primary-color); color: var(--white); padding: 0.25rem 1rem; border-radius: var(--radius-sm); font-size: 0.875rem; font-weight: 600; }
        
        .plan-name { font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem; color: var(--gray-900); }
        .plan-posts { font-size: 2.5rem; font-weight: 800; color: var(--primary-color); }
        .plan-posts span { font-size: 1rem; font-weight: 400; color: var(--gray-500); }
        .plan-price { margin-top: 1rem; color: var(--gray-700); font-size: 1.25rem; }
        .plan-price strong { font-size: 2rem; color: var(--gray-900); }
        
        .plan-features { margin: 1.5rem 0; list-style: none; flex-grow: 1; }
        .plan-features li { padding: 0.5rem 0; display: flex; align-items: center; gap: 0.5rem; }
        .plan-features li::before { content: "✓"; color: var(--success); font-weight: 700; }
        
        .plan-btn { display: block; text-align: center; padding: 0.875rem; background: var(--primary-color); color: var(--white); border-radius: var(--radius-md); text-decoration: none; font-weight: 600; transition: background 0.2s; }
        .plan-btn:hover { background: var(--secondary-color); }

        /* About */
        .about-section { padding: 5rem 1rem; }
        .about-content { max-width: 800px; margin: 0 auto; }
        .about-content p { margin-bottom: 1rem; }

        /* Contact */
        .contact-section { padding: 5rem 1rem; background: var(--gray-900); color: var(--white); }
        .contact-section .section-title { color: var(--white); }
        .contact-section .section-subtitle { color: var(--gray-300); }
        .contact-form { max-width: 500px; margin: 0 auto; }
        
        .form-group { margin-bottom: 1rem; }
        .form-group label { display: block; margin-bottom: 0.5rem; font-weight: 500; }
        .form-group input, .form-group textarea, .form-group select { width: 100%; padding: 0.875rem; border: 1px solid var(--gray-500); border-radius: var(--radius-md); font-size: 1rem; background: var(--gray-700); color: var(--white); }
        .form-group input::placeholder, .form-group textarea::placeholder { color: var(--gray-400); }
        .form-group input:focus, .form-group textarea:focus, .form-group select:focus { outline: none; border-color: var(--primary-color); }
        
        .submit-btn { width: 100%; padding: 1rem; background: var(--primary-color); color: var(--white); border: none; border-radius: var(--radius-md); font-size: 1.125rem; font-weight: 700; cursor: pointer; transition: background 0.2s; }
        .submit-btn:hover { background: var(--secondary-color); }
        .submit-btn:disabled { opacity: 0.7; cursor: not-allowed; }

        /* Footer */
        .footer { background: var(--gray-900); color: var(--gray-400); padding: 2rem 1rem; text-align: center; border-top: 1px solid var(--gray-700); }
        .footer-links { display: flex; justify-content: center; gap: 2rem; margin-bottom: 1rem; }
        .footer-links a { color: var(--gray-400); text-decoration: none; }
        .footer-links a:hover { color: var(--white); }

        /* Success Modal */
        .success-modal { display: none; position: fixed; inset: 0; background: rgba(0, 0, 0, 0.7); align-items: center; justify-content: center; z-index: 1000; }
        .success-modal.show { display: flex; }
        .success-content { background: var(--white); padding: 3rem; border-radius: var(--radius-lg); text-align: center; max-width: 400px; }
        .success-icon { font-size: 4rem; color: var(--success); margin-bottom: 1rem; }
        .success-content h3 { color: var(--gray-900); margin-bottom: 0.5rem; }
        .success-content p { color: var(--gray-600); }
        
        /* Preview Banner */
        .preview-banner { background: var(--error); color: var(--white); padding: 0.5rem; text-align: center; font-weight: 600; }
        
        @media (max-width: 768px) {
            .nav-links { display: none; }
            .hero { padding: 3rem 1rem; }
            .plans-section, .about-section, .contact-section { padding: 3rem 1rem; }
        }

        /* V2 Sections CSS */
        .pain-points-section { padding: 4rem 1rem; background: var(--gray-50); text-align: center; }
        .pain-points-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; max-width: 1000px; margin: 2rem auto 0; }
        .pain-point-card { background: var(--white); padding: 1.5rem; border-radius: var(--radius-md); box-shadow: var(--shadow-sm); border-left: 4px solid var(--error); text-align: left; }
        
        .benefits-section { padding: 5rem 1rem; background: var(--white); }
        .benefits-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; max-width: 1200px; margin: 3rem auto 0; }
        .benefit-card { padding: 2rem; text-align: center; }
        .benefit-icon { font-size: 2.5rem; color: var(--primary-color); margin-bottom: 1rem; display: inline-block; }
        .benefit-title { font-size: 1.25rem; font-weight: 700; margin-bottom: 0.5rem; color: var(--gray-900); }
        
        .social-proof-section { padding: 4rem 1rem; background: var(--gray-900); color: var(--white); text-align: center; }
        
        .faq-section { padding: 5rem 1rem; background: var(--gray-50); }
        .faq-container { max-width: 800px; margin: 0 auto; }
        .faq-item { background: var(--white); border-radius: var(--radius-md); margin-bottom: 1rem; box-shadow: var(--shadow-sm); overflow: hidden; }
        .faq-question { padding: 1.5rem; font-weight: 600; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }
        .faq-question::after { content: "+"; font-size: 1.5rem; color: var(--primary-color); }
        .faq-answer { padding: 0 1.5rem 1.5rem; color: var(--gray-600); display: none; }
        .faq-item.active .faq-answer { display: block; }
        .faq-item.active .faq-question::after { content: "-"; }
        
        .urgency-badge { display: inline-block; background: rgba(255, 255, 255, 0.2); padding: 0.5rem 1rem; border-radius: 50px; font-size: 0.875rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 1.5rem; border: 1px solid rgba(255, 255, 255, 0.4); }
        .scarcity-text { color: var(--error); font-weight: 600; margin-top: 1rem; font-size: 0.9rem; }
    </style>
    
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
</head>

<body>
    {% if is_preview %}
    <div class="preview-banner">🔍 MODO PREVIEW - Esta página não está pública</div>
    {% endif %}

    <!-- Header -->
    <header class="header">
        <div class="container header-inner">
            <a href="#" class="logo"><img src="{{ agency.get_logo_url }}" alt="{{ agency.get_display_name }}"></a>
            <nav>
                <ul class="nav-links">
                    <li><a href="#planos">Planos</a></li>
                    <li><a href="#sobre">Sobre</a></li>
                    <li><a href="#contato">Contato</a></li>
                </ul>
            </nav>
        </div>
    </header>

    <!-- Hero -->
    <section class="hero">
        <div class="container">
            {% if landing_page.extended_content.urgency_badge %}
            <div class="urgency-badge">{{ landing_page.extended_content.urgency_badge }}</div>
            {% endif %}

            <h1>{{ landing_page.hero_title|default:"Transforme seu blog em uma máquina de vendas" }}</h1>
            <p>{{ landing_page.hero_subtitle|default:"Geramos conteúdo otimizado para SEO de forma 100% automática com inteligência artificial." }}</p>

            <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
                <a href="#contato" class="cta-btn">{{ landing_page.cta_text|default:"Começar Agora" }}</a>
                {% if landing_page.extended_content.hero_cta_secondary %}
                <a href="#sobre" class="cta-btn" style="background: transparent; border: 2px solid white; color: white;">{{ landing_page.extended_content.hero_cta_secondary }}</a>
                {% endif %}
            </div>
        </div>
    </section>

    <!-- Pain Points (V2) -->
    {% if landing_page.extended_content.pain_points %}
    <section class="pain-points-section">
        <div class="container">
            <h2 class="section-title" style="font-size: 1.5rem;">Você enfrenta estes problemas?</h2>
            <div class="pain-points-grid">
                {% for point in landing_page.extended_content.pain_points %}
                <div class="pain-point-card"><p>🛑 {{ point }}</p></div>
                {% endfor %}
            </div>
        </div>
    </section>
    {% endif %}

    <!-- Benefits/Solution (V2) -->
    {% if landing_page.extended_content.benefits %}
    <section class="benefits-section">
        <div class="container">
            <h2 class="section-title">{{ landing_page.extended_content.solution_headline|default:"Nossa Solução" }}</h2>
            <div class="benefits-grid">
                {% for benefit in landing_page.extended_content.benefits %}
                <div class="benefit-card">
                    {% if benefit.icon_suggestion %}<div class="benefit-icon">✨</div>{% endif %}
                    <h3 class="benefit-title">{{ benefit.title }}</h3>
                    <p>{{ benefit.description }}</p>
                </div>
                {% endfor %}
            </div>
        </div>
    </section>
    {% endif %}

    <!-- Social Proof (V2) -->
    {% if landing_page.extended_content.social_proof_headline %}
    <section class="social-proof-section">
        <div class="container">
            <h2 class="section-title" style="color: white; margin-bottom: 2rem;">{{ landing_page.extended_content.social_proof_headline }}</h2>
            <p style="font-size: 1.2rem; opacity: 0.9;">{{ landing_page.extended_content.testimonial_prompt }}</p>
        </div>
    </section>
    {% endif %}

    <!-- Plans -->
    <section id="planos" class="plans-section">
        <div class="container">
            <h2 class="section-title">{{ landing_page.extended_content.pricing_headline|default:"Nossos Planos" }}</h2>
            <p class="section-subtitle">{{ landing_page.extended_content.pricing_subheadline|default:"Escolha o plano ideal para o seu negócio" }}</p>

            <div class="plans-grid">
                {% for plan in plans %}
                <div class="plan-card {% if plan.is_highlighted %}highlighted{% endif %}" data-plan-id="{{ plan.id }}">
                    <div class="plan-name">{{ plan.name }}</div>
                    <div class="plan-posts">{{ plan.posts_per_month }} <span>posts/mês</span></div>
                    {% if plan.price %}
                    <div class="plan-price">R$ <strong>{{ plan.price|floatformat:0 }}</strong>/mês</div>
                    {% else %}
                    <div class="plan-price">Sob consulta</div>
                    {% endif %}
                    {% if plan.features %}
                    <ul class="plan-features">
                        {% for feature in plan.get_features_list %}
                        <li>{{ feature }}</li>
                        {% endfor %}
                    </ul>
                    {% endif %}
                    <a href="#contato" class="plan-btn" onclick="selectPlan('{{ plan.id }}', '{{ plan.name }}')">Escolher plano</a>
                </div>
                {% empty %}
                <p style="text-align: center; grid-column: 1/-1;">Entre em contato para conhecer nossos planos.</p>
                {% endfor %}
            </div>
        </div>
    </section>

    <!-- About -->
    <section id="sobre" class="about-section">
        <div class="container">
            <h2 class="section-title">{{ landing_page.extended_content.about_headline|default:"Sobre Nós" }}</h2>
            <div class="about-content">
                {{ landing_page.about_section|linebreaks|default:"Entre em contato para saber mais sobre nossos serviços." }}
            </div>
        </div>
    </section>

    <!-- FAQ (V2) -->
    {% if landing_page.extended_content.faq_items %}
    <section class="faq-section">
        <div class="container">
            <h2 class="section-title">Perguntas Frequentes</h2>
            <div class="faq-container">
                {% for item in landing_page.extended_content.faq_items %}
                <div class="faq-item" onclick="this.classList.toggle('active')">
                    <div class="faq-question">{{ item.question }}</div>
                    <div class="faq-answer">{{ item.answer }}</div>
                </div>
                {% endfor %}
            </div>
        </div>
    </section>
    {% endif %}

    <!-- Contact Form -->
    <section id="contato" class="contact-section">
        <div class="container">
            <h2 class="section-title">{{ landing_page.extended_content.final_cta_headline|default:"Entre em Contato" }}</h2>
            <p class="section-subtitle">{{ landing_page.extended_content.final_cta_subheadline|default:"Preencha o formulário e entraremos em contato" }}</p>

            <form id="lead-form" class="contact-form">
                <input type="hidden" id="selected_plan_id" name="plan_id" value="">
                <input type="hidden" name="utm_source" value="{{ utm_data.utm_source }}">
                <input type="hidden" name="utm_medium" value="{{ utm_data.utm_medium }}">
                <input type="hidden" name="utm_campaign" value="{{ utm_data.utm_campaign }}">

                <div class="form-group"><label for="name">Nome *</label><input type="text" id="name" name="name" required placeholder="Seu nome completo"></div>
                
                <div class="form-group"><label for="email">Email *</label><input type="email" id="email" name="email" required placeholder="seu@email.com"></div>
                
                <div class="form-group"><label for="phone">WhatsApp</label><input type="tel" id="phone" name="phone" placeholder="(11) 99999-9999"></div>
                
                <div class="form-group"><label for="company_name">Site/Empresa</label><input type="text" id="company_name" name="company_name" placeholder="www.seusite.com.br"></div>

                {% if plans %}
                <div class="form-group">
                    <label for="plan_select">Plano de interesse</label>
                    <select id="plan_select" onchange="document.getElementById('selected_plan_id').value = this.value">
                        <option value="">Selecione um plano</option>
                        {% for plan in plans %}
                        <option value="{{ plan.id }}">{{ plan.name }} - {{ plan.posts_per_month }} posts/mês</option>
                        {% endfor %}
                    </select>
                </div>
                {% endif %}

                <div class="form-group"><label for="message">Mensagem</label><textarea id="message" name="message" rows="3" placeholder="Conte mais sobre seu projeto..."></textarea></div>

                <button type="submit" class="submit-btn" id="submit-btn">{{ landing_page.extended_content.final_cta_button|default:"Enviar" }}</button>

                {% if landing_page.extended_content.scarcity_text %}
                <p class="scarcity-text" style="text-align: center;">{{ landing_page.extended_content.scarcity_text }}</p>
                {% endif %}
            </form>
        </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
        <div class="container">
            <div class="footer-links">
                {% if landing_page.whatsapp_number %}<a href="https://wa.me/{{ landing_page.whatsapp_number }}" target="_blank">WhatsApp</a>{% endif %}
                {% if landing_page.email_contact %}<a href="mailto:{{ landing_page.email_contact }}">Email</a>{% endif %}
            </div>
            <p>&copy; {{ "now"|date:"Y" }} {{ agency.get_display_name }}. Todos os direitos reservados.</p>
        </div>
    </footer>

    <!-- Success Modal -->
    <div id="success-modal" class="success-modal">
        <div class="success-content">
            <div class="success-icon">✓</div>
            <h3>Mensagem Enviada!</h3>
            <p>Obrigado pelo contato! Entraremos em contato em breve.</p>
        </div>
    </div>

    <script>
        function selectPlan(planId, planName) {
            document.getElementById('selected_plan_id').value = planId;
            const planSelect = document.getElementById('plan_select');
            if (planSelect) { planSelect.value = planId; }
        }

        document.getElementById('lead-form').addEventListener('submit', async function (e) {
            e.preventDefault();

            const btn = document.getElementById('submit-btn');
            btn.disabled = true;
            btn.textContent = 'Enviando...';

            const formData = new FormData(this);
            const data = Object.fromEntries(formData.entries());

            try {
                const response = await fetch('/p/{{ agency.slug }}/lead/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (result.success) {
                    document.getElementById('success-modal').classList.add('show');
                    this.reset();

                    setTimeout(() => {
                        document.getElementById('success-modal').classList.remove('show');
                    }, 4000);
                } else {
                    alert('Erro: ' + result.error);
                }
            } catch (error) {
                alert('Erro ao enviar. Tente novamente.');
                console.error(error);
            } finally {
                btn.disabled = false;
                btn.textContent = 'Enviar';
            }
        });

        // Close modal on click outside
        document.getElementById('success-modal').addEventListener('click', function (e) {
            if (e.target === this) {
                this.classList.remove('show');
            }
        });
    </script>
</body>
</html>"""

print(f"Writing {len(html_content)} bytes to {TARGET_FILE}...")
with open(TARGET_FILE, 'w', encoding='utf-8', newline='\\n') as f:
    f.write(html_content)

print("Success! File overwritten clean.")
