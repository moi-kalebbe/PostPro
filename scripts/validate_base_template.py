#!/usr/bin/env python3
"""
Script para validar a sintaxe Django do base.html
"""
import os
import sys
import django

# Configurar o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.template import Template

def validate_template():
    file_path = r'templates\base.html'
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Tentar compilar o template
        Template(content)
        
        print('✅ Sintaxe Django válida no base.html!')
        return True
    except Exception as e:
        print(f'❌ Erro de sintaxe Django: {e}')
        return False

if __name__ == '__main__':
    success = validate_template()
    sys.exit(0 if success else 1)
