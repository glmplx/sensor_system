"""
Gestionnaire de configuration pour le système de capteurs.
Gère le chargement et la sauvegarde des paramètres depuis/vers un fichier JSON externe.
"""

import os
import sys
import json
import inspect
from typing import Dict, Any

# Constantes internes
DEFAULT_CONFIG_FILENAME = "sensor_config.json"

def is_running_as_executable() -> bool:
    """
    Détermine si l'application est exécutée en tant qu'exécutable compilé.
    
    Returns:
        bool: True si exécuté en tant qu'exécutable, False sinon
    """
    return getattr(sys, 'frozen', False)

def get_application_path() -> str:
    """
    Obtient le chemin de l'application, que ce soit en mode exécutable ou script.
    
    Returns:
        str: Chemin de l'application
    """
    if is_running_as_executable():
        # En mode exécutable, on utilise sys._MEIPASS (PyInstaller) ou sys.executable
        if hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS
        return os.path.dirname(sys.executable)
    else:
        # En mode script, on utilise le répertoire racine du projet
        # Remonter jusqu'au répertoire parent des modules importés
        import core
        return os.path.dirname(os.path.dirname(inspect.getfile(core)))

def get_config_file_path() -> str:
    """
    Obtient le chemin du fichier de configuration.
    
    Returns:
        str: Chemin complet du fichier de configuration
    """
    if is_running_as_executable():
        # En mode exécutable, le fichier est à côté de l'exécutable
        return os.path.join(get_application_path(), DEFAULT_CONFIG_FILENAME)
    else:
        # En mode script, le fichier est dans le dossier core/
        return os.path.join(get_application_path(), 'core', DEFAULT_CONFIG_FILENAME)

def save_config(config_data: Dict[str, Any]) -> bool:
    """
    Sauvegarde les paramètres de configuration dans un fichier JSON.
    
    Args:
        config_data: Dictionnaire contenant les paramètres à sauvegarder
        
    Returns:
        bool: True si la sauvegarde a réussi, False sinon
    """
    try:
        config_path = get_config_file_path()
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde de la configuration: {e}")
        return False

def load_config() -> Dict[str, Any]:
    """
    Charge les paramètres de configuration depuis le fichier JSON.
    Si le fichier n'existe pas ou est invalide, retourne un dictionnaire vide.
    
    Returns:
        dict: Dictionnaire contenant les paramètres chargés
    """
    config_path = get_config_file_path()
    
    # Si le fichier n'existe pas, retourner un dictionnaire vide
    if not os.path.exists(config_path):
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erreur lors du chargement de la configuration: {e}")
        return {}

def get_constants_as_dict() -> Dict[str, Any]:
    """
    Récupère les constantes du fichier sensor_config.json sous forme de dictionnaire.
    
    Returns:
        dict: Dictionnaire contenant les constantes
    """
    return load_config()

def update_constants_from_config() -> bool:
    """
    Charge la configuration depuis le fichier JSON.
    
    Returns:
        bool: True si le chargement a réussi, False sinon
    """
    try:
        config = load_config()
        return bool(config)
    except Exception as e:
        print(f"Erreur lors du chargement de la configuration: {e}")
        return False

def save_constants_to_config() -> bool:
    """
    Sauvegarde les constantes actuelles dans le fichier de configuration.
    
    Returns:
        bool: True si la sauvegarde a réussi, False sinon
    """
    try:
        constants_dict = get_constants_as_dict()
        return save_config(constants_dict)
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des constantes: {e}")
        return False