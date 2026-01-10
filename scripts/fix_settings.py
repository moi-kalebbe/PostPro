content = '''{% extends 'base.html' %}
{% load static %}

{% block title %}Configuracoes - PostPro{% endblock %}

{% block sidebar %}
{% include 'components/sidebar.html' %}
{% endblock %}

{% block content %}
<div class="container">
    <div class="page-header">
        <h1 class="page-title">Configuracoes</h1>
    </div>

    <div class="grid-responsive-2">
        <div class="card">
            <div class="card-header">
                <h3 class="card-title">OpenRouter API Key</h3>
            </div>
            <div class="card-body">
                <form method="post">
                    {% csrf_token %}
                    <input type="hidden" name="action" value="update_api_key">
                    <div class="form-group">
                        <label class="form-label">API Key</label>
                        <input type="password" name="openrouter_api_key" class="form-input" placeholder="{% if has_api_key %}************{% else %}sk-or-v1-...{% endif %}">
                        <span class="form-help">{% if has_api_key %}API key configurada.{% else %}Obtenha em openrouter.ai{% endif %}</span>
                    </div>
                    <div class="flex gap-3">
                        <button type="submit" class="btn btn-primary">Salvar</button>
                        <button type="submit" name="action" value="test_api_key" class="btn btn-secondary">Testar</button>
                    </div>
                </form>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <h3 class="card-title">Modelos Padrao da Agencia</h3>
            </div>
            <div class="card-body">
                <p style="font-size: 13px; color: #6b7280; margin-bottom: 16px;">Usados quando o projeto nao especifica modelo proprio.</p>
                <form method="post">
                    {% csrf_token %}
                    <input type="hidden" name="action" value="update_models">
                    <div class="form-group">
                        <label class="form-label">Modelo de Texto</label>
                        <select name="default_text_model" class="form-select">
                            <option value="deepseek/deepseek-v3"{% if agency.default_text_model == 'deepseek/deepseek-v3' %} selected{% endif %}>DeepSeek V3 (Economico)</option>
                            <option value="openai/gpt-4o-mini"{% if agency.default_text_model == 'openai/gpt-4o-mini' %} selected{% endif %}>GPT-4o Mini</option>
                            <option value="anthropic/claude-3-haiku"{% if agency.default_text_model == 'anthropic/claude-3-haiku' %} selected{% endif %}>Claude 3 Haiku</option>
                            <option value="anthropic/claude-3.5-sonnet"{% if agency.default_text_model == 'anthropic/claude-3.5-sonnet' %} selected{% endif %}>Claude 3.5 Sonnet</option>
                            <option value="anthropic/claude-sonnet-4"{% if agency.default_text_model == 'anthropic/claude-sonnet-4' %} selected{% endif %}>Claude Sonnet 4 (Premium)</option>
                            <option value="openai/gpt-4o"{% if agency.default_text_model == 'openai/gpt-4o' %} selected{% endif %}>GPT-4o</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Modelo de Imagem</label>
                        <select name="default_image_model" class="form-select">
                            <option value="pollinations/turbo"{% if agency.default_image_model == 'pollinations/turbo' %} selected{% endif %}>Turbo - Rapido (Pollinations)</option>
                            <option value="pollinations/flux"{% if agency.default_image_model == 'pollinations/flux' %} selected{% endif %}>Flux - Alta qualidade (Pollinations)</option>
                            <option value="pollinations/gptimage"{% if agency.default_image_model == 'pollinations/gptimage' %} selected{% endif %}>GPTImage (Pollinations)</option>
                            <option value="pollinations/gptimage-large"{% if agency.default_image_model == 'pollinations/gptimage-large' %} selected{% endif %}>GPTImage Large - Premium</option>
                            <option value="openai/dall-e-3"{% if agency.default_image_model == 'openai/dall-e-3' %} selected{% endif %}>DALL-E 3 (OpenAI - Premium)</option>
                        </select>
                        <span class="form-help" style="font-size: 12px; color: #6b7280;">Pollinations = gratuito/barato. OpenAI = premium.</span>
                    </div>
                    <button type="submit" class="btn btn-primary">Salvar</button>
                </form>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <h3 class="card-title">Seu Plano</h3>
            </div>
            <div class="card-body">
                <div class="flex items-center justify-between mb-4">
                    <span class="text-lg font-semibold">{{ agency.get_plan_display }}</span>
                    {% if agency.subscription_status == 'active' %}
                    <span class="badge badge-success">{{ agency.get_subscription_status_display }}</span>
                    {% else %}
                    <span class="badge badge-warning">{{ agency.get_subscription_status_display }}</span>
                    {% endif %}
                </div>
                <div class="mb-4">
                    <div class="flex justify-between text-sm mb-2">
                        <span>Posts este mes</span>
                        <span>{{ agency.current_month_posts }} / {{ agency.monthly_posts_limit }}</span>
                    </div>
                    <div class="progress">
                        <div class="progress-bar" style="width: {% widthratio agency.current_month_posts agency.monthly_posts_limit 100 %}%"></div>
                    </div>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <h3 class="card-title">Equipe</h3>
            </div>
            <div class="card-body">
                <table class="table">
                    <thead>
                        <tr>
                            <th>Membro</th>
                            <th>Role</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for member in team_members %}
                        <tr>
                            <td><strong>{{ member.first_name }} {{ member.last_name }}</strong></td>
                            <td><span class="badge badge-gray">{{ member.get_role_display }}</span></td>
                        </tr>
                        {% empty %}
                        <tr>
                            <td colspan="2" class="text-center text-muted">Nenhum membro</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
{% endblock %}
'''

with open('templates/dashboard/settings.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('OK - settings.html fixed')
