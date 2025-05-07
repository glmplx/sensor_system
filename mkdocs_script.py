import os
import re
from datetime import datetime
import yaml

def find_python_files(directory='.'):
    """Trouve tous les fichiers Python dans le répertoire et ses sous-répertoires."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Ignorer les dossiers spéciaux
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('venv', 'env', 'docs')]
        
        for file in files:
            if file.endswith('.py') and not file.startswith('_'):
                full_path = os.path.join(root, file)
                python_files.append(full_path)
    return python_files

def extract_functions(filepath):
    """Extrait les informations sur les fonctions d'un fichier Python."""
    functions = []
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()
        
        # Pattern pour détecter les fonctions avec leurs docstrings
        pattern = re.compile(
            r'def\s+(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)\s*\((?P<params>[^)]*)\)\s*:\s*(?P<docstring>""".*?"""|\'\'\'.*?\'\'\')?',
            re.DOTALL
        )
        
        for match in pattern.finditer(content):
            function_name = match.group('name')
            parameters = match.group('params').strip()
            docstring = match.group('docstring') or 'Pas de docstring'
            
            # Nettoyer la docstring
            docstring = docstring.strip('"\'').strip()
            docstring = re.sub(r'^\s*', '', docstring, flags=re.MULTILINE)
            
            functions.append({
                'name': function_name,
                'params': parameters,
                'docstring': docstring,
                'file': os.path.basename(filepath),
                'module': os.path.splitext(os.path.basename(filepath))[0]
            })
    
    return functions

def generate_mkdocs_structure(functions_data, output_dir='docs'):
    """Génère la structure de documentation pour MkDocs."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Organiser les fonctions par module
    modules = {}
    for func in functions_data:
        if func['module'] not in modules:
            modules[func['module']] = []
        modules[func['module']].append(func)
    
    # Créer un fichier markdown par module
    nav_items = []
    for module_name, functions in modules.items():
        module_file = f"{output_dir}/{module_name}.md"
        
        with open(module_file, 'w', encoding='utf-8') as md_file:
            # En-tête de la page
            md_file.write(f"# Module `{module_name}`\n\n")
            md_file.write(f"*Fichier source : `{functions[0]['file']}`*\n\n")
            
            # Liste des fonctions
            md_file.write("## Fonctions\n")
            for func in functions:
                md_file.write(f"- [`{func['name']}({func['params']})`](#{func['name'].lower()})\n")
            md_file.write("\n---\n\n")
            
            # Détail des fonctions
            for func in functions:
                md_file.write(f"## `{func['name']}({func['params']})` {{ #{func['name'].lower()} }}\n\n")
                md_file.write(f"```python\ndef {func['name']}({func['params']})\n```\n\n")
                md_file.write(f"{func['docstring']}\n\n")
                md_file.write("---\n\n")
        
        nav_items.append({module_name: f"{module_name}.md"})
    
    # Créer la page d'accueil
    with open(f"{output_dir}/index.md", 'w', encoding='utf-8') as index_file:
        index_file.write("# Documentation du projet\n\n")
        index_file.write(f"*Générée automatiquement le {datetime.now().strftime('%d/%m/%Y à %H:%M')}*\n\n")
        index_file.write("## Modules disponibles\n")
        
        for module in sorted(modules.keys()):
            index_file.write(f"- [{module}]({module}.md)\n")
    
    # Créer le fichier de configuration mkdocs.yml
    mkdocs_config = {
        'site_name': 'Documentation du projet',
        'site_url': '',
        'repo_url': '',
        'theme': {
            'name': 'material',
            'features': [
                'navigation.tabs',
                'navigation.sections',
                'toc.integrate',
                'search.highlight',
                'content.code.annotate'
            ],
            'palette': [
                {
                    'scheme': 'default',
                    'primary': 'deep purple',
                    'toggle': {
                        'icon': 'material/toggle-switch-off-outline',
                        'name': 'Passer en mode sombre'
                    }
                },
                {
                    'scheme': 'slate',
                    'primary': 'deep purple',
                    'toggle': {
                        'icon': 'material/toggle-switch',
                        'name': 'Passer en mode clair'
                    }
                }
            ]
        },
        'markdown_extensions': [
            'admonition',
            'toc',
            {'toc': {'permalink': True}},
            'pymdownx.highlight',
            'pymdownx.superfences',
            'pymdownx.details'
        ],
        'nav': [
            {'Accueil': 'index.md'},
            {'Modules': nav_items}
        ]
    }
    
    with open('mkdocs.yml', 'w', encoding='utf-8') as config_file:
        yaml.dump(mkdocs_config, config_file, allow_unicode=True, sort_keys=False)
    
    print(f"Structure MkDocs générée dans le dossier '{output_dir}'")

def main():
    print("🔍 Recherche des fichiers Python...")
    python_files = find_python_files()
    
    if not python_files:
        print("Aucun fichier Python trouvé.")
        return
    
    print(f"📂 {len(python_files)} fichiers trouvés:")
    for file in python_files[:3]:
        print(f" - {file}")
    if len(python_files) > 3:
        print(f" - ...et {len(python_files)-3} autres")
    
    print("\n📝 Extraction des fonctions...")
    all_functions = []
    for file in python_files:
        try:
            functions = extract_functions(file)
            all_functions.extend(functions)
        except Exception as e:
            print(f"⚠️ Erreur dans {file}: {str(e)}")
    
    if not all_functions:
        print("Aucune fonction trouvée.")
        return
    
    print(f"\n✨ {len(all_functions)} fonctions trouvées dans {len(python_files)} fichiers")
    
    print("\n🏗 Génération de la documentation MkDocs...")
    generate_mkdocs_structure(all_functions)
    
    print("\n✅ Documentation générée avec succès!")
    print("\nPour visualiser la documentation:")
    print("1. Installez MkDocs: pip install mkdocs mkdocs-material")
    print("2. Lancez le serveur: mkdocs serve")
    print("3. Ouvrez http://localhost:8000 dans votre navigateur")

if __name__ == '__main__':
    main()