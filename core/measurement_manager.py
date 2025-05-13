"""
Gestionnaire de mesures - Gère la logique de collecte et de traitement des données des capteurs
"""

import time
import numpy as np
import serial
from serial.serialutil import SerialException
import pyvisa
from core.constants import (
    INCREASE_SLOPE_MIN, INCREASE_SLOPE_MAX, STABILITY_DURATION,
    SLIDING_WINDOW, R0_THRESHOLD, REGENERATION_TEMP, TCONS_LOW, VALVE_DELAY,
    CO2_STABILITY_THRESHOLD, CO2_STABILITY_DURATION, REGENERATION_DURATION,
    CONDUCTANCE_DECREASE_THRESHOLD, CO2_INCREASE_THRESHOLD
)

class MeasurementManager:
    """Gère toutes les opérations de mesure et implémente la logique de détection des capteurs"""
    
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
        
        # Data storage for conductance measurements
        self.timeList = []
        self.conductanceList = []
        self.resistanceList = []
        
        # Data storage for CO2, temperature and humidity
        self.timestamps_co2 = []
        self.values_co2 = []
        self.timestamps_temp = []
        self.values_temp = []
        self.timestamps_humidity = []
        self.values_humidity = []
        
        # Data storage for resistance temperature
        self.timestamps_res_temp = []
        self.temperatures = []
        self.Tcons_values = []
        
        # Time tracking variables
        self.start_time_conductance = None
        self.start_time_co2_temp_humidity = None
        self.start_time_res_temp = None
        self.elapsed_time_conductance = 0
        self.elapsed_time_co2_temp_humidity = 0
        self.elapsed_time_res_temp = 0
        
        # Variables pour mémoriser le moment de pause
        self.pause_time_conductance = None
        self.pause_time_co2_temp_humidity = None
        self.pause_time_res_temp = None
        
        # State variables
        self.increase_detected = False
        self.stabilized = False
        self.increase_time = None
        self.stabilization_time = None
        self.max_slope_value = 0
        self.max_slope_time = 0
        self.sensor_state = None  # None: unknown, True: out, False: in
        self.escape_pressed = False
        self.last_set_Tcons = None  # Stocke la dernière valeur de Tcons définie
        self.first_stability_time = None  # Temps de la première stabilité dans le protocole complet
        
        # Variables pour la détection des étapes post-régénération
        self.conductance_decrease_detected = False
        self.conductance_decrease_time = None
        self.post_regen_stability_detected = False
        self.post_regen_stability_time = None
        
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
        
        # Regeneration protocol variables
        self.regeneration_in_progress = False
        self.regeneration_step = 0  # 0: not started, 1: checking CO2 stability, 2: regeneration active, 3: completed
        self.co2_stability_start_time = None
        self.regeneration_start_time = None
        self.co2_stable_value = None  # To store the reference CO2 value for stability check
        
        # Timestamps for key events in the regeneration protocol (for plotting markers)
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
        
        # Variables pour le protocole de conductance avec résistance/température
        self.conductance_regen_in_progress = False
        self.conductance_regen_start_time = None
        self.conductance_regen_target_reached = False
        self.conductance_regen_stop_time = None

        # Variables pour le protocole complet
        self.full_protocol_in_progress = False
        self.full_protocol_start_time = None
        self.full_regen_target_reached = False
        self.full_regen_stop_time = None
    
    def reset_data(self, data_type=None):
        """
        Reset stored data with proper handling for ExcelHandler
        
        Args:
            data_type: Type of data to reset, or None for all data
        """
        # Sauvegardons la dernière valeur de Tcons avant de tout réinitialiser
        last_tcons = getattr(self, 'last_set_Tcons', None)
        
        if data_type in [None, "conductance"]:
            # Save current data before resetting if we have an ExcelHandler
            if hasattr(self, 'excel_handler') and len(self.timeList) > 0:
                # This will trigger the save to Excel
                self.excel_handler.raz_conductance_data(
                    self.timeList,
                    self.conductanceList, 
                    self.resistanceList
                )
                
            # Now reset the data
            self.timeList.clear()
            self.conductanceList.clear()
            self.resistanceList.clear()
            self.start_time_conductance = None
            self.pause_time_conductance = None
            self.elapsed_time_conductance = 0
        
        if data_type in [None, "co2_temp_humidity"]:
            # Handle CO2/temp/humidity data similarly if needed
            # (Add similar code here for CO2/temp/humidity when implemented)
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
            # Handle temp_res data similarly if needed
            # (Add similar code here for temp_res when implemented)
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
            self.first_stability_time = None
            # Réinitialiser les indicateurs post-régénération
            self.conductance_decrease_detected = False
            self.conductance_decrease_time = None
            self.post_regen_stability_detected = False
            self.post_regen_stability_time = None
            
        # Restaurons la dernière valeur de Tcons
        if last_tcons is not None:
            self.last_set_Tcons = last_tcons
    
    def read_conductance(self):
        """Lit les données de conductance depuis l'appareil Keithley"""
        current_time = time.time()
        
        # Vérifier si le Keithley est disponible
        if self.keithley is None or not hasattr(self.keithley, 'device') or self.keithley.device is None:
            # Si l'erreur a déjà été signalée précédemment, ne pas la répéter
            if not hasattr(self, '_keithley_error_reported') or not self._keithley_error_reported:
                print("Warning: Attempting to read conductance but Keithley device is not available")
                self._keithley_error_reported = True
                
                # Si on avait commencé à collecter des données, mémoriser le moment de la pause
                if self.start_time_conductance is not None:
                    self.pause_time_conductance = current_time
                    
                # Marquer la déconnexion pour l'interface
                if hasattr(self, 'on_keithley_disconnected') and callable(self.on_keithley_disconnected):
                    self.on_keithley_disconnected()
            return None
        
        # Réinitialiser le marqueur d'erreur puisque l'appareil est disponible
        self._keithley_error_reported = False
        
        # Read resistance from Keithley
        try:
            # Capturer les erreurs de communication VISA spécifiques
            try:
                resistance = self.keithley.read_resistance()
                
                # Si la lecture échoue, on considère que le Keithley n'est plus disponible
                if resistance is None:
                    print("Lecture de résistance a échoué (None retourné)")
                    self.keithley.device = None
                    self._keithley_error_reported = True
                    
                    # Si on avait commencé à collecter des données, mémoriser le moment de la pause
                    if self.start_time_conductance is not None:
                        self.pause_time_conductance = current_time
                        
                    # Marquer la déconnexion pour l'interface
                    if hasattr(self, 'on_keithley_disconnected') and callable(self.on_keithley_disconnected):
                        self.on_keithley_disconnected()
                    return None
                    
                if resistance == 0.0:
                    conductance = float('inf')
                else:
                    conductance = (1 / resistance) * 1e6  # Convert to µS
                    
                # Si on arrive ici, la lecture a réussi, donc l'appareil est fonctionnel
                # Réinitialiser les compteurs d'erreur si nécessaire
                if hasattr(self, '_keithley_error_count'):
                    self._keithley_error_count = 0
                    
            except (IOError, OSError, pyvisa.errors.VisaIOError) as visa_err:
                # Erreur de communication VISA critique - l'appareil est probablement déconnecté
                if not hasattr(self, '_keithley_error_count'):
                    self._keithley_error_count = 0
                
                self._keithley_error_count += 1
                
                # N'afficher que périodiquement les erreurs pour éviter le spam
                if self._keithley_error_count % 20 == 1:
                    print(f"Error communicating with Keithley: {visa_err}")
                
                # Marquer l'appareil comme non disponible pour éviter d'autres erreurs
                self.keithley.device = None
                self._keithley_error_reported = True
                
                # Si on avait commencé à collecter des données, mémoriser le moment de la pause
                if self.start_time_conductance is not None:
                    self.pause_time_conductance = current_time
                    
                # Marquer la déconnexion pour l'interface
                if hasattr(self, 'on_keithley_disconnected') and callable(self.on_keithley_disconnected):
                    self.on_keithley_disconnected()
                return None
                
        except Exception as e:
            print(f"Error reading conductance: {e}")
            
            # Si on avait commencé à collecter des données, mémoriser le moment de la pause
            if self.start_time_conductance is not None:
                self.pause_time_conductance = current_time
                
            # Marquer la déconnexion pour l'interface si c'est une erreur qui peut indiquer une déconnexion
            if hasattr(self, 'on_keithley_disconnected') and callable(self.on_keithley_disconnected):
                self.on_keithley_disconnected()
            return None
        
        # Only initialize start_time when we actually get data to plot
        if self.start_time_conductance is None:
            self.start_time_conductance = current_time
        
        # Calculate timestamp
        timestamp = current_time - self.start_time_conductance - self.elapsed_time_conductance
        
        # Store data
        self.timeList.append(timestamp)
        self.conductanceList.append(conductance)
        self.resistanceList.append(resistance)

        # 1. Vérifier si la conductance a diminué sous le seuil après stabilisation
        if self.stabilized and not self.conductance_decrease_detected:
            self.check_reset_detection_indicators()

        # 2. Vérifier si la conductance remonte après une décroissance
        # et actualiser le temps de percolation si nécessaire
        if self.conductance_decrease_detected:
            self.check_conductance_increase_after_decrease()

        # 3. Vérifier si la conductance s'est stabilisée après une décroissance
        if self.conductance_decrease_detected and not self.post_regen_stability_detected:
            self.detect_post_regen_stability()

        return {
            'timestamp': timestamp,
            'conductance': conductance,
            'resistance': resistance
        }
    
    def read_arduino_status_only(self):
        """
        Read pin states from Arduino without storing CO2/temperature/humidity data
        Returns: True if pin states were updated, False otherwise
        """
        line = self.arduino.read_line()
        
        # Check for sensor status messages (VR, VS, TO, TF pins)
        if line and "VR:" in line and "VS:" in line and "TO:" in line and "TF:" in line:
            try:
                # Parse individual pin states
                vr_part = line.split("VR:")[1].split()[0]
                vs_part = line.split("VS:")[1].split()[0]
                to_part = line.split("TO:")[1].split()[0]
                tf_part = line.split("TF:")[1].split()[0]
                
                # Clarify status parsing (HIGH = True, LOW = False)
                vr_state = vr_part == "HIGH"
                vs_state = vs_part == "HIGH"
                to_state = to_part == "HIGH"
                tf_state = tf_part == "HIGH"
                
                # Print status for debugging
                print(f"Pin states: VR={vr_state}, VS={vs_state}, TO={to_state}, TF={tf_state}")
                
                # Store the pin states for UI updating
                self.pin_states = {
                    'vr': vr_state,  # Vérin Rentré
                    'vs': vs_state,  # Vérin Sorti
                    'to': to_state,  # Trappe Ouverte
                    'tf': tf_state   # Trappe Fermée
                }
                return True
            except Exception as e:
                print(f"Error parsing pin states: {e}, line: {line}")
                return False
        
        # Ignorer les données CO2/temp/humidity si la ligne commence par @
        if line and line.startswith('@'):
            return True  # Juste pour indiquer qu'une ligne a été traitée
            
        return False  # Aucune ligne valide
    
    def read_arduino_data(self):
        """
        Read CO2, temperature, humidity data from Arduino and store it
        Only called when measurements are active
        """
        current_time = time.time()
        
        # Vérifier si l'Arduino est disponible
        if not hasattr(self.arduino, 'read_line') or self.arduino.device is None:
            return None
        
        # Initialize start_time only when first data point is collected
        # instead of when the function is first called
        line = self.arduino.read_line()
        
        # Si pas de ligne, c'est peut-être un Arduino simulé ou pas de données
        if not line:
            return None
        
        # Handle pin state updates if they come through
        if line and "VR:" in line and "VS:" in line and "TO:" in line and "TF:" in line:
            try:
                # Parse individual pin states
                vr_part = line.split("VR:")[1].split()[0]
                vs_part = line.split("VS:")[1].split()[0]
                to_part = line.split("TO:")[1].split()[0]
                tf_part = line.split("TF:")[1].split()[0]
                
                # Clarify status parsing (HIGH = True, LOW = False)
                vr_state = vr_part == "HIGH"
                vs_state = vs_part == "HIGH"
                to_state = to_part == "HIGH"
                tf_state = tf_part == "HIGH"
                
                # Store the pin states for UI updating
                self.pin_states = {
                    'vr': vr_state,  # Vérin Rentré
                    'vs': vs_state,  # Vérin Sorti
                    'to': to_state,  # Trappe Ouverte
                    'tf': tf_state   # Trappe Fermée
                }
            except Exception as e:
                print(f"Error parsing pin states: {e}, line: {line}")
            
            return None  # No CO2 data in this message
        
        if not line.startswith('@'):
            return None
        
        data = line[1:].split()
        if len(data) != 3:
            return None
        
        # Parse data
        try:
            co2 = float(data[0])
            temperature = float(data[1])
            humidity = float(data[2])
        except ValueError:
            return None
        
        # Only initialize start_time when we actually get data to plot
        if self.start_time_co2_temp_humidity is None:
            self.start_time_co2_temp_humidity = current_time
        
        # Calculate timestamp
        timestamp = current_time - self.start_time_co2_temp_humidity - self.elapsed_time_co2_temp_humidity
        
        # Store data
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
        """Read resistance temperature data"""
        current_time = time.time()
        
        # Vérifier si le dispositif de régénération est disponible
        if self.regen is None or not hasattr(self.regen, 'device') or self.regen.device is None:
            # Si l'erreur a déjà été signalée précédemment, ne pas la répéter
            if not hasattr(self, '_regen_error_reported') or not self._regen_error_reported:
                print("Warning: Attempting to read res_temp but regeneration device is not available")
                self._regen_error_reported = True
            return None
        
        # Réinitialiser le marqueur d'erreur puisque l'appareil est disponible
        self._regen_error_reported = False
        
        try:
            # Capturer toutes les erreurs possibles lors de la communication série
            try:
                # Vérifier que le device est toujours valide avant lecture
                if not self.regen.device or not hasattr(self.regen.device, 'is_open') or not self.regen.device.is_open:
                    print("Device disconnected before reading Tcons")
                    self.regen.device = None
                    self._regen_error_reported = True
                    return None
                    
                raw_tcons = self.regen.read_variable('L', 'a')
                
                # Vérifier encore une fois que le device est valide
                if not self.regen.device or not hasattr(self.regen.device, 'is_open') or not self.regen.device.is_open:
                    print("Device disconnected after reading Tcons")
                    self.regen.device = None
                    self._regen_error_reported = True
                    return None
                
                Tcons_value = float(raw_tcons)
                
                # On teste la deuxième lecture séparément pour isoler les erreurs
                temperature_value = float(self.regen.read_variable('L', 'd'))
                
                # Si on arrive ici, les deux lectures ont réussi, donc l'appareil est fonctionnel
                # Réinitialiser le compteur d'erreurs puisque les lectures ont réussi
                if hasattr(self, '_serial_error_count'):
                    self._serial_error_count = 0
                
                # Utilisation systématique de la dernière valeur définie pour Tcons
                # plutôt que de faire confiance à la valeur retournée par l'appareil
                if hasattr(self, 'last_set_Tcons') and self.last_set_Tcons is not None:
                    # Si la dernière valeur définie est différente, on l'utilise
                    if abs(Tcons_value - self.last_set_Tcons) > 50:  # Différence significative
                        Tcons_value = self.last_set_Tcons
                
            except (OSError, IOError, serial.SerialException, PermissionError) as serial_err:
                # Erreur de communication série critique - l'appareil est probablement déconnecté
                # On la gère ici pour éviter de spammer la console
                if not hasattr(self, '_serial_error_count'):
                    self._serial_error_count = 0
                
                self._serial_error_count += 1
                
                # N'afficher que périodiquement les erreurs pour éviter le spam
                if self._serial_error_count % 20 == 1:
                    print(f"Error reading from regeneration device: {serial_err}")
                
                # Marquer l'appareil comme non disponible pour éviter d'autres erreurs
                if hasattr(self.regen, 'device') and self.regen.device:
                    try:
                        # Tenter une fermeture propre
                        self.regen.close()
                    except:
                        pass  # Ignorer les erreurs lors de la fermeture
                
                self.regen.device = None
                self._regen_error_reported = True
                return None
                
        except (ValueError, TypeError) as e:
            # Erreur de conversion des données
            print(f"Error processing temperature data: {e}, raw_tcons={raw_tcons if 'raw_tcons' in locals() else 'N/A'}")
            return None
        
        # Only initialize start_time when we actually get data to plot
        if self.start_time_res_temp is None:
            self.start_time_res_temp = current_time
        
        # Calculate timestamp
        timestamp = current_time - self.start_time_res_temp - self.elapsed_time_res_temp
        
        # Store data
        self.timestamps_res_temp.append(timestamp)
        self.temperatures.append(temperature_value)
        self.Tcons_values.append(Tcons_value)
        
        return {
            'timestamp': timestamp,
            'temperature': temperature_value,
            'Tcons': Tcons_value
        }
    
    def push_open_sensor(self):
        """Push/open the sensor"""
        # Vérifier si l'Arduino est disponible
        if not hasattr(self.arduino, 'send_command') or self.arduino.device is None:
            print("Warning: Attempting to push/open sensor but Arduino is not available")
            return False
            
        self.arduino.send_command("ouvrir\n")
        self.sensor_state = True
        return True
        
    def retract_close_sensor(self):
        """Retract/close the sensor"""
        # Vérifier si l'Arduino est disponible
        if not hasattr(self.arduino, 'send_command') or self.arduino.device is None:
            print("Warning: Attempting to retract/close sensor but Arduino is not available")
            return False
            
        self.arduino.send_command("fermer\n")
        self.sensor_state = False
        return True
        
    def init_system(self):
        """Initialize the system"""
        # Vérifier si l'Arduino est disponible
        if not hasattr(self.arduino, 'send_command') or self.arduino.device is None:
            print("Warning: Attempting to initialize system but Arduino is not available")
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
        
        # Vérifier que le port est ouvert
        if not hasattr(self.regen.device, 'is_open') or not self.regen.device.is_open:
            print("Warning: Serial port is closed, cannot set Tcons")
            self.regen.device = None
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
                if self.regen.device and hasattr(self.regen.device, 'is_open') and self.regen.device.is_open:
                    command_str = f"ea{value}\n"
                    self.regen.device.write(command_str.encode())
                    
                    # Si l'opération a réussi, réinitialiser le compteur d'erreurs
                    if hasattr(self, '_serial_error_count'):
                        self._serial_error_count = 0
                        
                    return True  # Nous considérons que cette méthode fonctionne même si write_parameter échoue
                else:
                    print("Warning: Device not open when attempting direct write")
                    self.regen.device = None
                    return False
            except (OSError, IOError, SerialException, PermissionError) as e:
                print(f"Erreur lors de l'écriture directe de Tcons: {e}")
                # Marquer l'appareil comme non disponible
                if hasattr(self.regen, 'device') and self.regen.device:
                    try:
                        # Tenter une fermeture propre
                        self.regen.close()
                    except:
                        pass  # Ignorer les erreurs lors de la fermeture
                
                self.regen.device = None
                return False
            except Exception as e:
                print(f"Erreur inattendue lors de l'écriture directe de Tcons: {e}")
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
            
        # Vérifier que le port est ouvert
        if not hasattr(self.regen.device, 'is_open') or not self.regen.device.is_open:
            print(f"Warning: Serial port is closed, cannot read R0. Port: {self.regen.port}")
            self.regen.device = None
            return None
            
        try:
            # La méthode read_variable retourne maintenant toujours une chaîne, jamais None
            R = self.regen.read_variable('L', 'c')
            
            # Vérification de sécurité supplémentaire
            if not isinstance(R, str):
                print(f"Warning: R0 reading returned non-string type: {type(R)}")
                return None
                
            try:
                # Tenter de faire le split avec gestion d'erreur
                if 'c' in R:
                    parts = R.split('c')
                    if len(parts) > 1:
                        try:
                            value = float(parts[1])
                            # Réinitialiser le compteur d'erreurs si la lecture réussit
                            if hasattr(self, '_serial_error_count'):
                                self._serial_error_count = 0
                            return value
                        except ValueError:
                            print(f"Error converting R0: '{parts[1]}' is not a valid float")
                else:
                    # Essayer de convertir directement si le format attendu n'est pas présent
                    try:
                        value = float(R)
                        # Réinitialiser le compteur d'erreurs si la lecture réussit
                        if hasattr(self, '_serial_error_count'):
                            self._serial_error_count = 0
                        return value
                    except ValueError:
                        print(f"Error converting direct R0 value: '{R}' is not a valid float")
            except Exception as e:
                print(f"Unexpected error processing R0 value '{R}': {e}")
                
        except (OSError, IOError, SerialException, PermissionError) as e:
            print(f"Error reading R0: {e}")
            
            # Marquer l'appareil comme non disponible
            if hasattr(self.regen, 'device') and self.regen.device:
                try:
                    # Tenter une fermeture propre
                    self.regen.close()
                except:
                    pass  # Ignorer les erreurs lors de la fermeture
            
            self.regen.device = None
            return None
            
        return None
    
    def detect_increase(self):
        """
        Detect increase in conductance
        Returns: True if increase detected, False otherwise
        """
        if self.increase_detected or len(self.conductanceList) < 10:
            return False
        
        # Calculate slope over last 10 points
        time_window = self.timeList[-10:]
        conductance_window = self.conductanceList[-10:]
        slope = np.polyfit(time_window, conductance_window, 1)[0]  # slope in S/s
        
        if INCREASE_SLOPE_MIN <= slope <= INCREASE_SLOPE_MAX:
            self.increase_detected = True
            self.max_slope_value = slope
            self.max_slope_time = self.timeList[-1]
            
            # Update increase_time only if it's not already set
            # Pour garder T perco de la première détection et ne pas le réinitialiser
            if self.increase_time is None:
                self.increase_time = self.timeList[-1]
                print(f"Time {self.timeList[-1]/60:.1f} min: Increase detected! Slope = {slope:.2f} µS/s")
            else:
                print(f"Time {self.timeList[-1]/60:.1f} min: Increase detected again! Slope = {slope:.2f} µS/s (T perco preserved: {self.increase_time/60:.1f} min)")
            
            return True
        
        return False
    
    def detect_stabilization(self):
        """
        Detect stabilization in conductance
        Returns: True if stabilization detected, False otherwise
        """
        if not self.increase_detected or self.stabilized or len(self.timeList) < 10:
            return False
        
        current_time = self.timeList[-1]
        
        # Find indices for sliding window
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
                
                # Update maximum slope if needed
                if current_slope > self.max_slope_value:
                    self.max_slope_value = current_slope
                    self.max_slope_time = current_time
                
                # Check if stabilized
                if (current_time - self.max_slope_time >= STABILITY_DURATION and 
                    abs(current_slope) < INCREASE_SLOPE_MIN/2):
                    self.stabilized = True
                    self.stabilization_time = current_time
                    print(f"Time {current_time/60:.1f} min: Stabilization detected! Last slope = {current_slope:.4f} µS/s")
                    return True
        
        return False
        
    def detect_co2_peak(self):
        """
        Detect CO2 peak after an increase was detected
        
        Returns:
            None: Updates self.co2_peak_detected flag if a peak is detected
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
        et réinitialise les indicateurs de détection (mais pas le temps de percolation)
        
        Returns: True si les indicateurs ont été réinitialisés, False sinon
        """
        # Ne vérifie que si stabilisation a été détectée et qu'il y a des mesures
        if not self.stabilized or len(self.conductanceList) < 1:
            return False
            
        # Vérifie si la conductance actuelle est inférieure à 5 µS
        current_conductance = self.conductanceList[-1]
        if current_conductance < CONDUCTANCE_DECREASE_THRESHOLD:
            # Marquer la détection de la décroissance (nouveau)
            if not self.conductance_decrease_detected:
                self.conductance_decrease_detected = True
                self.conductance_decrease_time = self.timeList[-1]
                print(f"Temps {self.timeList[-1]/60:.1f} min: Décroissance détectée - Conductance sous 5 µS ({current_conductance:.2f} µS)")
            
            # Réinitialise seulement les indicateurs de détection, pas le temps de percolation
            old_increase_time = self.increase_time  # Mémoriser le temps de percolation actuel
            self.increase_detected = False
            self.stabilized = False
            # Ne pas réinitialiser le temps de percolation: self.increase_time reste inchangé
            print(f"Conductance redescendue à {current_conductance:.2f} µS - Indicateurs réinitialisés (T perco conservé)")
            return True
            
        return False
        
    def check_conductance_increase_after_decrease(self):
        """
        Vérifie si la conductance remonte après être descendue sous 5 µS.
        Si oui, actualise l'indicateur de début d'augmentation (T perco).

        Returns: True si une remontée est détectée et l'indicateur actualisé, False sinon
        """
        # Ne vérifie que si la conductance a été détectée comme ayant diminué et qu'il y a assez de mesures
        if not self.conductance_decrease_detected or len(self.conductanceList) < 10:
            return False

        # Calcule la pente sur les 10 derniers points pour détecter une augmentation
        time_window = self.timeList[-10:]
        conductance_window = self.conductanceList[-10:]
        slope = np.polyfit(time_window, conductance_window, 1)[0]  # pente en S/s

        # Vérifie si la pente indique une augmentation significative
        if INCREASE_SLOPE_MIN <= slope <= INCREASE_SLOPE_MAX:
            # Actualise l'indicateur de début d'augmentation
            self.increase_time = self.timeList[-1]
            self.increase_detected = True
            self.stabilized = False  # Réinitialiser pour pouvoir détecter une nouvelle stabilisation
            self.stabilization_time = None
            self.conductance_decrease_detected = False  # Réinitialise le marqueur de diminution
            self.post_regen_stability_detected = False  # Réinitialiser aussi le marqueur de stabilisation post-régén

            print(f"Temps {self.timeList[-1]/60:.1f} min: Nouvelle augmentation détectée après diminution - Pente = {slope:.2f} µS/s")
            print(f"Indicateur T perco actualisé à {self.increase_time/60:.1f} min")

            return True

        return False
        
    def detect_post_regen_stability(self):
        """
        Détecte la restabilisation après une chute de conductance post-régénération
        Returns: True si restabilisation détectée, False sinon
        """
        # Vérifie seulement si décroissance a été détectée mais pas encore restabilisé
        if not self.conductance_decrease_detected or self.post_regen_stability_detected or len(self.timeList) < 15:
            return False
            
        current_time = self.timeList[-1]
        
        # Calculer la pente sur les 10 derniers points pour vérifier la stabilité
        time_window = self.timeList[-10:]
        conductance_window = self.conductanceList[-10:]
        current_slope = np.polyfit(time_window, conductance_window, 1)[0]
        
        # Vérifier si la conductance s'est stabilisée après la chute
        # La pente est proche de zéro et le temps écoulé depuis la décroissance est significatif
        if abs(current_slope) < INCREASE_SLOPE_MIN/3 and current_time - self.conductance_decrease_time >= STABILITY_DURATION:
            self.post_regen_stability_detected = True
            self.post_regen_stability_time = current_time
            print(f"Temps {current_time/60:.1f} min: Restabilisation post-régénération détectée! Pente = {current_slope:.4f} µS/s")
            return True
            
        return False
    
    def automatic_mode_handler(self):
        """
        Handle automatic mode logic
        Returns: True if action was taken, False otherwise
        """
        # Check for increase in conductance
        if self.detect_increase():
            return True
            
        # Check for stabilization
        if self.detect_stabilization():
            # Close valve after stabilization
            self.retract_close_sensor()
            print("Auto: Closing valve")
            time.sleep(VALVE_DELAY)
            
            # Read and update R0
            R0 = self.read_R0()
            if R0 is not None and R0 < R0_THRESHOLD:
                # Actualiser R0 en l'écrivant dans les paramètres
                self.set_R0(str(R0))
                print(f"Auto: R0 updated to {R0}")
                
                # Vérifier la stabilité du CO2 avant d'augmenter la température
                if len(self.values_co2) >= 3:
                    # Initialisation de la vérification de stabilité
                    co2_stable = False
                    co2_stable_start_time = time.time()
                    co2_reference = self.values_co2[-1]
                    print(f"Auto: Vérification de la stabilité du CO2 avant régénération (valeur initiale: {co2_reference} ppm)")
                    
                    # Boucle de vérification de la stabilité
                    while not co2_stable:
                        # Vérifier si de nouvelles données CO2 sont disponibles
                        self.read_arduino_data()
                        if len(self.values_co2) > 0:
                            current_co2 = self.values_co2[-1]
                            current_time = time.time()
                            
                            # Vérifier si le CO2 est stable
                            if abs(current_co2 - co2_reference) <= CO2_STABILITY_THRESHOLD:
                                # Stable, vérifier la durée
                                if current_time - co2_stable_start_time >= CO2_STABILITY_DURATION:
                                    co2_stable = True
                                    print(f"Auto: CO2 stable pendant {CO2_STABILITY_DURATION} secondes, lancement chauffage")
                            else:
                                # Non stable, réinitialiser la référence
                                print(f"Auto: CO2 instable, nouvelle référence: {current_co2} ppm")
                                co2_reference = current_co2
                                co2_stable_start_time = current_time
                                
                        # Petite pause pour éviter de surcharger le processeur
                        time.sleep(0.5)
                        
                        # Vérifier si le temps d'attente est trop long (3 minutes max)
                        if time.time() - co2_stable_start_time > 3*60 and not co2_stable:
                            print("Auto: Délai d'attente pour stabilité CO2 dépassé, continuation du processus")
                            break
                
                # Une fois la stabilité CO2 vérifiée, lancer la régénération
                print("Auto: Démarrage de la régénération - chauffage à haute température")
                success = self.set_Tcons(str(REGENERATION_TEMP))
                if not success:
                    print(f"Auto: Erreur lors de la définition de Tcons à {REGENERATION_TEMP}°C")
                
                # Ajouter une sécurité pour le temps de régénération
                regeneration_start_time = time.time()
                regen_completed = False
                
                # Surveiller la conductance pendant la régénération
                while not regen_completed and (time.time() - regeneration_start_time) < 3*60:
                    # Lire la conductance actuelle
                    conductance_data = self.read_conductance()
                    if conductance_data and len(self.conductanceList) > 0:
                        current_conductance = self.conductanceList[-1]
                        
                        # Vérifier si la conductance est descendue sous 1 µS
                        if current_conductance <= 5e-6:
                            print(f"Auto: Régénération terminée - Conductance inférieure à 1 µS ({current_conductance*1e6:.6f} µS)")
                            regen_completed = True
                            break
                    
                    # Petite pause pour éviter de surcharger le processeur
                    time.sleep(0.5)
                
                # Si le temps maximum de régénération est atteint sans que la conductance ne descende assez
                if not regen_completed:
                    print("Auto: Temps maximum de régénération atteint (3 min) - Arrêt forcé")
                
                # Dans tous les cas, remettre Tcons à basse température
                success = self.set_Tcons(str(TCONS_LOW))
                if not success:
                    print(f"Auto: Erreur lors de la définition de Tcons à {TCONS_LOW}°C")
                
            elif R0 is not None and R0 == 1000:
                print("Error - R0 not detected")
            else:
                print("Auto: Error - R0 too high (> 12)")
            
            return True
            
        # Check if conductance has returned to 0 after stabilization
        if self.stabilized and len(self.conductanceList) > 0 and self.conductanceList[-1] <= 5e-6:
            print(f"Auto: Conductance decreased below 1 µS ({self.conductanceList[-1]*1e6:.2f} µS)")
            
            # Set Tcons to low temperature if not already done
            success = self.set_Tcons(str(TCONS_LOW))
            if not success:
                print(f"Auto: Erreur lors de la définition de Tcons à {TCONS_LOW}°C")
            
            time.sleep(STABILITY_DURATION)
            
            print("Auto: Cycle completed. Ready for next cycle.")
            
            # Open valve
            self.push_open_sensor()
            print("Auto: Opening valve")
            time.sleep(VALVE_DELAY)
            
            # Reset detection flags
            self.increase_detected = False
            self.stabilized = False
            
            return True
            
        return False
    
    def get_last_timestamps(self):
        """Get the latest timestamps for all data types"""
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
            
        # Verify we have CO2 readings
        if not self.values_co2:
            print("No CO2 readings available - can't start regeneration protocol")
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
            
        # Initialize regeneration state
        self.regeneration_in_progress = True
        self.regeneration_step = 1  # Checking CO2 stability
        self.co2_stability_start_time = None  # Will be set when first stable reading is found
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
        
        # Arrêter aussi le protocole complet si actif
        if self.full_protocol_in_progress:
            self.full_protocol_in_progress = False
            self.full_protocol_step = 0
            print("Protocole complet également annulé")
        
        print("Regeneration protocol cancelled")
        return True
        
    def cancel_full_protocol(self):
        """
        Annule le protocole complet en cours
        
        Returns:
            bool: True si l'annulation a réussi, False si aucun protocole n'est en cours
        """
        if not self.full_protocol_in_progress:
            print("Aucun protocole complet actif à annuler")
            return False
            
        # Arrêter le protocole
        self.full_protocol_in_progress = False
        self.full_protocol_step = 0
        print("Protocole complet annulé par l'utilisateur")
        
        # Réinitialiser la température à 0°C par sécurité
        result = self.set_Tcons(str(TCONS_LOW))
        if result:
            print(f"Paramètre Tcons remis à {TCONS_LOW}°C après annulation du protocole complet")
        else:
            print(f"Erreur lors de la remise à {TCONS_LOW}°C après annulation du protocole complet")
        
        # Mettre à jour la dernière valeur définie pour Tcons
        self.last_set_Tcons = float(TCONS_LOW)
        
        return True
        
    def check_co2_stability(self):
        """
        Check if CO2 readings are stable (±2 ppm for 2 minutes)
        
        Returns:
            bool: True if CO2 is stable for the required duration, False otherwise
        """
        if not self.regeneration_in_progress or self.regeneration_step != 1:
            return False
            
        # Need at least a few readings
        if len(self.values_co2) < 3:
            return False
            
        current_time = time.time()
        latest_co2 = self.values_co2[-1]
        
        # If we don't have a reference stable value yet, use the current value
        if self.co2_stable_value is None:
            self.co2_stable_value = latest_co2
            self.co2_stability_start_time = current_time
            print(f"Setting initial CO2 reference value: {latest_co2} ppm")
            
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
        
        # Le temps de percolation est simplement le moment où l'augmentation commence
        percolation_time = 0
        if self.increase_time is not None:
            percolation_time = self.increase_time
            print(f"Temps de percolation: {percolation_time:.1f} s")
        
        # Stocker les résultats pour l'affichage
        self.regeneration_results = {
            'delta_c': delta_c,
            'carbon_mass': carbon_mass,
            'percolation_time': percolation_time,
            'first_stability_time': self.first_stability_time  # Ajouter la première stabilité
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
            
    def start_conductance_regen_protocol(self):
        """
        Démarre le protocole de conductance avec résistance/température:
        1. Lance la régénération à 700°C
        2. Surveille la résistance jusqu'à ce qu'elle dépasse 1 MΩ
        3. Arrête la régénération quand la résistance > 1 MΩ est atteinte
        
        Returns:
            bool: True si le protocole a été démarré, False si déjà en cours
        """
        if self.conductance_regen_in_progress:
            print("Protocole de conductance résistance/température déjà en cours")
            return False
        
        # S'assurer que l'appareil de régénération est disponible
        if self.regen is None or not hasattr(self.regen, 'device') or self.regen.device is None:
            print("Appareil de régénération non disponible - impossible de démarrer le protocole")
            return False
        
        # S'assurer que le Keithley est disponible pour mesurer la résistance
        if self.keithley is None or not hasattr(self.keithley, 'device') or self.keithley.device is None:
            print("Keithley non disponible - impossible de démarrer le protocole")
            return False
        
        # Initialiser les variables du protocole
        self.conductance_regen_in_progress = True
        self.conductance_regen_start_time = time.time()
        self.conductance_regen_target_reached = False
        self.conductance_regen_stop_time = None
        
        # Démarrer la régénération (température à 700°C)
        success = self.set_Tcons(str(REGENERATION_TEMP))
        if not success:
            print(f"Erreur lors de la définition de Tcons à {REGENERATION_TEMP}°C")
            self.conductance_regen_in_progress = False
            return False
        
        print(f"Protocole de conductance résistance/température démarré (chauffage à {REGENERATION_TEMP}°C)")
        return True
    
    def cancel_conductance_regen_protocol(self):
        """
        Annuler le protocole de conductance résistance/température
        
        Returns:
            bool: True si le protocole a été annulé, False sinon
        """
        if not self.conductance_regen_in_progress:
            print("Aucun protocole de conductance résistance/température en cours")
            return False
        
        # Arrêter le chauffage
        self.set_Tcons(str(TCONS_LOW))
        print(f"Température remise à {TCONS_LOW}°C")
        
        # Réinitialiser les variables
        self.conductance_regen_in_progress = False
        self.conductance_regen_start_time = None
        self.conductance_regen_target_reached = False
        self.conductance_regen_stop_time = None
        
        print("Protocole de conductance résistance/température annulé")
        return True
    
    def manage_conductance_regen_protocol(self):
        """
        Gère le protocole de conductance avec résistance/température:
        Surveille la résistance et arrête la régénération quand elle dépasse 1 MΩ
        
        Returns:
            dict: État actuel du protocole
        """
        # Vérifier si la conductance remonte après être descendue sous 5µS
        # Cette vérification est faite indépendamment de l'état du protocole
        # pour suivre les remontées en mode manuel
        self.check_conductance_increase_after_decrease()
        
        if not self.conductance_regen_in_progress:
            return {
                'active': False,
                'step': 0,
                'message': "Protocole non actif",
                'progress': 0
            }
        
        current_time = time.time()
        
        # Si la cible est déjà atteinte
        if self.conductance_regen_target_reached:
            elapsed = current_time - self.conductance_regen_stop_time
            
            # Afficher le temps écoulé depuis l'arrêt
            return {
                'active': True,
                'step': 2,
                'message': f"Résistance > 1 MΩ atteinte! (arrêté depuis {elapsed:.1f}s)",
                'progress': 100
            }
        
        # Vérifier si la résistance a dépassé 1 MΩ
        if len(self.resistanceList) > 0:
            current_resistance = self.resistanceList[-1]
            
            # Si résistance > 1 MΩ (1 000 000 Ω)
            if current_resistance > 1000000:
                # La cible est atteinte, arrêter le chauffage
                self.conductance_regen_target_reached = True
                self.conductance_regen_stop_time = current_time
                self.set_Tcons(str(TCONS_LOW))
                
                print(f"Résistance cible atteinte: {current_resistance:.0f} Ω > 1 MΩ")
                print(f"Chauffage arrêté, température réduite à {TCONS_LOW}°C")
                
                return {
                    'active': True,
                    'step': 2,
                    'message': f"Résistance > 1 MΩ atteinte! ({current_resistance/1000000:.2f} MΩ)",
                    'progress': 100
                }
            
            # Sinon, continuer le chauffage et afficher la progression
            elapsed = current_time - self.conductance_regen_start_time
            
            # Estimer la progression (basée sur la résistance)
            # Progression de 0 à 90% basée sur la résistance
            progress = min(90, (current_resistance / 1000000) * 90)
            
            return {
                'active': True,
                'step': 1,
                'message': f"Chauffage en cours: {current_resistance/1000:.1f} kΩ (cible: 1000 kΩ)",
                'progress': progress
            }
        
        # Si aucune mesure de résistance n'est disponible
        elapsed = current_time - self.conductance_regen_start_time
        return {
            'active': True,
            'step': 1,
            'message': f"Chauffage en cours... ({elapsed:.1f}s)",
            'progress': 10  # Valeur de progression arbitraire quand aucune donnée n'est disponible
        }
    
    def start_full_protocol(self):
        """
        Démarre le protocole complet, qui combine plusieurs opérations en séquence:
        1. Rétracte le vérin (ferme)
        2. Vérifie la stabilité du CO2
        3. Augmente Tcons à 700°C
        4. Attend que la conductance descende sous 5µS
        5. Remet Tcons à 0°C
        6. Attend la restabilisation du CO2
        7. Calcule delta C et masse de carbone
        
        Ce protocole est particulièrement destiné à être utilisé sur BANCO après un feu.
        
        Returns:
            bool: True si le protocole a démarré, False si déjà en cours
        """
        if self.full_protocol_in_progress:
            print("Full protocol already in progress")
            return False

        # Initialize protocol variables
        self.full_protocol_in_progress = True
        self.full_protocol_step = 1
        self.full_protocol_start_time = time.time()
        self.full_protocol_substep = 0
        self.full_protocol_substep_start_time = None
        
        # Initial values for calculations
        self.full_protocol_co2_initial = None
        self.full_protocol_co2_final = None

        # Send retract command but don't wait
        self.retract_close_sensor()
        print("Full protocol started - Step 1: Retracting sensor")

        return True

    def manage_full_protocol(self):
        """
        Gère les différentes étapes du protocole complet.

        Returns:
            dict: État actuel du protocole complet
                'active': bool - True si le protocole est en cours
                'step': int - Étape actuelle (1-7)
                'message': str - Message d'état
                'progress': float - Progression (0-100)
                'protocol_type': str - Toujours "full" pour identifier ce protocole
        """
        if not self.full_protocol_in_progress:
            return {
                'active': False,
                'step': 0,
                'message': "Protocole complet non actif",
                'progress': 0,
                'protocol_type': 'full'
            }

        current_time = time.time()
        total_steps = 6  # Nombre total d'étapes
        progress_per_step = 100 / total_steps
        
        try:
            # Étape 1: Rétraction du vérin
            if self.full_protocol_step == 1:
                if current_time - self.full_protocol_start_time > VALVE_DELAY:
                    self.full_protocol_step = 2
                    self.full_protocol_substep = 0
                    self.full_protocol_substep_start_time = current_time
                    print("Passage à l'étape 2: Vérification CO2")
                
                return {
                    'active': True,
                    'step': 1,
                    'message': "Vérin rétracté...",
                    'progress': progress_per_step * 1,
                    'protocol_type': 'full'
                }

            # Étape 2: Vérification CO2
            elif self.full_protocol_step == 2:
                # Étape 2: Vérifier la stabilité du CO2
                if self.full_protocol_substep == 0:
                    # Initialisation de la vérification
                    self.co2_stable_value = self.values_co2[-1] if len(self.values_co2) > 0 else None
                    self.co2_stability_start_time = current_time
                    self.full_protocol_substep = 1
                    print(f"Démarrage de la vérification de stabilité CO2 - Valeur de référence: {self.co2_stable_value}")
                    
                    # Enregistrer le timestamp du début de la vérification
                    if self.start_time_co2_temp_humidity is not None:
                        self.regeneration_timestamps['co2_stability_started'] = current_time - self.start_time_co2_temp_humidity - self.elapsed_time_co2_temp_humidity
                
                elif self.full_protocol_substep == 1:
                    # Vérification en cours
                    if len(self.values_co2) > 0:
                        latest_co2 = self.values_co2[-1]
                        print(f"Vérification CO2: valeur courante = {latest_co2} ppm, référence = {self.co2_stable_value} ppm")
                        
                        # Si nous avons une valeur de référence, vérifier la stabilité
                        if self.co2_stable_value is not None:
                            if abs(latest_co2 - self.co2_stable_value) <= CO2_STABILITY_THRESHOLD:
                                # Toujours stable, vérifier la durée
                                elapsed = current_time - self.co2_stability_start_time
                                stability_progress = min(100, (elapsed / CO2_STABILITY_DURATION) * 100)
                                
                                print(f"CO2 stable depuis {elapsed:.1f}s (seuil: {CO2_STABILITY_DURATION}s)")
                                
                                if elapsed >= CO2_STABILITY_DURATION:
                                    # CO2 stabilisé, passer à l'étape suivante
                                    self.full_protocol_step = 3
                                    self.full_protocol_substep = 0  # Réinitialiser la sous-étape pour l'étape 3
                                    self.full_protocol_co2_initial = latest_co2  # Mémoriser la valeur CO2 initiale
                                    print(f"CO2 stable à {latest_co2} ppm, passage à l'étape 3")

                                    # Lire et actualiser R0 avant de passer à l'étape de chauffage
                                    R0 = self.read_R0()
                                    if R0 is not None:
                                        self.set_R0(str(R0))
                                        print(f"R0 actualisé avant régénération: {R0}")

                                        # Enregistrer le timestamp pour R0 actualisé
                                        if self.start_time_co2_temp_humidity is not None:
                                            self.regeneration_timestamps['r0_actualized'] = current_time - self.start_time_co2_temp_humidity - self.elapsed_time_co2_temp_humidity

                                        # Enregistrer le timestamp pour CO2 stabilisé
                                        if self.start_time_co2_temp_humidity is not None:
                                            self.regeneration_timestamps['co2_stability_achieved'] = current_time - self.start_time_co2_temp_humidity - self.elapsed_time_co2_temp_humidity

                                        # Enregistrer le timestamp pour la première stabilité
                                        if self.start_time_conductance is not None:
                                            self.first_stability_time = current_time - self.start_time_conductance - self.elapsed_time_conductance
                                            print(f"Première stabilité atteinte à {self.first_stability_time:.1f}s")
                                
                                return {
                                    'active': True,
                                    'step': 2,
                                    'message': f"Vérification stabilité CO2 ({stability_progress:.0f}%)",
                                    'progress': progress_per_step + (stability_progress / 100) * progress_per_step,
                                    'protocol_type': 'full'
                                }
                            else:
                                # CO2 a changé, réinitialiser la référence
                                variation = abs(latest_co2 - self.co2_stable_value)
                                self.co2_stable_value = latest_co2
                                self.co2_stability_start_time = current_time
                                print(f"CO2 instable, nouvelle référence: {latest_co2} ppm (variation de {variation:.2f} ppm)")
                                
                                # Mettre à jour le timestamp pour la stabilité CO2
                                if self.start_time_co2_temp_humidity is not None:
                                    self.regeneration_timestamps['co2_stability_started'] = current_time - self.start_time_co2_temp_humidity - self.elapsed_time_co2_temp_humidity
                        else:
                            # Pas de valeur de référence, l'initialiser
                            self.co2_stable_value = latest_co2
                            self.co2_stability_start_time = current_time
                            print(f"Initialisation valeur de référence CO2: {latest_co2} ppm")
                    
                    # Vérifier si le temps d'attente est trop long (3 minutes max)
                    timeout_progress = min(100, ((current_time - self.full_protocol_substep_start_time) / (3*60)) * 100)
                    if current_time - self.full_protocol_substep_start_time > 3*60:
                        print("Délai d'attente pour stabilité CO2 dépassé, passage à l'étape suivante")
                        self.full_protocol_step = 3
                        self.full_protocol_substep = 0  # Réinitialiser la sous-étape pour l'étape 3
                        
                        # Mémoriser la dernière valeur CO2 comme référence
                        if len(self.values_co2) > 0:
                            self.full_protocol_co2_initial = self.values_co2[-1]
                    
                    return {
                        'active': True,
                        'step': 2,
                        'message': f"Vérification stabilité CO2... (timeout: {timeout_progress:.0f}%)",
                        'progress': progress_per_step + (timeout_progress / 100) * progress_per_step,
                        'protocol_type': 'full'
                    }
            
            elif self.full_protocol_step == 3:
                # Étape 3: Augmenter Tcons à haute température (REGENERATION_TEMP = 700°C)
                if self.full_protocol_substep == 0:
                    # Démarrer le chauffage
                    print(f"Démarrage de l'étape 3: Chauffage à {REGENERATION_TEMP}°C")
                    success = self.set_Tcons(str(REGENERATION_TEMP))
                    if success:
                        print(f"Chauffage démarré à {REGENERATION_TEMP}°C")
                        self.full_protocol_substep = 1
                        self.full_protocol_substep_start_time = current_time
                    else:
                        print(f"Erreur lors du démarrage du chauffage à {REGENERATION_TEMP}°C")
                        # Réessayer encore une fois
                        print("Nouvelle tentative de mise à température...")
                        success = self.set_Tcons(str(REGENERATION_TEMP))
                        if success:
                            print("Seconde tentative réussie")
                            self.full_protocol_substep = 1
                            self.full_protocol_substep_start_time = current_time
                        else:
                            print("Échec de la seconde tentative, annulation du protocole")
                            # Annuler le protocole en cas d'erreur
                            self.full_protocol_in_progress = False
                            return {
                                'active': False,
                                'step': 0,
                                'message': "Erreur lors du démarrage du chauffage",
                                'progress': 0,
                                'protocol_type': 'full'
                            }
                
                elif self.full_protocol_substep == 1:
                    # Chauffage en cours, attendre que la conductance descende sous 5µS
                    if len(self.conductanceList) > 0:
                        current_conductance = self.conductanceList[-1]

                        # Afficher la conductance actuelle périodiquement
                        # Éviter de saturer la console avec trop de messages, uniquement afficher toutes les quelques secondes
                        elapsed = current_time - self.full_protocol_substep_start_time
                        if int(elapsed) % 5 == 0:  # Afficher tous les 5 secondes
                            print(f"Étape 3 - Conductance actuelle: {current_conductance:.2f} µS")

                        # Vérifier si on est descendu sous le seuil de conductance
                        if current_conductance <= 5:  # Seuil en µS
                            print(f"Conductance descendue sous 5 µS ({current_conductance:.6f} µS), passage à l'étape 4")
                            self.full_protocol_step = 4
                            self.full_protocol_substep = 0
                            self.full_protocol_substep_start_time = current_time
                        elif current_time - self.full_protocol_substep_start_time > 3*60:
                            # Sécurité: après 3 minutes, passer à l'étape suivante même si la conductance n'est pas assez basse
                            print(f"Délai de 3 minutes écoulé, sécurité activée - passage à l'étape 4 (conductance: {current_conductance:.2f} µS)")
                            self.full_protocol_step = 4
                            self.full_protocol_substep = 0
                            self.full_protocol_substep_start_time = current_time
                            print(f"Sécurité : mise de Tcons à {TCONS_LOW}°C car conductance > 5 µS après 3 minutes")
                    
                    # Calculer la progression basée sur le temps écoulé (max 3 minutes)
                    elapsed = current_time - self.full_protocol_substep_start_time
                    heat_progress = min(100, (elapsed / (3*60)) * 100)
                    
                    return {
                        'active': True,
                        'step': 3,
                        'message': f"Chauffage en cours ({heat_progress:.0f}%)",
                        'progress': progress_per_step * 3 + (heat_progress / 100) * progress_per_step,
                        'protocol_type': 'full'
                    }
            
            elif self.full_protocol_step == 4:
                # Étape 4: Mettre Tcons à basse température (TCONS_LOW = 0°C)
                if self.full_protocol_substep == 0:
                    # Abaisser la température
                    print(f"Démarrage de l'étape 4: Abaissement de la température à {TCONS_LOW}°C")
                    success = self.set_Tcons(str(TCONS_LOW))
                    if success:
                        print(f"Température abaissée à {TCONS_LOW}°C")
                        self.full_protocol_substep = 1
                        self.full_protocol_substep_start_time = current_time
                    else:
                        print(f"Erreur lors de l'abaissement de la température à {TCONS_LOW}°C")
                        # Réessayer encore une fois
                        print("Nouvelle tentative d'abaissement de température...")
                        success = self.set_Tcons(str(TCONS_LOW))
                        if success:
                            print("Seconde tentative réussie")
                        else:
                            print("Échec de la seconde tentative, mais continuation du protocole")
                        
                        # Continuer malgré l'erreur
                        self.full_protocol_substep = 1
                        self.full_protocol_substep_start_time = current_time
                
                elif self.full_protocol_substep == 1:
                    # Attendre un court délai puis passer à l'étape suivante
                    elapsed = current_time - self.full_protocol_substep_start_time
                    if elapsed >= 5:  # 5 secondes
                        print(f"Délai d'attente de 5 secondes écoulé après l'abaissement de température ({elapsed:.1f}s)")
                        self.full_protocol_step = 5
                        self.full_protocol_substep = 0
                        self.full_protocol_substep_start_time = current_time
                        print("Passage à l'étape 5: Surveillance de restabilisation du CO2")
                    
                    # Calculer progression (5 secondes max)
                    progress_in_substep = min(100, (elapsed / 5) * 100)
                    
                    return {
                        'active': True,
                        'step': 4,
                        'message': f"Température abaissée, attente ({progress_in_substep:.0f}%)",
                        'progress': progress_per_step * 4 + (progress_in_substep / 100) * progress_per_step,
                        'protocol_type': 'full'
                    }
            
            elif self.full_protocol_step == 5:
                # Étape 5: Attendre la restabilisation du CO2
                if self.full_protocol_substep == 0:
                    # Initialisation de la surveillance de restabilisation
                    if len(self.values_co2) > 0:
                        self.co2_restabilization_reference = self.values_co2[-1]
                        self.co2_restabilization_start_time = current_time
                        self.full_protocol_substep = 1
                        print(f"Début de la surveillance de restabilisation du CO2 à {self.co2_restabilization_reference} ppm")
                        
                        # Enregistrer le timestamp pour le début de la surveillance
                        if self.start_time_co2_temp_humidity is not None:
                            self.regeneration_timestamps['co2_restabilization_start_time'] = current_time - self.start_time_co2_temp_humidity - self.elapsed_time_co2_temp_humidity
                    else:
                        return {
                            'active': True,
                            'step': 5,
                            'message': "En attente de données CO2 pour la restabilisation",
                            'progress': progress_per_step * 5,
                            'protocol_type': 'full'
                        }
                
                elif self.full_protocol_substep == 1:
                    # Vérification de la restabilisation
                    if len(self.values_co2) > 0:
                        latest_co2 = self.values_co2[-1]
                        
                        if abs(latest_co2 - self.co2_restabilization_reference) <= CO2_STABILITY_THRESHOLD:
                            # CO2 stable, vérifier la durée
                            elapsed = current_time - self.co2_restabilization_start_time
                            stability_progress = min(100, (elapsed / CO2_STABILITY_DURATION) * 100)
                            
                            if elapsed >= CO2_STABILITY_DURATION:
                                # CO2 restabilisé, passer à l'étape suivante
                                self.full_protocol_step = 6
                                self.full_protocol_co2_final = latest_co2  # Mémoriser la valeur CO2 finale
                                self.co2_restabilized = True
                                print(f"CO2 restabilisé à {latest_co2} ppm, passage à l'étape finale")
                                
                                # Enregistrer le timestamp pour CO2 restabilisé
                                if self.start_time_co2_temp_humidity is not None:
                                    self.regeneration_timestamps['co2_restabilized'] = current_time - self.start_time_co2_temp_humidity - self.elapsed_time_co2_temp_humidity
                            
                            return {
                                'active': True,
                                'step': 5,
                                'message': f"Surveillance restabilisation CO2 ({stability_progress:.0f}%)",
                                'progress': progress_per_step * 5 + (stability_progress / 100) * progress_per_step,
                                'protocol_type': 'full'
                            }
                        else:
                            # CO2 a changé, réinitialiser la référence
                            variation = abs(latest_co2 - self.co2_restabilization_reference)
                            self.co2_restabilization_reference = latest_co2
                            self.co2_restabilization_start_time = current_time
                            print(f"CO2 instable, nouvelle référence: {latest_co2} ppm (variation de {variation:.2f} ppm)")
                            
                            # Mettre à jour le timestamp pour le début de la recherche de restabilisation
                            if self.start_time_co2_temp_humidity is not None:
                                self.regeneration_timestamps['co2_restabilization_start_time'] = current_time - self.start_time_co2_temp_humidity - self.elapsed_time_co2_temp_humidity
                    
                    # Vérifier si le temps d'attente est trop long (5 minutes max)
                    timeout_progress = min(100, ((current_time - self.full_protocol_substep_start_time) / (5*60)) * 100)
                    if current_time - self.full_protocol_substep_start_time > 5*60:
                        print("Délai d'attente pour restabilisation CO2 dépassé, passage à l'étape finale")
                        self.full_protocol_step = 6
                        
                        # Mémoriser la dernière valeur CO2 comme valeur finale
                        if len(self.values_co2) > 0:
                            self.full_protocol_co2_final = self.values_co2[-1]
                            
                            # Forcer l'état restabilisé pour le calcul des résultats
                            self.co2_restabilized = True
                    
                    return {
                        'active': True,
                        'step': 5,
                        'message': f"Surveillance restabilisation CO2... (timeout: {timeout_progress:.0f}%)",
                        'progress': progress_per_step * 5 + (timeout_progress / 100) * progress_per_step,
                        'protocol_type': 'full'
                    }
            
            elif self.full_protocol_step == 6:
                # Étape 6: Calcul des résultats et fin du protocole
                from core.constants import CELL_VOLUME
                
                # Calcul du delta C et de la masse de carbone
                delta_c = 0
                carbon_mass = 0
                
                if self.full_protocol_co2_initial is not None and self.full_protocol_co2_final is not None:
                    # Calculer la différence entre la valeur stable initiale et la valeur finale
                    delta_c = self.full_protocol_co2_final - self.full_protocol_co2_initial
                    
                    # Calculer la masse de carbone en µg: mc = deltaC * volume / 24.5 * 12
                    carbon_mass = delta_c * CELL_VOLUME / 24.5 * 12
                    
                    print(f"Delta C: {delta_c:.2f} ppm")
                    print(f"Masse de carbone: {carbon_mass:.2f} µg")
                
                # Le temps de percolation est simplement le moment où l'augmentation commence
                percolation_time = 0
                if self.increase_time is not None:
                    percolation_time = self.increase_time
                    print(f"Temps de percolation: {percolation_time:.1f} s")
                
                # Stocker les résultats pour l'affichage
                self.regeneration_results = {
                    'delta_c': delta_c,
                    'carbon_mass': carbon_mass,
                    'percolation_time': percolation_time
                }
                
                # Fin du protocole
                self.full_protocol_in_progress = False
                self.full_protocol_step = 0
                print("Protocole complet terminé avec succès")
                
                return {
                    'active': False,
                    'step': 0,
                    'message': "Protocole complet terminé",
                    'progress': 100,
                    'results': self.regeneration_results,
                    'protocol_type': 'full'
                }
            
            # Retourner le statut actuel
            current_progress = min(99, progress_per_step * (self.full_protocol_step - 1))
            return {
                'active': True,
                'step': self.full_protocol_step,
                'message': f"Étape {self.full_protocol_step} en cours...",
                'progress': current_progress,
                'protocol_type': 'full'
            }
            
        except Exception as e:
            print(f"Erreur dans manage_full_protocol: {e}")
            self.full_protocol_in_progress = False
            return {
                'active': False,
                'step': 0,
                'message': f"Erreur: {str(e)}",
                'progress': 0,
                'protocol_type': 'full'
            }
    
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
                if current_co2 - self.co2_base_value >= CO2_INCREASE_THRESHOLD:  # Seuil d'augmentation
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

    def get_events_dictionary(self):
        """
        Crée un dictionnaire des événements pour l'affichage sur les graphiques

        Returns:
            dict: Dictionnaire contenant tous les événements de temps à marquer
        """
        events = {}

        # Ajouter les événements standards de détection
        if self.increase_time is not None:
            events['increase_time'] = self.increase_time

        if self.stabilization_time is not None:
            events['stabilization_time'] = self.stabilization_time

        if hasattr(self, 'max_slope_time') and self.max_slope_time:
            events['max_slope_time'] = self.max_slope_time

        # Ajouter les événements post-régénération
        if hasattr(self, 'conductance_decrease_time') and self.conductance_decrease_time is not None:
            events['conductance_decrease_time'] = self.conductance_decrease_time

        if hasattr(self, 'post_regen_stability_time') and self.post_regen_stability_time is not None:
            events['post_regen_stability_time'] = self.post_regen_stability_time

        # Ajouter l'événement de première stabilité du protocole complet
        if hasattr(self, 'first_stability_time') and self.first_stability_time is not None:
            events['first_stability_time'] = self.first_stability_time

        return events