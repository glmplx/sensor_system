# Module `menu`

*Fichier source : `menu.py`*

## Fonctions
- [`__init__(self)`](#__init__)
- [`scan_ports(self)`](#scan_ports)
- [`refresh_ports(self, show_message=True)`](#refresh_ports)
- [`setup_ui(self)`](#setup_ui)
- [`set_manual_mode(self)`](#set_manual_mode)
- [`set_auto_mode(self)`](#set_auto_mode)
- [`check_port_selections(self, arduino_port_str, other_port_str)`](#check_port_selections)
- [`launch_program(self)`](#launch_program)
- [`open_documentation(self)`](#open_documentation)
- [`quit_application(self)`](#quit_application)
- [`run(self)`](#run)

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

Ouvre le fichier de documentation

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

