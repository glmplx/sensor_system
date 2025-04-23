#!/usr/bin/env python
"""
Script to create an installer for the sensor system application
using NSIS (Nullsoft Scriptable Install System)
"""

import os
import subprocess
import sys
import shutil

def create_installer():
    """Create an installer for the sensor system application"""
    
    # Get the current directory (where this script is located)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Ensure working directory is set correctly
    os.chdir(current_dir)
    
    # Check if dist folder exists
    dist_folder = os.path.join(current_dir, 'dist')
    if not os.path.exists(dist_folder) or not os.path.exists(os.path.join(dist_folder, 'SensorSystem.exe')):
        print("Le dossier 'dist' ou l'exécutable n'a pas été trouvé.")
        print("Veuillez d'abord exécuter 'python create_executable.py' pour créer l'exécutable.")
        return False
    
    # Check if NSIS is installed
    nsis_path = None
    possible_paths = [
        r"C:\Program Files (x86)\NSIS\makensis.exe",
        r"C:\Program Files\NSIS\makensis.exe"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            nsis_path = path
            break
    
    if nsis_path is None:
        print("NSIS n'a pas été trouvé. Veuillez installer NSIS (Nullsoft Scriptable Install System).")
        print("Téléchargement: https://nsis.sourceforge.io/Download")
        return False
    
    # NSIS script path
    nsis_script = os.path.join(current_dir, 'create_installer.nsi')
    
    if not os.path.exists(nsis_script):
        print(f"Le script NSIS n'a pas été trouvé: {nsis_script}")
        return False
    
    # Create the installer
    print("Création de l'installateur...")
    try:
        # Run NSIS compiler
        subprocess.run([nsis_path, nsis_script], check=True)
        
        # Check if installer was created
        installer_path = os.path.join(current_dir, 'SensorSystemInstaller.exe')
        if os.path.exists(installer_path):
            print(f"Installateur créé avec succès: {installer_path}")
            return True
        else:
            print("L'installateur n'a pas été créé. Vérifiez les erreurs NSIS.")
            return False
        
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de la création de l'installateur: {e}")
        return False
    
    return True

if __name__ == "__main__":
    create_installer()