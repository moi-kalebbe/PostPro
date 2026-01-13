import re

FILE_PATH = r'c:\Users\olx\OneDrive\Desktop\PROJETOS 2026\PostPro\templates\admin_panel\superadmin_whatsapp.html'

def validate_file():
    try:
        with open(FILE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
            
        errors = []
        
        # Check basic balancing
        if content.count('{') != content.count('}'):
            # This is common in templates due to django tags, but let's check javascript blocks
            # Naive check for script block
            script_content = re.search(r'<script>(.*?)</script>', content, re.DOTALL)
            if script_content:
                js = script_content.group(1)
                if js.count('{') != js.count('}'):
                    errors.append("Desbalanço de chaves {} no bloco JavaScript")
                if js.count('(') != js.count(')'):
                    errors.append("Desbalanço de parênteses () no bloco JavaScript")
        
        # Check for banned keywords
        if 'alert(' in content:
            errors.append("Ainda existem chamadas para alert() no arquivo")
        if 'confirm(' in content:
            errors.append("Ainda existem chamadas para confirm() no arquivo")
            
        if errors:
            print("❌ Erros encontrados:")
            for e in errors:
                print(f"- {e}")
            return False
            
        print("✅ Validação básica concluída. Nenhum alert/confirm nativo encontrado.")
        return True
        
    except Exception as e:
        print(f"Erro ao ler arquivo: {e}")
        return False

if __name__ == "__main__":
    validate_file()
