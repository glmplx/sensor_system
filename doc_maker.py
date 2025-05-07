import os
import re
from datetime import datetime

def find_python_files(directory='.'):
    """Trouve tous les fichiers Python dans le répertoire et ses sous-répertoires."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def extract_functions(filepath):
    """Extrait les informations sur les fonctions d'un fichier Python."""
    functions = []
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()
        
        # Utilisation d'une expression régulière pour trouver les fonctions
        pattern = re.compile(
            r'def\s+(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)\s*\((?P<params>[^)]*)\)\s*:\s*(?P<docstring>""".*?"""|\'\'\'.*?\'\'\')?',
            re.DOTALL
        )
        
        for match in pattern.finditer(content):
            function_name = match.group('name')
            parameters = match.group('params').strip()
            docstring = match.group('docstring') or 'Pas de docstring'
            
            functions.append({
                'name': function_name,
                'params': parameters,
                'docstring': docstring.strip('"\'').strip(),
                'file': os.path.basename(filepath)
            })
    
    return functions

def generate_markdown_documentation(functions_data, output_file='DOCUMENTATION.md'):
    """Génère un fichier Markdown avec la documentation des fonctions."""
    with open(output_file, 'w', encoding='utf-8') as md_file:
        md_file.write(f"# Documentation des fonctions\n\n")
        md_file.write(f"Générée automatiquement le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        current_file = None
        for func in functions_data:
            if func['file'] != current_file:
                md_file.write(f"\n## Fichier: {func['file']}\n\n")
                current_file = func['file']
            
            md_file.write(f"### Fonction: `{func['name']}({func['params']})`\n\n")
            md_file.write(f"**Description:**\n\n")
            md_file.write(f"{func['docstring']}\n\n")
            md_file.write("---\n\n")

def main():
    print("Début de l'analyse des fichiers Python...")
    python_files = find_python_files()
    
    if not python_files:
        print("Aucun fichier Python trouvé.")
        return
    
    print(f"Fichiers Python trouvés ({len(python_files)}):")
    for file in python_files:
        print(f" - {file}")
    
    all_functions = []
    for file in python_files:
        functions = extract_functions(file)
        all_functions.extend(functions)
    
    if not all_functions:
        print("Aucune fonction trouvée.")
        return
    
    print(f"\nFonctions trouvées ({len(all_functions)}):")
    for func in all_functions:
        print(f" - {func['file']}: {func['name']}()")
    
    output_file = 'DOCUMENTATION.md'
    generate_markdown_documentation(all_functions, output_file)
    print(f"\nDocumentation générée dans le fichier: {output_file}")

if __name__ == '__main__':
    main()