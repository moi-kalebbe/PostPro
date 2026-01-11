import os
import re

def fix_templates(directory='templates'):
    print(f"🔧 Iniciando correção de templates em: {directory}")
    
    # Regex para adicionar espaço antes de == se não houver
    # Encontra: "{% ... (não espaço)=="
    # Substitui por: "{% ... (não espaço) =="
    # Mas regex replace é chato. Vamos fazer replace de string simples para os casos conhecidos primeiro.
    
    count = 0
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                modified = False
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Correção 1: Espaços em == 
                    # Substitui "=='" por " == '"
                    # Substitui '==' por ' == ' de forma geral se estiver colado
                    
                    new_content = re.sub(r"(?<=[^\s])==(?=[^\s])", " == ", content) # var==val -> var == val
                    new_content = re.sub(r"(?<=[^\s])==(?=\s)", " == ", new_content) # var== val -> var == val
                    new_content = re.sub(r"(?<=\s)==(?=[^\s])", " == ", new_content) # var ==val -> var == val
                    
                    # Especifico para o caso do settings.html que vimos: "=='"
                    new_content = new_content.replace("=='", " == '")
                    new_content = new_content.replace('=="', ' == "')
                    
                    # Correção 2: Juntar tags quebradas (avisos do linter)
                    # Ex: {% if \n ... %} -> {% if ... %}
                    # Isso é complexo com regex simples, mas vamos tentar limpar o caso específico do settings.html
                    # Removendo quebras de linha DENTRO de tags {% ... %}
                    
                    def clean_tag(match):
                        tag_content = match.group(0)
                        if '\n' in tag_content:
                            return re.sub(r'\s+', ' ', tag_content) # Normaliza espaços
                        return tag_content

                    new_content = re.sub(r'{%.*?%}', clean_tag, new_content, flags=re.DOTALL)

                    if new_content != content:
                        print(f"✏️ Corrigindo: {file_path}")
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        count += 1
                        
                except Exception as e:
                    print(f"❌ Erro em {file_path}: {e}")

    print(f"✅ Concluído. {count} arquivos corrigidos.")

if __name__ == "__main__":
    fix_templates()
