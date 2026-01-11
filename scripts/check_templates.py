import os
import re
import sys

# Forçar UTF-8 no stdout para Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass # Python antigo ou ambiente restrito

def check_templates(directory='templates'):
    """
    Varre diretório de templates buscando violações de regras de sintaxe Django.
    """
    print(f"🔍 Iniciando verificação de templates em: {directory}\n")
    
    errors_found = 0
    files_checked = 0
    
    # Regex para operadores sem espaço: captura ==, !=, <=, >=, <, > sem espaço antes ou depois
    # Focamos principalmente no == que é o erro mais comum
    # Procura por {% ... texto==texto ... %}
    # Padrão: {% (qualquer coisa) (caractere não espaço)==(qualquer coisa) %} OU {% (qualquer coisa)==(caractere não espaço) %}
    regex_missing_space_before = re.compile(r'{%.*?[^ ]==.*?%}')
    regex_missing_space_after = re.compile(r'{%.*?==[^ ].*?%}')
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                files_checked += 1
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        
                        for i, line in enumerate(lines):
                            line_num = i + 1
                            
                            # Regra 1: Espaços ao redor de operadores de comparação
                            if regex_missing_space_before.search(line) or regex_missing_space_after.search(line):
                                # Ignorar se for dentro de string (básico) ou comentário
                                if "==" in line and "{%" in line:
                                    print(f"❌ [ERRO SINTAXE] {file_path}:{line_num}")
                                    print(f"   Motivo: Comparação sem espaços (use 'var == value', não 'var==value')")
                                    print(f"   Código: {line.strip()}\n")
                                    errors_found += 1

                            # Regra 2: Tags quebradas incorretamente
                            # Ex: <option {% if ...
                            #        %} ...
                            if "{%" in line and "%}" not in line and "<option" in line:
                                # Verifica se a próxima linha fecha a tag
                                if i + 1 < len(lines):
                                    next_line = lines[i+1]
                                    if "%}" in next_line:
                                         print(f"⚠️ [AVISO SINTAXE] {file_path}:{line_num}")
                                         print(f"   Motivo: Tag Django quebrada em múltiplas linhas dentro de tag HTML (arriscado)")
                                         print(f"   Código: {line.strip()} ... {next_line.strip()}\n")
                                         errors_found += 1

                except Exception as e:
                    print(f"⚠️ Erro ao ler arquivo {file_path}: {e}")

    print("-" * 50)
    print(f"📊 Relatório Final:")
    print(f"   - Arquivos verificados: {files_checked}")
    print(f"   - Problemas encontrados: {errors_found}")
    
    if errors_found > 0:
        print("\n❌ ERROS ENCONTRADOS. Corrija os templates antes de deploy.")
        sys.exit(1)
    else:
        print("\n✅ TUDO OK. Nenhum erro de sintaxe detectado.")
        sys.exit(0)

if __name__ == "__main__":
    check_templates()
