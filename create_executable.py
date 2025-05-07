#!/usr/bin/env python
"""
Script to create an executable for the sensor system application
"""

import os
import subprocess
import sys
import shutil
import tempfile

def create_executable():
    """Create an executable for the sensor system application"""
    
    # Get the current directory (where this script is located)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Ensure working directory is set correctly
    os.chdir(current_dir)
    
    # Define paths
    main_script = os.path.join(current_dir, 'main.py')
    
    # Create a temporary file for the spec file
    with tempfile.NamedTemporaryFile(suffix='.spec', delete=False) as temp_file:
        spec_file = temp_file.name
    
    # Normalize paths for the spec file
    main_script_norm = main_script.replace("\\", "/")
    current_dir_norm = current_dir.replace("\\", "/")
    
    # Write the spec file content using a simpler approach with string concatenation
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['""" + main_script_norm + """'],
    pathex=['""" + current_dir_norm + """'],
    binaries=[],
    datas=[
"""
    
    # Add data files if they exist
    if os.path.exists(os.path.join(current_dir, 'README.md')):
        spec_content += "        ('" + os.path.join(current_dir_norm, 'README.md') + "', '.'),\n"
    if os.path.exists(os.path.join(current_dir, 'DOCUMENTATION.md')):
        spec_content += "        ('" + os.path.join(current_dir_norm, 'DOCUMENTATION.md') + "', '.'),\n"
    if os.path.exists(os.path.join(current_dir, 'mkdocs.yml')):
        spec_content += "        ('" + os.path.join(current_dir_norm, 'mkdocs.yml') + "', '.'),\n"
    if os.path.exists(os.path.join(current_dir, 'docs')) and os.path.isdir(os.path.join(current_dir, 'docs')):
        spec_content += "        ('" + os.path.join(current_dir_norm, 'docs') + "', 'docs'),\n"
    
    spec_content += """    ],
    hiddenimports=[
        'matplotlib',
        'numpy',
        'pandas',
        'openpyxl',
        'tkinter',
        'serial',
        'serial.tools.list_ports',
        'pyvisa',
        'pyvisa.ctwrapper.highlevel',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.backends.backend_pdf',
        'matplotlib.backends.backend_svg',
        'matplotlib.backends.backend_ps',
        'matplotlib.backends.backend_pgf',
        'matplotlib.backends.backend_agg',
        'PyQt5'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SensorSystem',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
"""
    
    with open(spec_file, 'w') as f:
        f.write(spec_content)
    
    # Execute PyInstaller with the spec file
    print("Creating executable...")
    
    try:
        # First check if PyInstaller is installed
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], 
                       check=True)
        
        # Then create the executable using the spec file
        subprocess.run(['pyinstaller', '--clean', spec_file], check=True)
        
        # Cleanup the spec file
        os.unlink(spec_file)
        
        # Copy README to the dist folder
        readme_path = os.path.join(current_dir, 'README_EXECUTABLE.md')
        if not os.path.exists(readme_path):
            # Create a README file for the executable
            with open(readme_path, 'w') as f:
                f.write("""# Systeme de capteurs - Executable

Cet exécutable contient le systeme complet de capteurs. Il ne nécessite pas d'installation de Python ni de bibliothèques supplémentaires.

## Utilisation

1. Double-cliquez sur le fichier SensorSystem.exe pour lancer l'application
2. Sélectionnez les ports COM pour les différents appareils
3. Choisissez le mode (Manuel ou Automatique)
4. Cliquez sur "Lancer le programme"

## Résolution des problèmes

- Si l'exécutable ne se lance pas, essayez de le déplacer dans un dossier dont le chemin ne contient pas de caractères spéciaux
- Pour les problèmes de connexion aux appareils, vérifiez que les pilotes des ports COM sont correctement installés
- Pour tout autre problème, consultez la documentation complète
""")
        
        # Copy README to dist folder
        dist_readme = os.path.join(current_dir, 'dist', 'README.md')
        shutil.copy2(readme_path, dist_readme)
        
        # Copy other documentation files
        docs_files = {
            'README.md': 'README.md',
            'DOCUMENTATION.md': 'DOCUMENTATION.md',
            'mkdocs.yml': 'mkdocs.yml'
        }
        
        for src_file, dest_file in docs_files.items():
            src_path = os.path.join(current_dir, src_file)
            if os.path.exists(src_path):
                dest_path = os.path.join(current_dir, 'dist', dest_file)
                shutil.copy2(src_path, dest_path)
                print(f"Copied {src_file} to dist folder")
        
        # Copy docs directory if it exists
        docs_dir = os.path.join(current_dir, 'docs')
        if os.path.exists(docs_dir) and os.path.isdir(docs_dir):
            docs_dist_dir = os.path.join(current_dir, 'dist', 'docs')
            if os.path.exists(docs_dist_dir):
                shutil.rmtree(docs_dist_dir)
            shutil.copytree(docs_dir, docs_dist_dir)
            print("Copied docs directory to dist folder")
        
        print("Executable created successfully in the 'dist' folder.")
        print(f"Execute path: {os.path.join(current_dir, 'dist', 'SensorSystem.exe')}")

    except subprocess.CalledProcessError as e:
        print(f"Error creating executable: {e}")
        return False
    
    return True

if __name__ == "__main__":
    create_executable()