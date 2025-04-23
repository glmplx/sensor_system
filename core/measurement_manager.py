"""
Gestionnaire de mesures - Gère la logique de collecte et de traitement des données
"""

import time
import numpy as np
from datetime import datetime
from core.constants import (
    INCREASE_SLOPE_MIN, INCREASE_SLOPE_MAX, STABILITY_DURATION,
    SLIDING_WINDOW, R0_THRESHOLD, REGENERATION_TEMP, TCONS_LOW, VALVE_DELAY,
    CO2_STABILITY_THRESHOLD, CO2_STABILITY_DURATION, REGENERATION_DURATION
)

class MeasurementManager:
    """Gère toutes les opérations de mesure et la logique de détection"""
    
    def __init__(self, keithley_device, arduino_device, regen_device):
        """
        Initialise le gestionnaire de mesures
        
        Args:
            keithley_device: Appareil pour les mesures de résistance
            arduino_device: Appareil pour les mesures de CO2, température, humidité
            regen_device: Appareil pour le contrôle de température de résistance
        """
        self.keithley = keithley_device
        self.arduino = arduino_device
        self.regen = regen_device
        
        # Stockage des données pour les mesures de conductance
        self.timeList = []
        self.conductanceList = []
        self.resistanceList = []
        
        # Stockage des données pour CO2, température et humidité
        self.timestamps_co2 = []
        self.values_co2 = []
        self.timestamps_temp = []
        self.values_temp = []
        self.timestamps_humidity = []
        self.values_humidity = []
        
        # Stockage des données pour la température de résistance
        self.timestamps_res_temp = []
        self.temperatures = []
        self.Tcons_values = []
        
        # Variables de suivi du temps
        self.start_time_conductance = None
        self.start_time_co2_temp_humidity = None
        self.start_time_res_temp = None
        self.elapsed_time_conductance = 0
        self.elapsed_time_co2_temp_humidity = 0
        self.elapsed_time_res_temp = 0
        
        # Variables pour le parallélisme et l'asynchrone
        self.async_tasks = []
        self.delayed_actions = {}
        
        # Variables pour mémoriser le moment de pause
        self.pause_time_conductance = None
        self.pause_time_co2_temp_humidity = None
        self.pause_time_res_temp = None
        
        # Variables d'état
        self.increase_detected = False
        self.stabilized = False
        self.increase_time = None
        self.stabilization_time = None
        self.max_slope_value = 0
        self.max_slope_time = 0
        self.sensor_state = None  # None: inconnu, True: sorti, False: rentré
        self.escape_pressed = False
        self.last_set_Tcons = None  # Stocke la dernière valeur de Tcons définie
        
        # Variables pour la détection d'augmentation de CO2 après Tcons=700
        self.co2_increase_detection_started = None
        self.co2_base_value = None
        self.co2_increase_detected = False
        
        # Variables pour la détection de fin de montée et stabilisation du CO2
        self.co2_peak_value = None
        self.co2_peak_time = None
        self.co2_peak_detected = False
        self.co2_max_slope_value = 0
        self.co2_max_slope_time = 0
        self.co2_peak_detection_started = None
        self.co2_peak_detection_value = None
        self.co2_restabilization_start_time = None
        self.co2_restabilization_reference = None
        self.co2_restabilized = False
        self.tcons_reduced = False  # Indique si Tcons a été remis à 0°C
        
        # Variables pour le suivi des valeurs post-augmentation CO2
        self.co2_values_after_increase = []
        self.co2_timestamps_after_increase = []
        
        # Variables pour le suivi des déplacements de stabilité CO2
        self.co2_stability_shifted = False
        self.co2_previous_stable_value = None
        self.co2_stability_shift_count = 0
        
        # Pin states for vérin and trappe indicators
        self.pin_states = {
            'vr': False,  # Vérin Rentré
            'vs': False,  # Vérin Sorti
            'to': False,  # Trappe Ouverte
            'tf': False   # Trappe Fermée
        }
        
        # Variables du protocole de régénération
        self.regeneration_in_progress = False
        self.regeneration_step = 0  # 0: non démarré, 1: vérification stabilité CO2, 2: régénération active, 3: terminée
        self.co2_stability_start_time = None
        self.regeneration_start_time = None
        self.co2_stable_value = None  # Pour stocker la valeur de référence CO2 pour la vérification de stabilité
        
        # Horodatages des événements clés dans le protocole de régénération (pour les marqueurs de tracé)
        self.regeneration_timestamps = {
            'r0_actualized': None,          # Moment où R0 est actualisé
            'co2_stability_started': None,  # Moment où on commence à vérifier la stabilité CO2
            'co2_stability_achieved': None, # Moment où la stabilité CO2 est confirmée
            'co2_increase_detected': None,  # Moment où l'augmentation de CO2 est détectée après Tcons=700
            'co2_peak_reached': None,       # Moment où le CO2 atteint son maximum après l'augmentation
            'co2_restabilization_start_time': None,  # Moment où on commence à chercher la restabilisation
            'co2_restabilized': None        # Moment où le CO2 se stabilise à nouveau après l'augmentation
        }
        
        # Résultats de calculs pour le protocole de régénération
        self.regeneration_results = {
            'delta_c': 0,                   # Différence de CO2 entre avant et après régénération (ppm)
            'carbon_mass': 0                # Masse de carbone calculée (µg)
        }
    
    def reset_data(self, data_type=None):
        """
        Reset stored data
        
        Args:
            data_type: Type of data to reset, or None for all data
        """
        # Sauvegardons la dernière valeur de Tcons avant de tout réinitialiser
        last_tcons = getattr(self, 'last_set_Tcons', None)
        
        if data_type in [None, "conductance"]:
            self.timeList.clear()
            self.conductanceList.clear()
            self.resistanceList.clear()
            self.start_time_conductance = None
            self.pause_time_conductance = None
            self.elapsed_time_conductance = 0
        
        if data_type in [None, "co2_temp_humidity"]:
            self.timestamps_co2.clear()
            self.values_co2.clear()
            self.timestamps_temp.clear()
            self.values_temp.clear()
            self.timestamps_humidity.clear()
            self.values_humidity.clear()
            self.start_time_co2_temp_humidity = None
            self.pause_time_co2_temp_humidity = None
            self.elapsed_time_co2_temp_humidity = 0
        
        if data_type in [None, "res_temp"]:
            self.timestamps_res_temp.clear()
            self.temperatures.clear()
            self.Tcons_values.clear()
            self.start_time_res_temp = None
            self.pause_time_res_temp = None
            self.elapsed_time_res_temp = 0
        
        if data_type in [None, "detection"]:
            self.increase_detected = False
            self.stabilized = False
            self.increase_time = None
            self.stabilization_time = None
            self.max_slope_value = 0
            self.max_slope_time = 0
            
        # Restaurons la dernière valeur de Tcons
        if last_tcons is not None:
            self.last_set_Tcons = last_tcons
    
    async def schedule_delayed_action(self, action_id, delay_seconds, action_func, *args, **kwargs):
        """
        Planifie une action à exécuter après un délai, sans bloquer le thread principal
        
        Args:
            action_id: Identifiant unique pour cette action
            delay_seconds: Délai en secondes avant d'exécuter l'action
            action_func: Fonction à exécuter
            *args, **kwargs: Arguments pour la fonction
        """
        import asyncio
        
        # Annuler toute action existante avec le même ID
        if action_id in self.delayed_actions:
            self.delayed_actions[action_id].cancel()
            
        # Créer une nouvelle tâche asynchrone
        loop = asyncio.get_event_loop()
        task = loop.create_task(self._run_delayed_action(delay_seconds, action_func, *args, **kwargs))
        self.delayed_actions[action_id] = task
        
        # Ajouter un callback pour nettoyer l'entrée dans le dictionnaire une fois terminée
        def cleanup_task(task):
            if action_id in self.delayed_actions:
                del self.delayed_actions[action_id]
        
        task.add_done_callback(cleanup_task)
        return task
    
    async def _run_delayed_action(self, delay_seconds, action_func, *args, **kwargs):
        """Fonction interne pour exécuter une action après un délai"""
        import asyncio
        await asyncio.sleep(delay_seconds)
        return action_func(*args, **kwargs)
    
    def read_conductance(self):
        """Lire les données de conductance depuis le Keithley"""
        current_time = time.time()
        
        # Vérifier si le Keithley est disponible
        if self.keithley is None:
            print("Avertissement: Tentative de lecture de conductance mais l'appareil Keithley n'est pas disponible")
            return None
        
        # Lire la résistance depuis le Keithley
        try:
            resistance = self.keithley.read_resistance()
            if resistance is None or resistance == 0.0:
                conductance = float('inf')
            else:
                conductance = (1 / resistance) * 1e6  # Conversion en µS
        except Exception as e:
            print(f"Erreur lors de la lecture de conductance: {e}")
            return None
        
        # Initialiser start_time seulement quand on obtient réellement des données à tracer
        if self.start_time_conductance is None:
            self.start_time_conductance = current_time
        
        # Calculer l'horodatage
        timestamp = current_time - self.start_time_conductance - self.elapsed_time_conductance
        
        # Stocker les données
        self.timeList.append(timestamp)
        self.conductanceList.append(conductance)
        self.resistanceList.append(resistance)
        
        return {
            'timestamp': timestamp,
            'conductance': conductance,
            'resistance': resistance
        }
    
    def read_arduino_status_only(self):
        """
        Lire les états des broches Arduino sans stocker les données CO2/température/humidité
        Returns: True si les états des broches ont été mis à jour, False sinon
        """
        line = self.arduino.read_line()
        
        # Vérifier les messages d'état du capteur (broches VR, VS, TO, TF)
        if line and "VR:" in line and "VS:" in line and "TO:" in line and "TF:" in line:
            try:
                # Analyser les états individuels des broches
                vr_part = line.split("VR:")[1].split()[0]
                vs_part = line.split("VS:")[1].split()[0]
                to_part = line.split("TO:")[1].split()[0]
                tf_part = line.split("TF:")[1].split()[0]
                
                # Clarifier l'analyse de l'état (HIGH = True, LOW = False)
                vr_state = vr_part == "HIGH"
                vs_state = vs_part == "HIGH"
                to_state = to_part == "HIGH"
                tf_state = tf_part == "HIGH"
                
                # Afficher l'état pour le débogage
                print(f"États des broches: VR={vr_state}, VS={vs_state}, TO={to_state}, TF={tf_state}")
                
                # Stocker les états des broches pour la mise à jour de l'interface utilisateur
                self.pin_states = {
                    'vr': vr_state,  # Vérin Rentré
                    'vs': vs_state,  # Vérin Sorti
                    'to': to_state,  # Trappe Ouverte
                    'tf': tf_state   # Trappe Fermée
                }
                return True
            except Exception as e:
                print(f"Erreur lors de l'analyse des états des broches: {e}, ligne: {line}")
                return False
        
        # Ignorer les données CO2/temp/humidity si la ligne commence par @
        if line and line.startswith('@'):
            return True  # Juste pour indiquer qu'une ligne a été traitée
            
        return False  # Aucune ligne valide
    
    def read_arduino_data(self):
        """
        Lire les données CO2, température, humidité depuis l'Arduino et les stocker
        Appelé uniquement lorsque les mesures sont actives
        """
        current_time = time.time()
        
        # Vérifier si l'Arduino est disponible
        if not hasattr(self.arduino, 'read_line') or self.arduino.device is None:
            return None
        
        # Initialiser start_time uniquement lors de la collecte du premier point de données
        # au lieu de lorsque la fonction est appelée pour la première fois
        line = self.arduino.read_line()
        
        # Si pas de ligne, c'est peut-être un Arduino simulé ou pas de données
        if not line:
            return None
        
        # Gérer les mises à jour d'état des broches si elles arrivent
        if line and "VR:" in line and "VS:" in line and "TO:" in line and "TF:" in line:
            try:
                # Analyser les états individuels des broches
                vr_part = line.split("VR:")[1].split()[0]
                vs_part = line.split("VS:")[1].split()[0]
                to_part = line.split("TO:")[1].split()[0]
                tf_part = line.split("TF:")[1].split()[0]
                
                # Clarifier l'analyse de l'état (HIGH = True, LOW = False)
                vr_state = vr_part == "HIGH"
                vs_state = vs_part == "HIGH"
                to_state = to_part == "HIGH"
                tf_state = tf_part == "HIGH"
                
                # Stocker les états des broches pour la mise à jour de l'interface utilisateur
                self.pin_states = {
                    'vr': vr_state,  # Vérin Rentré
                    'vs': vs_state,  # Vérin Sorti
                    'to': to_state,  # Trappe Ouverte
                    'tf': tf_state   # Trappe Fermée
                }
            except Exception as e:
                print(f"Erreur lors de l'analyse des états des broches: {e}, ligne: {line}")
            
            return None  # Pas de données CO2 dans ce message
        
        if not line.startswith('@'):
            return None
        
        data = line[1:].split()
        if len(data) != 3:
            return None
        
        # Analyser les données
        try:
            co2 = float(data[0])
            temperature = float(data[1])
            humidity = float(data[2])
        except ValueError:
            return None
        
        # Initialiser start_time uniquement lorsqu'on obtient réellement des données à tracer
        if self.start_time_co2_temp_humidity is None:
            self.start_time_co2_temp_humidity = current_time
        
        # Calculer l'horodatage
        timestamp = current_time - self.start_time_co2_temp_humidity - self.elapsed_time_co2_temp_humidity
        
        # Stocker les données
        self.timestamps_co2.append(timestamp)
        self.values_co2.append(co2)
        self.timestamps_temp.append(timestamp)
        self.values_temp.append(temperature)
        self.timestamps_humidity.append(timestamp)
        self.values_humidity.append(humidity)
        
        return {
            'timestamp': timestamp,
            'co2': co2,
            'temperature': temperature,
            'humidity': humidity
        }
        
    def read_arduino(self):
        """
        Méthode pour compatibilité - redirige vers read_arduino_data
        """
        return self.read_arduino_data()
    
    def read_res_temp(self):
        """Lire les données de température de résistance"""
        current_time = time.time()
        
        # Vérifier si le dispositif de régénération est disponible
        if self.regen is None or not hasattr(self.regen, 'device') or self.regen.device is None:
            print("Avertissement: Tentative de lecture de res_temp mais le dispositif de régénération n'est pas disponible")
            return None
        
        try:
            raw_tcons = self.regen.read_variable('L', 'a')
            Tcons_value = float(raw_tcons)
            temperature_value = float(self.regen.read_variable('L', 'd'))
            
            # Utilisation systématique de la dernière valeur définie pour Tcons
            # plutôt que de faire confiance à la valeur retournée par l'appareil
            if hasattr(self, 'last_set_Tcons') and self.last_set_Tcons is not None:
                # Si la dernière valeur définie est différente, on l'utilise
                if abs(Tcons_value - self.last_set_Tcons) > 50:  # Différence significative
                    Tcons_value = self.last_set_Tcons
                
        except (ValueError, TypeError) as e:
            print(f"Erreur lors de la lecture de la température: {e}, raw_tcons={raw_tcons if 'raw_tcons' in locals() else 'N/A'}")
            return None
        
        # Initialiser start_time uniquement lorsqu'on obtient réellement des données à tracer
        if self.start_time_res_temp is None:
            self.start_time_res_temp = current_time
        
        # Calculer l'horodatage
        timestamp = current_time - self.start_time_res_temp - self.elapsed_time_res_temp
        
        # Stocker les données
        self.timestamps_res_temp.append(timestamp)
        self.temperatures.append(temperature_value)
        self.Tcons_values.append(Tcons_value)
        
        return {
            'timestamp': timestamp,
            'temperature': temperature_value,
            'Tcons': Tcons_value
        }
    
    def push_open_sensor(self):
        """Pousser/ouvrir le capteur"""
        # Vérifier si l'Arduino est disponible
        if not hasattr(self.arduino, 'send_command') or self.arduino.device is None:
            print("Avertissement: Tentative de pousser/ouvrir le capteur mais l'Arduino n'est pas disponible")
            return False
            
        self.arduino.send_command("ouvrir\n")
        self.sensor_state = True
        return True
        
    def retract_close_sensor(self):
        """Rétracter/fermer le capteur"""
        # Vérifier si l'Arduino est disponible
        if not hasattr(self.arduino, 'send_command') or self.arduino.device is None:
            print("Avertissement: Tentative de rétracter/fermer le capteur mais l'Arduino n'est pas disponible")
            return False
            
        self.arduino.send_command("fermer\n")
        self.sensor_state = False
        return True
        
    def init_system(self):
        """Initialiser le système"""
        # Vérifier si l'Arduino est disponible
        if not hasattr(self.arduino, 'send_command') or self.arduino.device is None:
            print("Avertissement: Tentative d'initialisation du système mais l'Arduino n'est pas disponible")
            return False
            
        self.arduino.send_command("init\n")
        # État reste inchangé après initialisation
        return True
    
    def set_R0(self, value):
        """Set R0 value"""
        # Vérifier si le dispositif de régénération est disponible
        if self.regen is None or not hasattr(self.regen, 'device') or self.regen.device is None:
            print("Warning: Attempting to set R0 but regeneration device is not available")
            return False
            
        self.regen.write_parameter('e', 'b', str(value))
        return True
    
    def set_Tcons(self, value):
        """Set Tcons value"""
        # Vérifier si le dispositif de régénération est disponible
        if self.regen is None or not hasattr(self.regen, 'device') or self.regen.device is None:
            print("Warning: Attempting to set Tcons but regeneration device is not available")
            return False
            
        try:
            value_float = float(value)
            self.last_set_Tcons = value_float
            
            # 1. Utiliser la méthode write_parameter pour envoyer la commande
            result = self.regen.write_parameter('e', 'a', str(value))
            if not result:
                print(f"Avertissement: Échec de l'envoi de Tcons via write_parameter")
                # Si cette méthode échoue, on essaie la méthode directe en 2
                
            # 2. Essayer également d'écrire directement sur le périphérique pour s'assurer
            # que la commande est transmise efficacement
            try:
                if self.regen.device:
                    command_str = f"ea{value}\n"
                    self.regen.device.write(command_str.encode())
                    return True  # Nous considérons que cette méthode fonctionne même si write_parameter échoue
            except Exception as e:
                print(f"Erreur lors de l'écriture directe de Tcons: {e}")
                # Si la méthode directe échoue mais que write_parameter a réussi, on renvoie quand même True
                return result
                
        except ValueError:
            print(f"Erreur: valeur Tcons invalide '{value}'")
            return False
            
        return True
    
    def read_R0(self):
        """Read R0 value"""
        # Vérifier si le dispositif de régénération est disponible
        if self.regen is None or not hasattr(self.regen, 'device') or self.regen.device is None:
            print("Warning: Attempting to read R0 but regeneration device is not available")
            return None
            
        R = self.regen.read_variable('L', 'c')
        parts = R.split('c')
        if len(parts) > 1:
            try:
                return float(parts[1])
            except ValueError:
                print("Error converting R0")
        return None
    
    def detect_increase(self):
        """
        Détecter l'augmentation de la conductance
        Returns: True si une augmentation est détectée, False sinon
        """
        if self.increase_detected or len(self.conductanceList) < 10:
            return False
        
        # Calculer la pente sur les 10 derniers points
        time_window = self.timeList[-10:]
        conductance_window = self.conductanceList[-10:]
        slope = np.polyfit(time_window, conductance_window, 1)[0]  # pente en S/s
        
        if INCREASE_SLOPE_MIN <= slope <= INCREASE_SLOPE_MAX:
            self.increase_detected = True
            self.max_slope_value = slope
            self.max_slope_time = self.timeList[-1]
            self.increase_time = self.timeList[-1]
            print(f"Time {self.timeList[-1]/60:.1f} min: Increase detected! Slope = {slope:.2f} µS/s")
            return True
        
        return False
    
    def detect_stabilization(self):
        """
        Détecter la stabilisation de la conductance
        Returns: True si une stabilisation est détectée, False sinon
        """
        if not self.increase_detected or self.stabilized or len(self.timeList) < 10:
            return False
        
        current_time = self.timeList[-1]
        
        # Trouver les indices pour la fenêtre glissante
        start_idx = None
        end_idx = None
        
        for i, t in enumerate(self.timeList):
            if t >= current_time - SLIDING_WINDOW/2 and start_idx is None:
                start_idx = i
            if t <= current_time + SLIDING_WINDOW/2:
                end_idx = i
        
        if end_idx >= len(self.timeList):
            end_idx = len(self.timeList) - 1
        
        if start_idx is not None and end_idx is not None and start_idx < end_idx:
            window_time = self.timeList[start_idx:end_idx+1]
            window_conductance = self.conductanceList[start_idx:end_idx+1]
            
            if len(window_time) > 1:
                current_slope = np.polyfit(window_time, window_conductance, 1)[0]
                
                # Mettre à jour la pente maximale si nécessaire
                if current_slope > self.max_slope_value:
                    self.max_slope_value = current_slope
                    self.max_slope_time = current_time
                
                # Vérifier si stabilisé
                if (current_time - self.max_slope_time >= STABILITY_DURATION and 
                    abs(current_slope) < INCREASE_SLOPE_MIN/2):
                    self.stabilized = True
                    self.stabilization_time = current_time
                    print(f"Time {current_time/60:.1f} min: Stabilization detected! Last slope = {current_slope:.4f} µS/s")
                    return True
        
        return False
        
    def detect_co2_peak(self):
        """
        Détecter le pic de CO2 après qu'une augmentation a été détectée
        
        Returns:
            None: Met à jour le drapeau self.co2_peak_detected si un pic est détecté
        """
        if not self.co2_peak_detected and self.co2_increase_detected and len(self.values_co2) >= 5:
            current_co2 = self.values_co2[-1]
            max_co2 = max(self.values_co2[-10:])  # Chercher sur les 10 dernières valeurs
            
            # Condition 1: Augmentation minimale de 5 ppm par rapport à la base
            if (max_co2 - self.co2_base_value) >= 5:
                # Condition 2: Descente actuelle d'au moins 1 ppm par rapport au max
                if (max_co2 - current_co2) >= 1:
                    # Condition 3: Pente descendante significative
                    slope = np.polyfit(self.timestamps_co2[-3:], self.values_co2[-3:], 1)[0]
                    if slope < -0.05:  # Pente descendante significative
                        self.co2_peak_detected = True
                        self.co2_peak_value = max_co2
                        self.co2_peak_time = self.timestamps_co2[self.values_co2.index(max_co2, -10)]
                        
                        # Enregistrer le timestamp du pic CO2 pour l'affichage avec pointillés
                        if self.start_time_co2_temp_humidity is not None:
                            self.regeneration_timestamps['co2_peak_reached'] = self.co2_peak_time
                        
                        print(f"Pic CO2 détecté à {max_co2} ppm (augmentation de {max_co2-self.co2_base_value:.1f} ppm)")
                        
                        # Initialiser immédiatement la surveillance de la restabilisation
                        self.co2_restabilization_reference = current_co2
                        self.co2_restabilization_start_time = time.time()
                        # Enregistrer le timestamp pour le début de la recherche de restabilisation
                        if self.start_time_co2_temp_humidity is not None:
                            self.regeneration_timestamps['co2_restabilization_start_time'] = self.timestamps_co2[-1]
                        print(f"Début automatique de la surveillance de restabilisation CO2 à {current_co2} ppm")
        
    def check_reset_detection_indicators(self):
        """
        Vérifie si la conductance est descendue sous 5 µS après stabilisation
        et réinitialise les indicateurs le cas échéant
        
        Returns: True si les indicateurs ont été réinitialisés, False sinon
        """
        # Ne vérifie que si stabilisation a été détectée et qu'il y a des mesures
        if not self.stabilized or len(self.conductanceList) < 1:
            return False
            
        # Vérifie si la conductance actuelle est inférieure à 5 µS
        current_conductance = self.conductanceList[-1]
        if current_conductance < 5.0:
            # Réinitialise les indicateurs de détection
            self.increase_detected = False
            self.stabilized = False
            print(f"Conductance redescendue à {current_conductance:.2f} µS - Indicateurs réinitialisés")
            return True
            
        return False
    
    async def _delay_action(self, delay, callback_func, *args, **kwargs):
        """Exécute une action après un délai sans bloquer le thread principal"""
        import asyncio
        await asyncio.sleep(delay)
        return callback_func(*args, **kwargs)
        
    def schedule_delayed_action(self, action_id, delay_seconds, callback_func, *args, **kwargs):
        """
        Planifie une action à exécuter après un délai sans bloquer
        
        Args:
            action_id: Identifiant unique pour cette action
            delay_seconds: Délai en secondes
            callback_func: Fonction à exécuter après le délai
            *args, **kwargs: Arguments pour la fonction
        """
        # Cette méthode est utilisée pour remplacer les appels à time.sleep
        import threading
        
        def execute_after_delay():
            import time
            time.sleep(delay_seconds)
            return callback_func(*args, **kwargs)
        
        # Créer et démarrer un thread pour l'action différée
        thread = threading.Thread(target=execute_after_delay)
        thread.daemon = True
        thread.start()
        return thread
    
    def automatic_mode_handler(self):
        """
        Gérer la logique du mode automatique
        Returns: True si une action a été prise, False sinon
        """
        # Vérifier l'augmentation de la conductance
        if self.detect_increase():
            return True
            
        # Vérifier la stabilisation
        if self.detect_stabilization():
            # Fermer la vanne après stabilisation
            self.retract_close_sensor()
            print("Auto: Fermeture de la vanne")
            
            # Planifier les actions suivantes après un délai au lieu de bloquer avec time.sleep
            def delayed_actions_after_valve():
                # Lire et mettre à jour R0
                R0 = self.read_R0()
                if R0 is not None and R0 < R0_THRESHOLD:
                    # Actualiser R0 en l'écrivant dans les paramètres
                    self.set_R0(str(R0))
                    print(f"Auto: R0 mis à jour à {R0}")
                    
                    # Mise à jour de Tcons à température élevée
                    success = self.set_Tcons(str(REGENERATION_TEMP))
                    if not success:
                        print(f"Auto: Erreur lors de la définition de Tcons à {REGENERATION_TEMP}°C")
                elif R0 is not None and R0 == 1000:
                    print("Erreur - R0 non détecté")
                else:
                    print("Auto: Erreur - R0 trop élevé (> 12)")
            
            # Lancer les actions avec délai sans bloquer
            self.schedule_delayed_action("post_stabilization", VALVE_DELAY, delayed_actions_after_valve)
            return True
            
        # Vérifier si la conductance est redescendue à 0 après stabilisation
        if self.stabilized and len(self.conductanceList) > 0 and self.conductanceList[-1] <= 1e-6:
            print(f"Auto: Conductance descendue sous 1 µS ({self.conductanceList[-1]*1e6:.2f} µS), attente 5 minutes...")
            
            # Définir Tcons à température basse
            success = self.set_Tcons(str(TCONS_LOW))
            if not success:
                print(f"Auto: Erreur lors de la définition de Tcons à {TCONS_LOW}°C")
            
            # Planifier les actions suivantes après STABILITY_DURATION sans bloquer
            def delayed_actions_after_stability():
                print("Auto: Cycle terminé. Prêt pour le prochain cycle.")
                
                # Ouvrir la vanne
                self.push_open_sensor()
                print("Auto: Ouverture de la vanne")
                
                # Planifier les actions finales après un autre délai
                def reset_detection_flags():
                    # Réinitialiser les indicateurs de détection
                    self.increase_detected = False
                    self.stabilized = False
                
                # Lancer les actions finales avec un délai sans bloquer
                self.schedule_delayed_action("reset_flags", VALVE_DELAY, reset_detection_flags)
            
            # Lancer les actions après STABILITY_DURATION
            self.schedule_delayed_action("post_conductance_decrease", STABILITY_DURATION, delayed_actions_after_stability)
            return True
            
        return False
    
    def get_last_timestamps(self):
        """Obtenir les derniers horodatages pour tous les types de données"""
        return {
            'conductance': self.timeList[-1] if self.timeList else None,
            'co2': self.timestamps_co2[-1] if self.timestamps_co2 else None,
            'res_temp': self.timestamps_res_temp[-1] if self.timestamps_res_temp else None
        }
        
    def start_regeneration_protocol(self):
        """
        Start the regeneration protocol:
        1. Check for CO2 stability (±2 ppm for 2 minutes)
        2. When stable, increase temperature to 700°C for 3 minutes
        3. Return to normal operation
        
        Returns:
            bool: True if regeneration protocol was started, False if already in progress
        """
        if self.regeneration_in_progress:
            print("Regeneration protocol already in progress")
            return False
            
        # Vérifier que nous avons des lectures CO2
        if not self.values_co2:
            print("Aucune lecture CO2 disponible - impossible de démarrer le protocole de régénération")
            return False
        
        # Lire R0 avant de démarrer pour avoir une valeur initiale
        initial_R0 = self.read_R0()
        if initial_R0 is not None:
            print(f"Starting regeneration protocol - Initial R0: {initial_R0}")
            # Actualisation de R0 en l'écrivant dans les paramètres
            self.set_R0(str(initial_R0))
            print(f"R0 actualisé: {initial_R0}")
            
            # Enregistrer le timestamp de l'actualisation de R0
            current_time = time.time()
            if self.start_time_co2_temp_humidity is not None:
                self.regeneration_timestamps['r0_actualized'] = current_time - self.start_time_co2_temp_humidity - self.elapsed_time_co2_temp_humidity
            
        # Initialiser l'état de régénération
        self.regeneration_in_progress = True
        self.regeneration_step = 1  # Vérification de la stabilité du CO2
        self.co2_stability_start_time = None  # Sera défini lors de la première lecture stable
        self.regeneration_start_time = None
        self.co2_stable_value = None
        
        print("Regeneration protocol started: checking CO2 stability")
        return True
        
    def cancel_regeneration_protocol(self):
        """
        Cancel the regeneration protocol and return to normal temperature
        
        Returns:
            bool: True if regeneration was cancelled, False if not in progress
        """
        if not self.regeneration_in_progress:
            print("No regeneration protocol in progress to cancel")
            return False
            
        # Set temperature back to low value - méthode renforcée
        # 1. Utiliser d'abord la méthode interne set_Tcons
        result = self.set_Tcons(str(TCONS_LOW))
        if result:
            print(f"Paramètre Tcons remis à {TCONS_LOW}°C après annulation via set_Tcons")
        else:
            print(f"Erreur lors de la remise à {TCONS_LOW}°C après annulation via set_Tcons")
        
        # 2. Puis essayer d'écrire directement via le périphérique de régénération
        try:
            if self.regen and hasattr(self.regen, 'device') and self.regen.device:
                command_str = f"ea{TCONS_LOW}\n"
                self.regen.device.write(command_str.encode())
                print(f"Paramètre Tcons remis à {TCONS_LOW}°C après annulation via commande brute")
                
                # Force une mise à jour de la mémoire interne
                self.last_set_Tcons = float(TCONS_LOW)
        except Exception as e:
            print(f"Erreur lors de l'écriture directe pour remettre Tcons à {TCONS_LOW}°C après annulation: {e}")
        
        # Reset regeneration state
        self.regeneration_in_progress = False
        self.regeneration_step = 0
        self.co2_stability_start_time = None
        self.regeneration_start_time = None
        self.co2_stable_value = None
        
        # Reset CO2 increase detection variables
        self.co2_increase_detection_started = None
        self.co2_base_value = None
        self.co2_increase_detected = False
        
        # Reset CO2 peak and restabilization variables
        self.co2_peak_value = None
        self.co2_peak_time = None
        self.co2_peak_detected = False
        self.co2_max_slope_value = 0
        self.co2_max_slope_time = 0
        self.co2_peak_detection_started = None
        self.co2_peak_detection_value = None
        self.co2_restabilization_start_time = None
        self.co2_restabilization_reference = None
        self.co2_restabilized = False
        self.tcons_reduced = False
        
        # Reset CO2 stability shift variables
        self.co2_stability_shifted = False
        self.co2_previous_stable_value = None
        self.co2_stability_shift_count = 0
        
        # Reset regeneration timestamps
        self.regeneration_timestamps = {
            'r0_actualized': None,
            'co2_stability_started': None,
            'co2_stability_achieved': None,
            'co2_increase_detected': None,
            'co2_peak_reached': None,
            'co2_restabilization_start_time': None,
            'co2_restabilized': None
        }
        
        print("Regeneration protocol cancelled")
        return True
        
    def check_co2_stability(self):
        """
        Vérifier si les lectures CO2 sont stables (±2 ppm pendant 2 minutes)
        
        Returns:
            bool: True si le CO2 est stable pendant la durée requise, False sinon
        """
        if not self.regeneration_in_progress or self.regeneration_step != 1:
            return False
            
        # Besoin d'au moins quelques lectures
        if len(self.values_co2) < 3:
            return False
            
        current_time = time.time()
        latest_co2 = self.values_co2[-1]
        
        # Si nous n'avons pas encore de valeur de référence stable, utiliser la valeur actuelle
        if self.co2_stable_value is None:
            self.co2_stable_value = latest_co2
            self.co2_stability_start_time = current_time
            print(f"Définition de la valeur de référence CO2 initiale: {latest_co2} ppm")
            
            # Enregistrer le timestamp du début de la vérification de stabilité CO2
            if self.start_time_co2_temp_humidity is not None:
                self.regeneration_timestamps['co2_stability_started'] = current_time - self.start_time_co2_temp_humidity - self.elapsed_time_co2_temp_humidity
                
            return False
        
        # Check if the current value is within the stability threshold
        if abs(latest_co2 - self.co2_stable_value) <= CO2_STABILITY_THRESHOLD:
            # Still stable, check if we've been stable long enough
            if self.co2_stability_start_time is not None:
                stable_duration = current_time - self.co2_stability_start_time
                
                print(f"DEBUG Stabilisation initiale: Écart CO2 = {abs(latest_co2 - self.co2_stable_value):.2f} ppm, Durée stable = {stable_duration:.1f}/{CO2_STABILITY_DURATION} s")
                
                if stable_duration >= CO2_STABILITY_DURATION:
                    # Avant de confirmer la stabilité, lire R0, l'afficher et l'actualiser
                    R0 = self.read_R0()
                    if R0 is not None:
                        print(f"CO2 stable - R0 initial: {R0}")
                        # Actualisation de R0 en l'écrivant dans les paramètres
                        self.set_R0(str(R0))
                        print(f"R0 actualisé avant régénération: {R0}")
                    
                    # Enregistrer le timestamp de la stabilité CO2 atteinte
                    self.regeneration_timestamps['co2_stability_achieved'] = current_time - self.start_time_co2_temp_humidity - self.elapsed_time_co2_temp_humidity
                    return True
                else:
                    return False
        else:
            # Not stable, reset the reference
            variation = abs(latest_co2 - self.co2_stable_value)
            self.co2_stable_value = latest_co2
            self.co2_stability_start_time = current_time
            
            # Mettre à jour le marqueur de début de vérification de stabilité CO2
            # UNIQUEMENT pendant la phase 1, avant la mise en chauffage
            if self.start_time_co2_temp_humidity is not None and self.regeneration_step == 1:
                self.regeneration_timestamps['co2_stability_started'] = current_time - self.start_time_co2_temp_humidity - self.elapsed_time_co2_temp_humidity
                print(f"Marqueur de début stabilité CO2 déplacé: {latest_co2} ppm (variation de {variation:.2f} ppm > {CO2_STABILITY_THRESHOLD} ppm)")
            
            return False
            
    def check_co2_restabilization(self):
        """
        Check if CO2 readings have restabilized after the peak
        
        Returns:
            bool: True if CO2 is stable for the required duration, False otherwise
        """
        if not self.co2_peak_detected or len(self.values_co2) < 3:
            return False
            
        current_time = time.time()
        latest_co2 = self.values_co2[-1]
        
        # If we don't have a reference stabilization value yet, initialize it
        if self.co2_restabilization_reference is None:
            self.co2_restabilization_reference = latest_co2
            self.co2_restabilization_start_time = current_time
            print(f"Début de la surveillance de restabilisation CO2 à {latest_co2} ppm")
            return False
        
        # Check if the current value is within the stability threshold
        if abs(latest_co2 - self.co2_restabilization_reference) <= CO2_STABILITY_THRESHOLD:
            # Still stable, check if we've been stable long enough
            if self.co2_restabilization_start_time is not None:
                stable_duration = current_time - self.co2_restabilization_start_time
                
                print(f"DEBUG Restabilisation: Écart CO2 = {abs(latest_co2 - self.co2_restabilization_reference):.2f} ppm, Durée stable = {stable_duration:.1f}/{CO2_STABILITY_DURATION} s")
                
                if stable_duration >= CO2_STABILITY_DURATION:
                    # Stability confirmed
                    self.co2_restabilized = True
                    
                    # Record the timestamp of restabilization
                    if self.start_time_co2_temp_humidity is not None:
                        self.regeneration_timestamps['co2_restabilized'] = current_time - self.start_time_co2_temp_humidity - self.elapsed_time_co2_temp_humidity
                    
                    print(f"CO2 restabilisé à {latest_co2} ppm")
                    return True
                else:
                    # Still waiting for full stability duration
                    return False
        else:
            # Not stable, reset the reference
            variation = abs(latest_co2 - self.co2_restabilization_reference)
            self.co2_restabilization_reference = latest_co2
            self.co2_restabilization_start_time = current_time
            
            # Mettre à jour le timestamp de début de recherche de restabilisation
            if self.start_time_co2_temp_humidity is not None:
                self.regeneration_timestamps['co2_restabilization_start_time'] = current_time - self.start_time_co2_temp_humidity - self.elapsed_time_co2_temp_humidity
                
            print(f"Référence restabilisation réinitialisée: {latest_co2} ppm (variation de {variation:.2f} ppm > {CO2_STABILITY_THRESHOLD} ppm)")
            return False
            
    def regeneration_complete(self):
        """Complete the regeneration process and reset variables"""
        from core.constants import CELL_VOLUME
        
        print("Protocole de régénération terminé avec succès")
        
        # Calculer le delta C et la masse de carbone
        delta_c = 0
        carbon_mass = 0
        
        if self.co2_stable_value is not None and self.co2_restabilization_reference is not None:
            # Calculer la différence entre la valeur stable initiale et la valeur finale
            delta_c = self.co2_restabilization_reference - self.co2_stable_value
            
            # Calculer la masse de carbone en µg: mc = deltaC * volume / 24.5 * 12
            carbon_mass = delta_c * CELL_VOLUME / 24.5 * 12
            
            print(f"Delta C: {delta_c:.2f} ppm")
            print(f"Masse de carbone: {carbon_mass:.2f} µg")
        
        # Stocker les résultats pour l'affichage
        self.regeneration_results = {
            'delta_c': delta_c,
            'carbon_mass': carbon_mass
        }
        
        # Reset regeneration state
        self.regeneration_in_progress = False
        self.regeneration_step = 0
        
        # Reset all CO2 detection variables
        self.co2_increase_detected = False
        self.co2_base_value = None
        self.co2_peak_detected = False
        self.co2_peak_value = None 
        self.co2_peak_time = None
        self.co2_restabilized = False
        self.co2_restabilization_reference = None
        self.co2_restabilization_start_time = None
        self.tcons_reduced = False
            
    def manage_regeneration_protocol(self):
        """
        Gère le protocole de régénération avec les nouvelles règles :
        1. La détection de restabilisation peut commencer dès le pic détecté
        2. La température reste à 700°C jusqu'à la fin de REGENERATION_DURATION
        3. La restabilisation peut se terminer avant ou après le retour à 0°C
        """
        if not self.regeneration_in_progress:
            return {
                'active': False,
                'step': 0,
                'message': "Regeneration not active",
                'progress': 0
            }
        
        current_time = time.time()
        
        # Étape 1: Vérification stabilité CO2 initiale
        if self.regeneration_step == 1:
            if self.check_co2_stability():
                # Stabilité atteinte, passer à l'étape 2
                self.regeneration_step = 2
                self.regeneration_start_time = current_time
                self.co2_base_value = self.values_co2[-1]
                
                # Démarrage de la régénération (température à 700°C)
                self.set_Tcons(str(REGENERATION_TEMP))
                
                return {
                    'active': True,
                    'step': 2,
                    'message': f"Régénération à {REGENERATION_TEMP}°C démarrée",
                    'progress': 33.3
                }
            else:
                return {
                    'active': True,
                    'step': 1,
                    'message': "Recherche stabilité CO2 initiale...",
                    'progress': (min(current_time - self.co2_stability_start_time, CO2_STABILITY_DURATION) 
                                / CO2_STABILITY_DURATION) * 33.3
                }
        
        # Étape 2: Régénération à haute température (durée fixe)
        elif self.regeneration_step == 2:
            elapsed = current_time - self.regeneration_start_time
            regeneration_completed = elapsed >= REGENERATION_DURATION
            
            # Détection de l'augmentation CO2 (peut se faire à tout moment)
            if not self.co2_increase_detected and self.co2_base_value is not None:
                current_co2 = self.values_co2[-1]
                if current_co2 - self.co2_base_value >= 5:  # Seuil d'augmentation
                    self.co2_increase_detected = True
                    self.regeneration_timestamps['co2_increase_detected'] = current_time - self.start_time_co2_temp_humidity
                    print(f"Augmentation CO2 détectée: {current_co2 - self.co2_base_value:.1f} ppm")
            
            # Détection du pic CO2 (peut se faire à tout moment)
            if self.co2_increase_detected and not self.co2_peak_detected:
                self.detect_co2_peak()
                
                # Si pic détecté, lancer la surveillance de restabilisation IMMÉDIATEMENT
                if self.co2_peak_detected:
                    self.co2_restabilization_reference = self.values_co2[-1]
                    self.co2_restabilization_start_time = current_time
                    self.regeneration_timestamps['co2_restabilization_start_time'] = current_time - self.start_time_co2_temp_humidity
                    print(f"Pic CO2 détecté, début surveillance restabilisation à {self.co2_restabilization_reference} ppm")
            
            # Vérifier la restabilisation si le pic a été détecté
            restabilization_detected = False
            if self.co2_peak_detected:
                restabilization_detected = self.check_co2_restabilization()
            
            # Gestion de la température
            if not regeneration_completed:
                # Maintenir à 700°C jusqu'à la fin de la durée, même si restabilisation détectée
                if not self.tcons_reduced:
                    self.set_Tcons(str(REGENERATION_TEMP))
                
                progress = 33.3 + (elapsed / REGENERATION_DURATION) * 66.7 * 0.5  # Progress jusqu'à 66.6%
                
                return {
                    'active': True,
                    'step': 2,
                    'message': f"Régénération en cours ({elapsed:.1f}/{REGENERATION_DURATION}s)" + 
                            (" (restabilisation en cours)" if self.co2_peak_detected else ""),
                    'progress': min(66.6, progress)
                }
            else:
                # Durée de régénération écoulée
                if not self.tcons_reduced:
                    self.set_Tcons(str(TCONS_LOW))
                    self.tcons_reduced = True
                    print("Durée de régénération écoulée - température réduite à 0°C")
                
                if restabilization_detected:
                    # Restabilisation terminée - fin du protocole
                    self.regeneration_complete()
                    return {
                        'active': False,
                        'step': 4,
                        'message': "Régénération terminée avec succès",
                        'progress': 100
                    }
                else:
                    # Attendre la restabilisation après la fin du chauffage
                    restab_time = current_time - self.co2_restabilization_start_time if self.co2_restabilization_start_time else 0
                    progress = 75.0 + min(25.0, (restab_time / CO2_STABILITY_DURATION) * 25.0)
                    
                    return {
                        'active': True,
                        'step': 3,
                        'message': f"Attente restabilisation CO2 ({restab_time:.1f}/{CO2_STABILITY_DURATION}s)",
                        'progress': progress
                    }
        
        # Étape 3: Attente restabilisation après fin de régénération (si pas encore détectée)
        elif self.regeneration_step == 3:
            if self.check_co2_restabilization():
                self.regeneration_complete()
                return {
                    'active': False,
                    'step': 4,
                    'message': "Régénération terminée avec succès",
                    'progress': 100
                }
            else:
                restab_time = current_time - self.co2_restabilization_start_time if self.co2_restabilization_start_time else 0
                progress = 75.0 + min(25.0, (restab_time / CO2_STABILITY_DURATION) * 25.0)
                
                return {
                    'active': True,
                    'step': 3,
                    'message': f"Surveillance restabilisation CO2 ({restab_time:.1f}/{CO2_STABILITY_DURATION}s)",
                    'progress': progress
                }
        
        return {
            'active': True,
            'step': self.regeneration_step,
            'message': "État inconnu",
            'progress': 75.0
        }