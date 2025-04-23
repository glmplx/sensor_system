"""
Fonctions utilitaires pour le système de capteurs
"""

import time
import numpy as np

def calculate_slope(x_values, y_values, window_size=10):
    """
    Calculer la pente d'une ligne ajustée aux valeurs données
    
    Args:
        x_values: Liste des valeurs x
        y_values: Liste des valeurs y
        window_size: Nombre de points à inclure dans le calcul
    
    Returns:
        float: Pente de la ligne
    """
    if len(x_values) < 2 or len(y_values) < 2:
        return 0.0
    
    if len(x_values) != len(y_values):
        raise ValueError("x_values et y_values doivent avoir la même longueur")
    
    if window_size > len(x_values):
        window_size = len(x_values)
    
    x_window = x_values[-window_size:]
    y_window = y_values[-window_size:]
    
    return np.polyfit(x_window, y_window, 1)[0]

def find_indices_for_sliding_window(time_values, current_time, half_window_size):
    """
    Trouver les indices pour une fenêtre glissante autour d'un temps donné
    
    Args:
        time_values: Liste des valeurs temporelles
        current_time: Temps central pour la fenêtre
        half_window_size: Demi-taille de la fenêtre en unités de temps
    
    Returns:
        tuple: (indice_début, indice_fin)
    """
    start_idx = None
    end_idx = None
    
    for i, t in enumerate(time_values):
        if t >= current_time - half_window_size and start_idx is None:
            start_idx = i
        if t <= current_time + half_window_size:
            end_idx = i
    
    if end_idx >= len(time_values):
        end_idx = len(time_values) - 1
    
    if start_idx is None:
        start_idx = 0
    
    return start_idx, end_idx

def parse_co2_data(line):
    """
    Analyser les données de CO2, température et humidité à partir d'une ligne
    
    Args:
        line: Ligne lue depuis le port série
    
    Returns:
        tuple: (co2, température, humidité) ou None si l'analyse a échoué
    """
    if not line or not line.startswith('@'):
        return None
    
    data = line[1:].split()
    if len(data) != 3:
        return None
    
    try:
        co2 = float(data[0])
        temperature = float(data[1])
        humidity = float(data[2])
        return co2, temperature, humidity
    except ValueError:
        return None

def parse_pin_states(line):
    """
    Analyser les états des pins à partir d'une ligne de données Arduino
    
    Args:
        line: Ligne lue depuis le port série contenant les états des pins
        
    Returns:
        dict: Dictionnaire des états des pins {'vr': bool, 'vs': bool, 'to': bool, 'tf': bool}
              ou None si l'analyse a échoué
    """
    if not line or not ("VR:" in line and "VS:" in line and "TO:" in line and "TF:" in line):
        return None
        
    try:
        # Analyser les états des pins individuels
        vr_part = line.split("VR:")[1].split()[0]
        vs_part = line.split("VS:")[1].split()[0]
        to_part = line.split("TO:")[1].split()[0]
        tf_part = line.split("TF:")[1].split()[0]
        
        # Clarifier l'analyse des états (HIGH = True, LOW = False)
        vr_state = vr_part == "HIGH"
        vs_state = vs_part == "HIGH"
        to_state = to_part == "HIGH"
        tf_state = tf_part == "HIGH"
        
        # Retourner les états des pins
        return {
            'vr': vr_state,  # Vérin Rentré
            'vs': vs_state,  # Vérin Sorti
            'to': to_state,  # Trappe Ouverte
            'tf': tf_state   # Trappe Fermée
        }
    except Exception as e:
        return None