# Module `auto_app`

*Fichier source : `auto_app.py`*

## Fonctions
- [`main(arduino_port=None, arduino_baud_rate=None, other_port=None, other_baud_rate=None)`](#main)
- [`handle_window_close(event=None)`](#handle_window_close)
- [`toggle_auto(event)`](#toggle_auto)
- [`raz_auto(event)`](#raz_auto)
- [`set_R0(event)`](#set_r0)
- [`update_read_R0(event)`](#update_read_r0)
- [`push_open(event)`](#push_open)
- [`retract_close(event)`](#retract_close)
- [`init_system(event)`](#init_system)
- [`start_regeneration(event)`](#start_regeneration)
- [`cancel_regeneration(event)`](#cancel_regeneration)
- [`quit_program(event)`](#quit_program)
- [`process_pin_states(line)`](#process_pin_states)

---

## `main(arduino_port=None, arduino_baud_rate=None, other_port=None, other_baud_rate=None)` { #main }

```python
def main(arduino_port=None, arduino_baud_rate=None, other_port=None, other_baud_rate=None)
```

Point d'entrée principal pour l'application en mode automatique
Cette fonction initialise les appareils, configure l'interface graphique et exécute
la boucle principale qui gère la détection de conductance et la régénération automatiques.
Args:
arduino_port: Port COM de l'Arduino (CO2, température, humidité)
arduino_baud_rate: Débit en bauds pour la communication avec l'Arduino
other_port: Port COM de la carte de régénération
other_baud_rate: Débit en bauds pour la communication avec la carte de régénération

---

## `handle_window_close(event=None)` { #handle_window_close }

```python
def handle_window_close(event=None)
```

Gère l'événement de fermeture de la fenêtre par le bouton X
Args:
event: Événement de fermeture de la fenêtre

---

## `toggle_auto(event)` { #toggle_auto }

```python
def toggle_auto(event)
```

Active ou désactive les mesures automatiques
Cette fonction gère l'activation/désactivation des mesures automatiques,
incluant l'initialisation des fichiers, l'activation du Keithley et la 
gestion des temps de pause pour maintenir des timestamps cohérents.
Args:
event: Événement déclencheur (clic sur le bouton)

---

## `raz_auto(event)` { #raz_auto }

```python
def raz_auto(event)
```

Réinitialise les données de mesure en mode automatique
Cette fonction sauvegarde d'abord les données actuelles dans les fichiers Excel,
puis réinitialise les données de mesure et les graphiques. Elle conserve l'historique
des données déjà enregistrées.
Args:
event: Événement déclencheur (clic sur le bouton)

---

## `set_R0(event)` { #set_r0 }

```python
def set_R0(event)
```

Pas de docstring

---

## `update_read_R0(event)` { #update_read_r0 }

```python
def update_read_R0(event)
```

Pas de docstring

---

## `push_open(event)` { #push_open }

```python
def push_open(event)
```

Pas de docstring

---

## `retract_close(event)` { #retract_close }

```python
def retract_close(event)
```

Pas de docstring

---

## `init_system(event)` { #init_system }

```python
def init_system(event)
```

Pas de docstring

---

## `start_regeneration(event)` { #start_regeneration }

```python
def start_regeneration(event)
```

Gère le clic sur le bouton de régénération
Cette fonction démarre le protocole de régénération du capteur qui implique
le chauffage du capteur pour éliminer les molécules adsorbées.
Args:
event: Événement déclencheur (clic sur le bouton)

---

## `cancel_regeneration(event)` { #cancel_regeneration }

```python
def cancel_regeneration(event)
```

Gère le clic sur le bouton d'annulation de régénération
Cette fonction annule le protocole de régénération en cours et
ramène le système à son état normal.
Args:
event: Événement déclencheur (clic sur le bouton)

---

## `quit_program(event)` { #quit_program }

```python
def quit_program(event)
```

Gère la fermeture propre du programme
Cette fonction sauvegarde les données, propose de renommer le dossier de données,
réinitialise la température consigne, ferme les connexions avec les appareils et
nettoie les ressources graphiques avant de quitter le programme.
Args:
event: Événement déclencheur (clic sur le bouton ou fermeture de fenêtre)

---

## `process_pin_states(line)` { #process_pin_states }

```python
def process_pin_states(line)
```

Traite les informations d'état des pins et met à jour l'interface
Cette fonction analyse les états des pins (capteurs de position) depuis
une ligne de données Arduino et met à jour les indicateurs visuels correspondants.
Args:
line: Ligne de texte contenant les informations d'état des pins
Returns:
bool: True si des états de pins ont été traités, False sinon

---

