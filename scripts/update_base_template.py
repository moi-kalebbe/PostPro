#!/usr/bin/env python3
"""
Script para adicionar os scripts toast.js e confirm-modal.js ao base.html
Garante encoding UTF-8 e sintaxe Django correta
"""

def update_base_template():
    file_path = r'c:\Users\olx\OneDrive\Desktop\PROJETOS 2026\PostPro\templates\base.html'
    
    # Ler arquivo com encoding UTF-8
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar se os scripts já foram adicionados
    if 'toast.js' in content:
        print('✅ Scripts já foram adicionados ao base.html')
        return
    
    # Encontrar a linha do main.js
    old_script = '    <script src="{% load static %}{% static \'js/main.js\' %}"></script>'
    
    # Novo conteúdo com os 3 scripts
    new_scripts = '''    <!-- Core Scripts -->
    <script src="{% load static %}{% static 'js/main.js' %}"></script>
    <script src="{% load static %}{% static 'js/toast.js' %}"></script>
    <script src="{% load static %}{% static 'js/confirm-modal.js' %}"></script>'''
    
    # Substituir
    if old_script in content:
        content = content.replace(old_script, new_scripts)
        
        # Salvar com encoding UTF-8
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print('✅ Scripts adicionados com sucesso ao base.html!')
        print('   - toast.js')
        print('   - confirm-modal.js')
    else:
        print('❌ Não foi possível encontrar a linha do main.js')
        print('   Verifique manualmente o arquivo base.html')

if __name__ == '__main__':
    update_base_template()
