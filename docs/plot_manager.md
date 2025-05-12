# Module `plot_manager`

*Fichier source : `plot_manager.py`*

## Fonctions
- [`__init__(self, mode="manual")`](#__init__)
- [`setup_plots(self)`](#setup_plots)
- [`center_window()`](#center_window)
- [`setup_manual_buttons(self)`](#setup_manual_buttons)
- [`setup_auto_buttons(self)`](#setup_auto_buttons)
- [`setup_common_elements(self)`](#setup_common_elements)
- [`setup_add_device_buttons(self)`](#setup_add_device_buttons)
- [`setup_indicators(self)`](#setup_indicators)
- [`connect_button(self, button_name, callback)`](#connect_button)
- [`wrapped_disabled_callback(event)`](#wrapped_disabled_callback)
- [`wrapped_init_callback(event)`](#wrapped_init_callback)
- [`connect_textbox(self, textbox_name, callback)`](#connect_textbox)
- [`connect_radiobutton(self, radiobutton_name, callback)`](#connect_radiobutton)
- [`update_indicator(self, indicator_name, state)`](#update_indicator)
- [`update_sensor_indicators(self, pin_states=None)`](#update_sensor_indicators)
- [`update_detection_indicators(self, increase_detected, stabilized)`](#update_detection_indicators)
- [`reset_reference_restabilization(self)`](#reset_reference_restabilization)
- [`update_R0_display(self, value)`](#update_r0_display)
- [`update_regeneration_status(self, status, results=None)`](#update_regeneration_status)
- [`update_conductance_plot(self, timeList, conductanceList, events=None)`](#update_conductance_plot)
- [`update_co2_temp_humidity_plot(self, timestamps_co2, values_co2, timestamps_temp, values_temp, 
                                    timestamps_humidity, values_humidity, regeneration_timestamps=None)`](#update_co2_temp_humidity_plot)
- [`update_res_temp_plot(self, timestamps, temperatures, tcons_values, regeneration_timestamps=None)`](#update_res_temp_plot)
- [`update_raz_buttons_visibility(self, measurement_states)`](#update_raz_buttons_visibility)
- [`deactivate_movement_buttons(self)`](#deactivate_movement_buttons)
- [`set_regeneration_buttons_state(self, active)`](#set_regeneration_buttons_state)
- [`configure_measurement_panels(self, measure_conductance=True, measure_co2=True, measure_regen=True)`](#configure_measurement_panels)
- [`on_time_unit_change(self, label)`](#on_time_unit_change)
- [`update_backup_status(self, status_info)`](#update_backup_status)
- [`close(self)`](#close)
- [`show(self)`](#show)
- [`update_add_device_buttons(self, available_devices=None)`](#update_add_device_buttons)
- [`connect_add_device_button(self, device_type, callback)`](#connect_add_device_button)
- [`wrapped_callback(event)`](#wrapped_callback)
- [`update_protocol_button_states(self, measure_co2_temp_humidity_active, measure_conductance_active, measure_res_temp_active)`](#update_protocol_button_states)
- [`_update_button_state(self, button_name, is_active, active_color)`](#_update_button_state)
- [`_update_cancel_button_visibility(self)`](#_update_cancel_button_visibility)
- [`update_regeneration_status(self, status_info, regeneration_results=None)`](#update_regeneration_status)
- [`set_close_callback(self, callback)`](#set_close_callback)
- [`new_close_event(event)`](#new_close_event)
- [`on_close(event)`](#on_close)

---

## `__init__(self, mode="manual")` { #__init__ }

```python
def __init__(self, mode="manual")
```

Initialise le gestionnaire de graphiques
Args:
mode: Mode "manual" ou "auto"

---

## `setup_plots(self)` { #setup_plots }

```python
def setup_plots(self)
```

Configure la figure et les axes pour les graphiques

---

## `center_window()` { #center_window }

```python
def center_window()
```

Pas de docstring

---

## `setup_manual_buttons(self)` { #setup_manual_buttons }

```python
def setup_manual_buttons(self)
```

Configure les boutons pour le mode manuel

---

## `setup_auto_buttons(self)` { #setup_auto_buttons }

```python
def setup_auto_buttons(self)
```

Configure les boutons pour le mode automatique

---

## `setup_common_elements(self)` { #setup_common_elements }

```python
def setup_common_elements(self)
```

Configure les éléments communs aux deux modes

---

## `setup_add_device_buttons(self)` { #setup_add_device_buttons }

```python
def setup_add_device_buttons(self)
```

Configure les boutons pour ajouter des appareils pendant l'exécution

---

## `setup_indicators(self)` { #setup_indicators }

```python
def setup_indicators(self)
```

Configure les indicateurs d'état

---

## `connect_button(self, button_name, callback)` { #connect_button }

```python
def connect_button(self, button_name, callback)
```

Connecte un bouton à une fonction de rappel
Args:
button_name: Nom du bouton à connecter
callback: Fonction à appeler lorsque le bouton est cliqué

---

## `wrapped_disabled_callback(event)` { #wrapped_disabled_callback }

```python
def wrapped_disabled_callback(event)
```

Pas de docstring

---

## `wrapped_init_callback(event)` { #wrapped_init_callback }

```python
def wrapped_init_callback(event)
```

Pas de docstring

---

## `connect_textbox(self, textbox_name, callback)` { #connect_textbox }

```python
def connect_textbox(self, textbox_name, callback)
```

Connecte un champ de texte à une fonction de rappel
Args:
textbox_name: Nom du champ de texte à connecter
callback: Fonction à appeler lorsque le champ de texte est soumis

---

## `connect_radiobutton(self, radiobutton_name, callback)` { #connect_radiobutton }

```python
def connect_radiobutton(self, radiobutton_name, callback)
```

Connecte un bouton radio à une fonction de rappel
Args:
radiobutton_name: Nom du bouton radio à connecter
callback: Fonction à appeler lorsque la sélection du bouton radio change

---

## `update_indicator(self, indicator_name, state)` { #update_indicator }

```python
def update_indicator(self, indicator_name, state)
```

Met à jour l'état d'un indicateur
Args:
indicator_name: Nom de l'indicateur à mettre à jour
state: Nouvel état pour l'indicateur (True = actif, False = inactif)

---

## `update_sensor_indicators(self, pin_states=None)` { #update_sensor_indicators }

```python
def update_sensor_indicators(self, pin_states=None)
```

Met à jour les indicateurs de capteurs en fonction des états individuels des broches
Args:
pin_states: Dictionnaire avec les états des broches VR, VS, TO, TF
{'vr': bool, 'vs': bool, 'to': bool, 'tf': bool}

---

## `update_detection_indicators(self, increase_detected, stabilized)` { #update_detection_indicators }

```python
def update_detection_indicators(self, increase_detected, stabilized)
```

Met à jour les indicateurs de détection - utilise maintenant des lignes verticales pointillées 
dans le graphique de conductance au lieu des indicateurs LED
Args:
increase_detected: Si une augmentation de conductance a été détectée
stabilized: Si la conductance s'est stabilisée

---

## `reset_reference_restabilization(self)` { #reset_reference_restabilization }

```python
def reset_reference_restabilization(self)
```

Réinitialise le temps de référence de restabilisation pour utiliser la prochaine restabilisation détectée

---

## `update_R0_display(self, value)` { #update_r0_display }

```python
def update_R0_display(self, value)
```

Met à jour l'affichage de R0
Args:
value: Valeur à afficher

---

## `update_regeneration_status(self, status, results=None)` { #update_regeneration_status }

```python
def update_regeneration_status(self, status, results=None)
```

Met à jour l'état du bouton de régénération en fonction de la progression de la régénération
Args:
status: Dictionnaire contenant l'état du protocole de régénération
'active': bool - True si la régénération est en cours
'step': int - Étape actuelle (0-3)
'message': str - Message d'état
'progress': float - Pourcentage de progression (0-100)
results: Dictionnaire optionnel contenant les résultats de la régénération
'delta_c': float - Delta C entre la stabilisation initiale et finale
'carbon_mass': float - Masse de carbone calculée en µg

---

## `update_conductance_plot(self, timeList, conductanceList, events=None)` { #update_conductance_plot }

```python
def update_conductance_plot(self, timeList, conductanceList, events=None)
```

Met à jour le graphique de conductance
Args:
timeList: Liste des valeurs de temps
conductanceList: Liste des valeurs de conductance
events: Dictionnaire des événements à marquer sur le graphique

---

## `update_co2_temp_humidity_plot(self, timestamps_co2, values_co2, timestamps_temp, values_temp, 
                                    timestamps_humidity, values_humidity, regeneration_timestamps=None)` { #update_co2_temp_humidity_plot }

```python
def update_co2_temp_humidity_plot(self, timestamps_co2, values_co2, timestamps_temp, values_temp, 
                                    timestamps_humidity, values_humidity, regeneration_timestamps=None)
```

Met à jour le graphique de CO2, température et humidité
Args:
timestamps_co2: Liste des horodatages CO2
values_co2: Liste des valeurs de CO2
timestamps_temp: Liste des horodatages de température
values_temp: Liste des valeurs de température
timestamps_humidity: Liste des horodatages d'humidité
values_humidity: Liste des valeurs d'humidité
regeneration_timestamps: Dictionnaire des horodatages pour les événements clés du protocole de régénération

---

## `update_res_temp_plot(self, timestamps, temperatures, tcons_values, regeneration_timestamps=None)` { #update_res_temp_plot }

```python
def update_res_temp_plot(self, timestamps, temperatures, tcons_values, regeneration_timestamps=None)
```

Met à jour le graphique de température de résistance
Args:
timestamps: Liste des horodatages
temperatures: Liste des valeurs de température
tcons_values: Liste des valeurs de Tcons
regeneration_timestamps: Dictionnaire des horodatages pour les événements clés du protocole de régénération

---

## `update_raz_buttons_visibility(self, measurement_states)` { #update_raz_buttons_visibility }

```python
def update_raz_buttons_visibility(self, measurement_states)
```

Met à jour la visibilité des boutons de réinitialisation en fonction des états de mesure
Args:
measurement_states: Dictionnaire avec les états de mesure

---

## `deactivate_movement_buttons(self)` { #deactivate_movement_buttons }

```python
def deactivate_movement_buttons(self)
```

Désactive les boutons push/open et retract/close

---

## `set_regeneration_buttons_state(self, active)` { #set_regeneration_buttons_state }

```python
def set_regeneration_buttons_state(self, active)
```

Active ou désactive les boutons qui doivent être indisponibles pendant la régénération
Args:
active: True pour activer les boutons, False pour les désactiver

---

## `configure_measurement_panels(self, measure_conductance=True, measure_co2=True, measure_regen=True)` { #configure_measurement_panels }

```python
def configure_measurement_panels(self, measure_conductance=True, measure_co2=True, measure_regen=True)
```

Configure les panneaux de mesure visibles et réorganise la mise en page
Args:
measure_conductance: Si le panneau de conductance doit être affiché
measure_co2: Si le panneau CO2/temp/humidité doit être affiché
measure_regen: Si le panneau de température de régénération doit être affiché

---

## `on_time_unit_change(self, label)` { #on_time_unit_change }

```python
def on_time_unit_change(self, label)
```

Gère le changement d'affichage des unités de temps (secondes/minutes)
Args:
label: Étiquette du bouton radio sélectionné

---

## `update_backup_status(self, status_info)` { #update_backup_status }

```python
def update_backup_status(self, status_info)
```

Met à jour l'indicateur de sauvegarde de secours
Args:
status_info: Dictionnaire contenant les informations sur la dernière sauvegarde
'time': float - Timestamp de la dernière sauvegarde
'success': bool - True si la sauvegarde a réussi
'reason': str - Raison de la sauvegarde

---

## `close(self)` { #close }

```python
def close(self)
```

Ferme la fenêtre du graphique

---

## `show(self)` { #show }

```python
def show(self)
```

Affiche la fenêtre du graphique

---

## `update_add_device_buttons(self, available_devices=None)` { #update_add_device_buttons }

```python
def update_add_device_buttons(self, available_devices=None)
```

Met à jour l'état des boutons d'ajout d'appareils en fonction des appareils déjà connectés
Args:
available_devices: Dictionnaire indiquant les appareils déjà connectés
{'arduino': bool, 'regen': bool, 'keithley': bool}

---

## `connect_add_device_button(self, device_type, callback)` { #connect_add_device_button }

```python
def connect_add_device_button(self, device_type, callback)
```

Connecte un callback au bouton d'ajout d'appareil
Args:
device_type: Type d'appareil ('arduino', 'regen' ou 'keithley')
callback: Fonction à appeler lorsque le bouton est cliqué

---

## `wrapped_callback(event)` { #wrapped_callback }

```python
def wrapped_callback(event)
```

Pas de docstring

---

## `update_protocol_button_states(self, measure_co2_temp_humidity_active, measure_conductance_active, measure_res_temp_active)` { #update_protocol_button_states }

```python
def update_protocol_button_states(self, measure_co2_temp_humidity_active, measure_conductance_active, measure_res_temp_active)
```

Met à jour l'état des boutons de protocole en fonction des mesures actives
- Le bouton de protocole CO2 doit être cliquable si CO2 et Tcons/Tmes sont actifs
- Le bouton de protocole de conductance doit être cliquable si Conductance et Tcons/Tmes sont actifs
- Le bouton de protocole complet doit être cliquable si les trois mesures sont actives ET que l'init a été effectué
Args:
measure_co2_temp_humidity_active: Si la mesure de CO2/température/humidité est active
measure_conductance_active: Si la mesure de conductance est active
measure_res_temp_active: Si la mesure de résistance/température est active

---

## `_update_button_state(self, button_name, is_active, active_color)` { #_update_button_state }

```python
def _update_button_state(self, button_name, is_active, active_color)
```

Met à jour l'état d'un bouton de protocole

---

## `_update_cancel_button_visibility(self)` { #_update_cancel_button_visibility }

```python
def _update_cancel_button_visibility(self)
```

Met à jour la visibilité du bouton Cancel

---

## `update_regeneration_status(self, status_info, regeneration_results=None)` { #update_regeneration_status }

```python
def update_regeneration_status(self, status_info, regeneration_results=None)
```

Met à jour l'affichage du statut de régénération/protocole
Args:
status_info: Dictionnaire contenant les informations de statut
'active': Bool - Si le protocole est actif
'step': Int - Étape courante du protocole
'message': Str - Message à afficher
'progress': Float - Progression (0-100)
regeneration_results: Résultats de régénération (non utilisé dans cette fonction)

---

## `set_close_callback(self, callback)` { #set_close_callback }

```python
def set_close_callback(self, callback)
```

Configure un callback pour quand la fenêtre est fermée via le bouton X
Args:
callback: Fonction à appeler quand la fenêtre est fermée

---

## `new_close_event(event)` { #new_close_event }

```python
def new_close_event(event)
```

Pas de docstring

---

## `on_close(event)` { #on_close }

```python
def on_close(event)
```

Pas de docstring

---

