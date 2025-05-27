# Module `measurement_manager`

*Fichier source : `measurement_manager.py`*

## Fonctions
- [`__init__(self, keithley_device, arduino_device, regen_device)`](#__init__)
- [`reset_data(self, data_type=None)`](#reset_data)
- [`read_conductance(self)`](#read_conductance)
- [`read_arduino_status_only(self)`](#read_arduino_status_only)
- [`read_arduino_data(self)`](#read_arduino_data)
- [`read_arduino(self)`](#read_arduino)
- [`read_res_temp(self)`](#read_res_temp)
- [`push_open_sensor(self)`](#push_open_sensor)
- [`retract_close_sensor(self)`](#retract_close_sensor)
- [`init_system(self)`](#init_system)
- [`set_R0(self, value)`](#set_r0)
- [`set_Tcons(self, value)`](#set_tcons)
- [`read_R0(self)`](#read_r0)
- [`detect_increase(self)`](#detect_increase)
- [`detect_stabilization(self)`](#detect_stabilization)
- [`detect_co2_peak(self)`](#detect_co2_peak)
- [`check_reset_detection_indicators(self)`](#check_reset_detection_indicators)
- [`check_conductance_increase_after_decrease(self)`](#check_conductance_increase_after_decrease)
- [`detect_post_regen_stability(self)`](#detect_post_regen_stability)
- [`automatic_mode_handler(self)`](#automatic_mode_handler)
- [`get_last_timestamps(self)`](#get_last_timestamps)
- [`start_regeneration_protocol(self)`](#start_regeneration_protocol)
- [`cancel_regeneration_protocol(self)`](#cancel_regeneration_protocol)
- [`cancel_full_protocol(self)`](#cancel_full_protocol)
- [`check_co2_stability(self)`](#check_co2_stability)
- [`check_co2_restabilization(self)`](#check_co2_restabilization)
- [`regeneration_complete(self)`](#regeneration_complete)
- [`start_conductance_regen_protocol(self)`](#start_conductance_regen_protocol)
- [`cancel_conductance_regen_protocol(self)`](#cancel_conductance_regen_protocol)
- [`manage_conductance_regen_protocol(self)`](#manage_conductance_regen_protocol)
- [`start_full_protocol(self)`](#start_full_protocol)
- [`manage_full_protocol(self)`](#manage_full_protocol)
- [`manage_regeneration_protocol(self)`](#manage_regeneration_protocol)
- [`get_events_dictionary(self)`](#get_events_dictionary)

---

## `__init__(self, keithley_device, arduino_device, regen_device)` { #__init__ }

```python
def __init__(self, keithley_device, arduino_device, regen_device)
```

Initialise le gestionnaire de mesures
Args:
keithley_device: Appareil pour les mesures de résistance
arduino_device: Appareil pour les mesures de CO2, température, humidité
regen_device: Appareil pour le contrôle de température de résistance

---

## `reset_data(self, data_type=None)` { #reset_data }

```python
def reset_data(self, data_type=None)
```

Reset stored data with proper handling for ExcelHandler
Args:
data_type: Type of data to reset, or None for all data

---

## `read_conductance(self)` { #read_conductance }

```python
def read_conductance(self)
```

Lit les données de conductance depuis l'appareil Keithley

---

## `read_arduino_status_only(self)` { #read_arduino_status_only }

```python
def read_arduino_status_only(self)
```

Read pin states from Arduino without storing CO2/temperature/humidity data
Returns: True if pin states were updated, False otherwise

---

## `read_arduino_data(self)` { #read_arduino_data }

```python
def read_arduino_data(self)
```

Read CO2, temperature, humidity data from Arduino and store it
Only called when measurements are active

---

## `read_arduino(self)` { #read_arduino }

```python
def read_arduino(self)
```

Méthode pour compatibilité - redirige vers read_arduino_data

---

## `read_res_temp(self)` { #read_res_temp }

```python
def read_res_temp(self)
```

Read resistance temperature data

---

## `push_open_sensor(self)` { #push_open_sensor }

```python
def push_open_sensor(self)
```

Push/open the sensor

---

## `retract_close_sensor(self)` { #retract_close_sensor }

```python
def retract_close_sensor(self)
```

Retract/close the sensor

---

## `init_system(self)` { #init_system }

```python
def init_system(self)
```

Initialize the system

---

## `set_R0(self, value)` { #set_r0 }

```python
def set_R0(self, value)
```

Set R0 value

---

## `set_Tcons(self, value)` { #set_tcons }

```python
def set_Tcons(self, value)
```

Set Tcons value

---

## `read_R0(self)` { #read_r0 }

```python
def read_R0(self)
```

Read R0 value

---

## `detect_increase(self)` { #detect_increase }

```python
def detect_increase(self)
```

Detect increase in conductance
Returns: True if increase detected, False otherwise

---

## `detect_stabilization(self)` { #detect_stabilization }

```python
def detect_stabilization(self)
```

Detect stabilization in conductance
Returns: True if stabilization detected, False otherwise

---

## `detect_co2_peak(self)` { #detect_co2_peak }

```python
def detect_co2_peak(self)
```

Detect CO2 peak after an increase was detected
Returns:
None: Updates self.co2_peak_detected flag if a peak is detected

---

## `check_reset_detection_indicators(self)` { #check_reset_detection_indicators }

```python
def check_reset_detection_indicators(self)
```

Vérifie si la conductance est descendue sous 5 µS après stabilisation
et réinitialise les indicateurs de détection (mais pas le temps de percolation)
Returns: True si les indicateurs ont été réinitialisés, False sinon

---

## `check_conductance_increase_after_decrease(self)` { #check_conductance_increase_after_decrease }

```python
def check_conductance_increase_after_decrease(self)
```

Vérifie si la conductance remonte après être descendue sous 5 µS.
Si oui, actualise l'indicateur de début d'augmentation (T perco).
Returns: True si une remontée est détectée et l'indicateur actualisé, False sinon

---

## `detect_post_regen_stability(self)` { #detect_post_regen_stability }

```python
def detect_post_regen_stability(self)
```

Détecte la restabilisation après une chute de conductance post-régénération
Returns: True si restabilisation détectée, False sinon

---

## `automatic_mode_handler(self)` { #automatic_mode_handler }

```python
def automatic_mode_handler(self)
```

Handle automatic mode logic
Returns: True if action was taken, False otherwise

---

## `get_last_timestamps(self)` { #get_last_timestamps }

```python
def get_last_timestamps(self)
```

Get the latest timestamps for all data types

---

## `start_regeneration_protocol(self)` { #start_regeneration_protocol }

```python
def start_regeneration_protocol(self)
```

Start the regeneration protocol:
1. Check for CO2 stability (±2 ppm for 2 minutes)
2. When stable, increase temperature to 700°C for 3 minutes
3. Return to normal operation
Returns:
bool: True if regeneration protocol was started, False if already in progress

---

## `cancel_regeneration_protocol(self)` { #cancel_regeneration_protocol }

```python
def cancel_regeneration_protocol(self)
```

Cancel the regeneration protocol and return to normal temperature
Returns:
bool: True if regeneration was cancelled, False if not in progress

---

## `cancel_full_protocol(self)` { #cancel_full_protocol }

```python
def cancel_full_protocol(self)
```

Annule le protocole complet en cours
Returns:
bool: True si l'annulation a réussi, False si aucun protocole n'est en cours

---

## `check_co2_stability(self)` { #check_co2_stability }

```python
def check_co2_stability(self)
```

Check if CO2 readings are stable (±2 ppm for 2 minutes)
Returns:
bool: True if CO2 is stable for the required duration, False otherwise

---

## `check_co2_restabilization(self)` { #check_co2_restabilization }

```python
def check_co2_restabilization(self)
```

Check if CO2 readings have restabilized after the peak
Returns:
bool: True if CO2 is stable for the required duration, False otherwise

---

## `regeneration_complete(self)` { #regeneration_complete }

```python
def regeneration_complete(self)
```

Complete the regeneration process and reset variables

---

## `start_conductance_regen_protocol(self)` { #start_conductance_regen_protocol }

```python
def start_conductance_regen_protocol(self)
```

Démarre le protocole de conductance avec résistance/température:
1. Lance la régénération à 700°C
2. Surveille la résistance jusqu'à ce qu'elle dépasse 1 MΩ
3. Arrête la régénération quand la résistance > 1 MΩ est atteinte
Returns:
bool: True si le protocole a été démarré, False si déjà en cours

---

## `cancel_conductance_regen_protocol(self)` { #cancel_conductance_regen_protocol }

```python
def cancel_conductance_regen_protocol(self)
```

Annuler le protocole de conductance résistance/température
Returns:
bool: True si le protocole a été annulé, False sinon

---

## `manage_conductance_regen_protocol(self)` { #manage_conductance_regen_protocol }

```python
def manage_conductance_regen_protocol(self)
```

Gère le protocole de conductance avec résistance/température:
Surveille la résistance et arrête la régénération quand elle dépasse 1 MΩ
Returns:
dict: État actuel du protocole

---

## `start_full_protocol(self)` { #start_full_protocol }

```python
def start_full_protocol(self)
```

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

---

## `manage_full_protocol(self)` { #manage_full_protocol }

```python
def manage_full_protocol(self)
```

Gère les différentes étapes du protocole complet.
Returns:
dict: État actuel du protocole complet
'active': bool - True si le protocole est en cours
'step': int - Étape actuelle (1-7)
'message': str - Message d'état
'progress': float - Progression (0-100)
'protocol_type': str - Toujours "full" pour identifier ce protocole

---

## `manage_regeneration_protocol(self)` { #manage_regeneration_protocol }

```python
def manage_regeneration_protocol(self)
```

Gère le protocole de régénération avec les nouvelles règles :
1. La détection de restabilisation peut commencer dès le pic détecté
2. La température reste à 700°C jusqu'à la fin de REGENERATION_DURATION
3. La restabilisation peut se terminer avant ou après le retour à 0°C

---

## `get_events_dictionary(self)` { #get_events_dictionary }

```python
def get_events_dictionary(self)
```

Crée un dictionnaire des événements pour l'affichage sur les graphiques
Returns:
dict: Dictionnaire contenant tous les événements de temps à marquer

---

