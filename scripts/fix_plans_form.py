#!/usr/bin/env python
"""Script to fix the plans form template."""

TEMPLATE_CONTENT = '''{% extends 'base.html' %}
{% load static %}

{% block title %}{% if edit_mode %}Editar{% else %}Novo{% endif %} Plano - {{ request.user.agency.name }}{% endblock %}

{% block sidebar %}
{% include 'components/sidebar.html' %}
{% endblock %}

{% block content %}
<div class="container">
    <div class="page-header">
        <h1 class="page-title">{% if edit_mode %}Editar Plano{% else %}Novo Plano{% endif %}</h1>
        <a href="{% url 'dashboard:plans_list' %}" class="btn btn-ghost">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" stroke-width="2">
                <line x1="19" y1="12" x2="5" y2="12"></line>
                <polyline points="12 19 5 12 12 5"></polyline>
            </svg>
            Voltar
        </a>
    </div>

    <div class="card">
        <div class="card-body">
            <form method="post">
                {% csrf_token %}

                <div class="grid grid-cols-2 gap-4 mb-4">
                    <div class="form-group">
                        <label for="name" class="form-label">Nome do Plano *</label>
                        <input type="text" id="name" name="name" class="form-input" placeholder="Ex: Bronze, Prata, Ouro" value="{% if edit_mode %}{{ plan.name }}{% elif form_data %}{{ form_data.name }}{% endif %}" required>
                    </div>
                    <div class="form-group">
                        <label for="posts_per_month" class="form-label">Posts por Mês *</label>
                        <input type="number" id="posts_per_month" name="posts_per_month" class="form-input" min="1" max="10000" value="{% if edit_mode %}{{ plan.posts_per_month }}{% elif form_data %}{{ form_data.posts_per_month }}{% else %}30{% endif %}" required>
                        <span class="form-hint">Limite mensal de posts para projetos deste plano</span>
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-4 mb-4">
                    <div class="form-group">
                        <label for="price" class="form-label">Preço Mensal (R$)</label>
                        <input type="text" id="price" name="price" class="form-input" placeholder="Ex: 199,90 (opcional)" value="{% if edit_mode and plan.price %}{{ plan.price }}{% elif form_data %}{{ form_data.price }}{% endif %}">
                        <span class="form-hint">Exibido na landing page (opcional)</span>
                    </div>
                    <div class="form-group">
                        <label for="order" class="form-label">Ordem de Exibição</label>
                        <input type="number" id="order" name="order" class="form-input" min="0" value="{% if edit_mode %}{{ plan.order }}{% elif form_data %}{{ form_data.order }}{% else %}0{% endif %}">
                        <span class="form-hint">Menor número = aparece primeiro</span>
                    </div>
                </div>

                <div class="form-group mb-4">
                    <label for="description" class="form-label">Descrição</label>
                    <textarea id="description" name="description" class="form-input" rows="2" placeholder="Breve descrição do plano">{% if edit_mode %}{{ plan.description }}{% elif form_data %}{{ form_data.description }}{% endif %}</textarea>
                </div>

                <div class="form-group mb-4">
                    <label for="features" class="form-label">Features (uma por linha)</label>
                    <textarea id="features" name="features" class="form-input" rows="5" placeholder="Suporte prioritário">{% if edit_mode %}{{ features_text }}{% elif form_data %}{{ form_data.features }}{% endif %}</textarea>
                    <span class="form-hint">Lista de benefícios exibidos na landing page</span>
                </div>

                <div class="form-group mb-6">
                    <label class="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" name="is_highlighted" class="form-checkbox" {% if edit_mode and plan.is_highlighted %}checked{% endif %}>
                        <span>Destacar como plano recomendado</span>
                    </label>
                    <span class="form-hint">Este plano terá destaque visual na landing page</span>
                </div>

                <div class="flex gap-4">
                    <button type="submit" class="btn btn-primary">{% if edit_mode %}Salvar Alterações{% else %}Criar Plano{% endif %}</button>
                    <a href="{% url 'dashboard:plans_list' %}" class="btn btn-ghost">Cancelar</a>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
'''

if __name__ == '__main__':
    with open('templates/agencies/plans/form.html', 'w', encoding='utf-8') as f:
        f.write(TEMPLATE_CONTENT)
    print('Template corrigido com sucesso!')
