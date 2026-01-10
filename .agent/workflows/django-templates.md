---
description: Regras críticas para templates Django neste projeto
---

# Django Template Syntax Rules - PostPro

## ⚠️ REGRA CRÍTICA: Espaços em Operadores

No Django 5.x, **SEMPRE adicione espaços** ao redor de operadores de comparação em template tags:

### ❌ ERRADO (causa TemplateSyntaxError):
```django
{% if project_filter==project.id %}
{% if status_filter==value %}
{% if post.status=='published' %}
```

### ✅ CORRETO:
```django
{% if project_filter == project.id %}
{% if status_filter == value %}
{% if post.status == 'published' %}
```

## Outros cuidados:

1. **Filtros com comparação**: Use `|stringformat:'s'` para converter UUIDs para string
   ```django
   {% if project_filter == project.id|stringformat:'s' %}
   ```

⚠️ **REGRA CRÍTICA: Tags Multi-linha**
    **NUNCA quebre a tag de fechamento em nova linha separada do conteúdo da tag anterior se não houver fechamento de bloco explícito.**
    
    ### ❌ ERRADO (Gera `Invalid block tag ... expected 'endif'`):
    ```django
    <option value="..." {% if condition %}selected{%
    endif %}>Opção</option>
    ```

    ### ✅ CORRETO:
    ```django
    <option value="..." {% if condition %}selected{% endif %}>Opção</option>
    ```

3. **Operadores suportados**: `==`, `!=`, `<`, `>`, `<=`, `>=`, `and`, `or`, `not`, `in`, `not in`

## Checklist antes de editar templates:
- [ ] Verificar espaços ao redor de `==` e outros operadores
- [ ] Validar sintaxe localmente antes de testar no browser
- [ ] Não confundir syntax JavaScript com Django template tags

## Comando de Verificação (Grep)
Para evitar este erro recorrente, execute este comando antes de finalizar:
```bash
grep -r "{% if .*[^ ]==.* %}" templates/
grep -r "{% if .*==[^ ].* %}" templates/
```
Se encontrar resultados, ADICIONE ESPAÇOS.

---

## 🔧 Como Corrigir Templates Corrompidos

### Problema: Ferramentas de edição (VS Code, PowerShell) corrompem a sintaxe

**Sintomas:**
- `TemplateSyntaxError: Invalid block tag on line X: 'endif', expected 'endblock'`
- `TemplateSyntaxError: Could not parse the remainder: '==value' from 'form.field.value==value'`
- Caracteres estranhos no lugar de acentos (problema de encoding)

### ✅ Solução: Usar script Python para reescrever o arquivo

O método mais seguro é criar um script Python que escreva o template corretamente:

```python
# scripts/fix_template.py
content = '''{% extends 'base.html' %}
{% load static %}

{% block content %}
<select name="field" class="form-select">
    {% for value, label in form.fields.field.choices %}
    <option value="{{ value }}"{% if form.field.value == value %} selected{% endif %}>{{ label }}</option>
    {% endfor %}
</select>
{% endblock %}
'''

with open('templates/path/to/template.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('OK')
```

Depois execute:
```bash
python scripts/fix_template.py
```

### ⚠️ NUNCA usar PowerShell para editar templates Django

O PowerShell pode:
- Quebrar encoding UTF-8
- Adicionar BOM indesejado
- Corromper caracteres especiais

### Padrão correto para `<option>` com selected:

```django
<option value="{{ value }}"{% if form.field.value == value %} selected{% endif %}>{{ label }}</option>
```

**Regras:**
1. SEM espaço entre `"{{ value }}"` e `{% if`
2. COM espaço ao redor de `==`
3. TUDO em uma única linha
4. Espaço antes de `selected`

### Padrão correto para checkbox com checked:

```django
<input type="checkbox" name="field" class="checkbox"{% if form.field.value %} checked{% endif %}>
```

---

## Scripts de correção disponíveis

Este projeto possui scripts prontos para corrigir templates:

- `scripts/fix_settings.py` - Regenera `templates/dashboard/settings.html`
- `scripts/fix_form.py` - Regenera `templates/projects/form.html`

Para usar: `python scripts/fix_settings.py`
