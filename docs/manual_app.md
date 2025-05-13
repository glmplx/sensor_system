# Module `manual_app`

*Fichier source : `manual_app.py`*

## Fonctions
- [`main(arduino_port=None, arduino_baud_rate=None, other_port=None, other_baud_rate=None,
         measure_conductance=1, measure_co2=1, measure_regen=1, auto_save=True, save_data=True,
         custom_save_location=False, save_location=None)`](#main)
- [`handle_window_close(event=None)`](#handle_window_close)
- [`toggle_conductance(event)`](#toggle_conductance)
- [`toggle_co2_temp_humidity(event)`](#toggle_co2_temp_humidity)
- [`toggle_res_temp(event)`](#toggle_res_temp)
- [`raz_conductance(event)`](#raz_conductance)
- [`raz_co2_temp_humidity(event)`](#raz_co2_temp_humidity)
- [`raz_res_temp(event)`](#raz_res_temp)
- [`set_R0(event)`](#set_r0)
- [`set_Tcons(event)`](#set_tcons)
- [`update_read_R0(event)`](#update_read_r0)
- [`push_open(event)`](#push_open)
- [`retract_close(event)`](#retract_close)
- [`init_system(event)`](#init_system)
- [`start_full_protocol(self)`](#start_full_protocol)
- [`start_regeneration(event)`](#start_regeneration)
- [`cancel_regeneration(event)`](#cancel_regeneration)
- [`quit_program(event)`](#quit_program)
- [`toggle_all_measurements(event)`](#toggle_all_measurements)
- [`perform_emergency_backup(reason="sauvegarde automatique")`](#perform_emergency_backup)
- [`check_device_errors()`](#check_device_errors)
- [`add_arduino_device(event)`](#add_arduino_device)
- [`add_keithley_device(event=None)`](#add_keithley_device)
- [`add_regen_device(event)`](#add_regen_device)
- [`start_conductance_regen(event)`](#start_conductance_regen)
- [`add_keithley_device(event)`](#add_keithley_device)

---

## `main(arduino_port=None, arduino_baud_rate=None, other_port=None, other_baud_rate=None,
         measure_conductance=1, measure_co2=1, measure_regen=1, auto_save=True, save_data=True,
         custom_save_location=False, save_location=None)` { #main }

```python
def main(arduino_port=None, arduino_baud_rate=None, other_port=None, other_baud_rate=None,
         measure_conductance=1, measure_co2=1, measure_regen=1, auto_save=True, save_data=True,
         custom_save_location=False, save_location=None)
```

Point d'entrée principal pour l'application en mode manuel
Args:
arduino_port: Port COM pour l'Arduino
arduino_baud_rate: Débit en bauds pour l'Arduino
other_port: Port COM pour l'appareil de régénération
other_baud_rate: Débit en bauds pour l'appareil de régénération
measure_conductance: Activer les mesures de conductance (1=activé, 0=désactivé)
measure_co2: Activer les mesures de CO2/température/humidité (1=activé, 0=désactivé)
measure_regen: Activer les mesures de régénération/température (1=activé, 0=désactivé)

---

## `handle_window_close(event=None)` { #handle_window_close }

```python
def handle_window_close(event=None)
```

Gère la fermeture de la fenêtre

---

## `toggle_conductance(event)` { #toggle_conductance }

```python
def toggle_conductance(event)
```

Gère l'activation/desactivation des données de conductance

---

## `toggle_co2_temp_humidity(event)` { #toggle_co2_temp_humidity }

```python
def toggle_co2_temp_humidity(event)
```

Gère l'activation/desactivation des données CO2/température/humidité

---

## `toggle_res_temp(event)` { #toggle_res_temp }

```python
def toggle_res_temp(event)
```

Gère l'activation/desactivation des données de température et de résistance

---

## `raz_conductance(event)` { #raz_conductance }

```python
def raz_conductance(event)
```

Gère la réinitialisation des données de conductance

---

## `raz_co2_temp_humidity(event)` { #raz_co2_temp_humidity }

```python
def raz_co2_temp_humidity(event)
```

Gère la réinitialisation des données CO2/température/humidité

---

## `raz_res_temp(event)` { #raz_res_temp }

```python
def raz_res_temp(event)
```

Gère la réinitialisation des données de température et de résistance

---

## `set_R0(event)` { #set_r0 }

```python
def set_R0(event)
```

Gère la définition de R0

---

## `set_Tcons(event)` { #set_tcons }

```python
def set_Tcons(event)
```

Gère la définition de Tcons

---

## `update_read_R0(event)` { #update_read_r0 }

```python
def update_read_R0(event)
```

Gère la lecture de R0

---

## `push_open(event)` { #push_open }

```python
def push_open(event)
```

Gère le bouton d'ouverture du vérin

---

## `retract_close(event)` { #retract_close }

```python
def retract_close(event)
```

Gère le bouton de rétraction du vérin

---

## `init_system(event)` { #init_system }

```python
def init_system(event)
```

Gère l'initialisation du système

---

## `start_full_protocol(self)` { #start_full_protocol }

```python
def start_full_protocol(self)
```

Gère le démarrage du protocole complet

---

## `start_regeneration(event)` { #start_regeneration }

```python
def start_regeneration(event)
```

Gère le démarrage du protocole de régénération

---

## `cancel_regeneration(event)` { #cancel_regeneration }

```python
def cancel_regeneration(event)
```

Gère l'annulation de tous les protocoles

---

## `quit_program(event)` { #quit_program }

```python
def quit_program(event)
```

Gère la fermeture du programme

---

## `toggle_all_measurements(event)` { #toggle_all_measurements }

```python
def toggle_all_measurements(event)
```

Pas de docstring

---

## `perform_emergency_backup(reason="sauvegarde automatique")` { #perform_emergency_backup }

```python
def perform_emergency_backup(reason="sauvegarde automatique")
```

Effectue une sauvegarde d'urgence des données en cas de problème avec un appareil
ou périodiquement pour éviter la perte de données
Args:
reason: Raison de la sauvegarde (pour le journal et les notifications)
Returns:
bool: True si des données ont été sauvegardées, False sinon

---

## `check_device_errors()` { #check_device_errors }

```python
def check_device_errors()
```

Vérifie les erreurs des appareils pour détecter des problèmes de connexion
Returns:
dict: Informations sur les erreurs détectées

---

## `add_arduino_device(event)` { #add_arduino_device }

```python
def add_arduino_device(event)
```

Fonction pour ajouter un Arduino en cours d'exécution

---

## `add_keithley_device(event=None)` { #add_keithley_device }

```python
def add_keithley_device(event=None)
```

Fonction pour ajouter un Keithley en cours d'exécution

---

## `add_regen_device(event)` { #add_regen_device }

```python
def add_regen_device(event)
```

Fonction pour ajouter une carte de régénération en cours d'exécution

---

## `start_conductance_regen(event)` { #start_conductance_regen }

```python
def start_conductance_regen(event)
```

Gérer le protocole de régénération de conductance

---

## `add_keithley_device(event)` { #add_keithley_device }

```python
def add_keithley_device(event)
```

Fonction pour ajouter un Keithley en cours d'exécution

---

