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
