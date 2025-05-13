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
    # En mode exécutable, le fichier est à côté de l'exécutable
    # En mode script, il est dans le répertoire du projet
    return os.path.join(get_application_path(), DEFAULT_CONFIG_FILENAME)

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
    Récupère les constantes du module constants.py sous forme de dictionnaire.
    Ne récupère que les constantes numériques (int, float) et les chaînes de caractères.
    
    Returns:
        dict: Dictionnaire contenant les constantes
    """
    from core import constants
    
    # Filtrer pour ne garder que les constantes (majuscules) et exclure les modules, fonctions, etc.
    constants_dict = {
        name: value for name, value in inspect.getmembers(constants)
        if name.isupper() and not inspect.ismodule(value) and not inspect.isfunction(value) 
        and not inspect.isclass(value) and not name.startswith('_')
    }
    
    # Exclure les dictionnaires et autres structures complexes qui ne peuvent pas être
    # simplement convertis en JSON
    for key in list(constants_dict.keys()):
        if isinstance(constants_dict[key], (dict, list, tuple)) or callable(constants_dict[key]):
            del constants_dict[key]
    
    return constants_dict

def update_constants_from_config() -> bool:
    """
    Met à jour les constantes du module à partir du fichier de configuration.
    
    Returns:
        bool: True si la mise à jour a réussi, False sinon
    """
    try:
        # Ne charger la configuration que si nous sommes en mode exécutable
        if not is_running_as_executable():
            return True
        
        # Charger la configuration
        config = load_config()
        if not config:
            return True  # Pas de configuration à appliquer
        
        # Mettre à jour les constantes dans le module
        import core.constants
        updated = False
        
        for key, value in config.items():
            if hasattr(core.constants, key):
                # Vérifier que le type est compatible
                original_value = getattr(core.constants, key)
                if isinstance(original_value, (int, float, str)) and isinstance(value, (int, float, str)):
                    setattr(core.constants, key, value)
                    updated = True
        
        return updated
    except Exception as e:
        print(f"Erreur lors de la mise à jour des constantes: {e}")
        return False

def save_constants_to_config() -> bool:
    """
    Sauvegarde les constantes actuelles dans le fichier de configuration.
    
    Returns:
        bool: True si la sauvegarde a réussi, False sinon
    """
    try:
        # Ne sauvegarder la configuration que si nous sommes en mode exécutable
        if not is_running_as_executable():
            return True
        
        # Récupérer les constantes sous forme de dictionnaire
        constants_dict = get_constants_as_dict()
        
        # Sauvegarder dans le fichier de configuration
        return save_config(constants_dict)
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des constantes: {e}")
        return False