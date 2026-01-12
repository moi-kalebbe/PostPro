---
description: Regras críticas para templates Django neste projeto
---

# Django Template Syntax Rules - PostPro

> [!CAUTION]
> **REGRA DE OURO**: A sintaxe do Django Template Language (DTL) é sensível a espaços em algumas versões e configurações. Siga estas regras estritamente para evitar falhas em produção.

## 1. Operadores de Comparação (CRÍTICO)

No Django, você **DEVE** adicionar espaços ao redor de operadores de comparação (`==`, `!=`, `<`, `>`, `<=`, `>=`). A falta de espaço causa o erro `TemplateSyntaxError: Could not parse the remainder`.

### ❌ JAMAIS FAÇA ISSO:
```django
{% if settings.value==30 %}          <!-- ERRO: Sem espaço -->
{% if post.status=='published' %}    <!-- ERRO: Sem espaço -->
{% if count>=10 %}                   <!-- ERRO: Sem espaço -->
```

### ✅ SEMPRE FAÇA ISSO:
```django
{% if settings.value == 30 %}        <!-- CORRETO -->
{% if post.status == 'published' %}  <!-- CORRETO -->
{% if count >= 10 %}                 <!-- CORRETO -->
```

---

## 2. Tags Multi-linha (CRÍTICO)

Não quebre a tag de fechamento `endif` ou `endblock` em uma linha isolada se ela fizer parte de uma tag HTML aberta, a menos que você saiba exatamente o que está fazendo. Editores automáticos e formatadores podem quebrar isso incorretamente.

### ❌ ERRADO:
```django
<option value="1" {% if value == 1 %}selected{%
endif %}>Opção</option>
```
Isso gera `Invalid block tag ... expected 'endif'`.

### ✅ CORRETO:
Mantenha a lógica condicional simples em uma linha quando possível:
```django
<option value="1" {% if value == 1 %}selected{% endif %}>Opção</option>
```

---

## 3. Comandos de Verificação

Se você suspeitar de erros de sintaxe, use estes comandos (PowerShell) para varrer os templates:

```powershell
# Encontrar falta de espaço antes de ==
Get-ChildItem -Recurse -Filter *.html | Select-String -Pattern "{% if .*[^ ]==.* %}"

# Encontrar falta de espaço depois de ==
Get-ChildItem -Recurse -Filter *.html | Select-String -Pattern "{% if .*==[^ ].* %}"
```

Se encontrar, corrija imediatamente.

---

## 4. Scripts de Correção Automática

Se um arquivo estiver muito corrompido, prefira reescrevê-lo via script Python para garantir encoding correto (UTF-8) e sintaxe limpa, em vez de tentar editar manualmente se o seu editor estiver configurado incorretamente.

Exemplo de script de correção:
```python
# scripts/fix_broken_template.py
with open('templates/caminho/arquivo.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends 'base.html' %}
<!-- Cole o conteúdo correto aqui -->
{% if value == 10 %}...{% endif %}
''')
```
