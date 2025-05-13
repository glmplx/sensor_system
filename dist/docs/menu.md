# Module `menu`

*Fichier source : `menu.py`*

## Fonctions
- [`__init__(self)`](#__init__)
- [`scan_ports(self)`](#scan_ports)
- [`refresh_ports(self, show_message=True)`](#refresh_ports)
- [`setup_ui(self)`](#setup_ui)
- [`toggle_location_selector(*args)`](#toggle_location_selector)
- [`browse_directory()`](#browse_directory)
- [`set_manual_mode(self)`](#set_manual_mode)
- [`set_auto_mode(self)`](#set_auto_mode)
- [`check_port_selections(self, arduino_port_str, other_port_str)`](#check_port_selections)
- [`launch_program(self)`](#launch_program)
- [`open_documentation(self)`](#open_documentation)
- [`run_mkdocs_server()`](#run_mkdocs_server)
- [`check_server_status(attempt=1, max_attempts=10)`](#check_server_status)
- [`_find_available_port(self, start_port=8000, end_port=8020)`](#_find_available_port)
- [`_kill_mkdocs_server(self)`](#_kill_mkdocs_server)
- [`open_config_window(self)`](#open_config_window)
- [`quit_application(self)`](#quit_application)
- [`run(self)`](#run)
- [`__init__(self, parent)`](#__init__)
- [`setup_ui(self)`](#setup_ui)
- [`reset_values(self)`](#reset_values)
- [`save_values(self)`](#save_values)

---

## `__init__(self)` { #__init__ }

```python
def __init__(self)
```

Initialiser l'interface utilisateur du menu

---

## `scan_ports(self)` { #scan_ports }

```python
def scan_ports(self)
```

Analyse les ports COM disponibles et identifie les types d'appareils
Returns:
tuple: (ports_info, ports_display, arduino_port_index, regen_port_index)
- ports_info: Liste de tuples (port.device, port.description)
- ports_display: Liste des ports formatés pour l'affichage
- arduino_port_index: Index du port Arduino détecté ou None
- regen_port_index: Index du port de régénération détecté ou None

---

## `refresh_ports(self, show_message=True)` { #refresh_ports }

```python
def refresh_ports(self, show_message=True)
```

Actualiser la liste des ports COM disponibles
Args:
show_message: Afficher un message de confirmation après l'actualisation
Returns:
dict: Informations sur les ports détectés (pour usage externe)

---

## `setup_ui(self)` { #setup_ui }

```python
def setup_ui(self)
```

Configurer les éléments de l'interface utilisateur

---

## `toggle_location_selector(*args)` { #toggle_location_selector }

```python
def toggle_location_selector(*args)
```

Afficher ou masquer le champ de saisie de l'emplacement de sauvegarde

---

## `browse_directory()` { #browse_directory }

```python
def browse_directory()
```

Ouvrir le sélecteur de dossier pour choisir l'emplacement de sauvegarde

---

## `set_manual_mode(self)` { #set_manual_mode }

```python
def set_manual_mode(self)
```

Définir le mode manuel et décocher le mode automatique

---

## `set_auto_mode(self)` { #set_auto_mode }

```python
def set_auto_mode(self)
```

Définir le mode automatique et décocher le mode manuel

---

## `check_port_selections(self, arduino_port_str, other_port_str)` { #check_port_selections }

```python
def check_port_selections(self, arduino_port_str, other_port_str)
```

Vérifie que les ports sélectionnés correspondent aux bonnes cartes
Args:
arduino_port_str: chaîne du port Arduino sélectionné
other_port_str: chaîne du port de régénération sélectionné
Returns:
bool: True si les sélections sont valides ou si l'utilisateur confirme
str: "swap" si l'utilisateur choisit d'échanger les ports

---

## `launch_program(self)` { #launch_program }

```python
def launch_program(self)
```

Lancer le mode de programme sélectionné

---

## `open_documentation(self)` { #open_documentation }

```python
def open_documentation(self)
```

Lance mkdocs serve et ouvre la documentation dans un navigateur

---

## `run_mkdocs_server()` { #run_mkdocs_server }

```python
def run_mkdocs_server()
```

Lancer le serveur mkdocs dans un thread séparé

---

## `check_server_status(attempt=1, max_attempts=10)` { #check_server_status }

```python
def check_server_status(attempt=1, max_attempts=10)
```

Vérifier si le serveur MkDocs est prêt

---

## `_find_available_port(self, start_port=8000, end_port=8020)` { #_find_available_port }

```python
def _find_available_port(self, start_port=8000, end_port=8020)
```

Trouve un port disponible dans la plage spécifiée

---

## `_kill_mkdocs_server(self)` { #_kill_mkdocs_server }

```python
def _kill_mkdocs_server(self)
```

Arrête le serveur MkDocs s'il est en cours d'exécution

---

## `open_config_window(self)` { #open_config_window }

```python
def open_config_window(self)
```

Ouvre la fenêtre de configuration des constantes

---

## `quit_application(self)` { #quit_application }

```python
def quit_application(self)
```

Ferme l'application proprement et termine le processus

---

## `run(self)` { #run }

```python
def run(self)
```

Exécuter la boucle principale de l'interface utilisateur

---

## `__init__(self, parent)` { #__init__ }

```python
def __init__(self, parent)
```

Initialise la fenêtre de configuration des constantes
Args:
parent: Fenêtre parente (MenuUI) qui a créé cette fenêtre

---

## `setup_ui(self)` { #setup_ui }

```python
def setup_ui(self)
```

Configurer l'interface utilisateur

---

## `reset_values(self)` { #reset_values }

```python
def reset_values(self)
```

Réinitialise les champs aux valeurs par défaut

---

## `save_values(self)` { #save_values }

```python
def save_values(self)
```

Sauvegarde les valeurs modifiées pour la session en cours et dans les fichiers appropriés

---

