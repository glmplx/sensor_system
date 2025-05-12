# Module `arduino_device`

*Fichier source : `arduino_device.py`*

## Fonctions
- [`__init__(self, port=None, baud_rate=115200, timeout=2)`](#__init__)
- [`connect(self)`](#connect)
- [`read_line(self)`](#read_line)
- [`send_command(self, command)`](#send_command)
- [`close(self)`](#close)

---

## `__init__(self, port=None, baud_rate=115200, timeout=2)` { #__init__ }

```python
def __init__(self, port=None, baud_rate=115200, timeout=2)
```

Initialise l'appareil Arduino
Args:
port: Port série à connecter
baud_rate: Vitesse en bauds pour la connexion série
timeout: Délai d'expiration pour les opérations série en secondes

---

## `connect(self)` { #connect }

```python
def connect(self)
```

Établit la connexion à l'appareil Arduino via le port série
Returns:
bool: True si la connexion a réussi, False sinon

---

## `read_line(self)` { #read_line }

```python
def read_line(self)
```

Lire une ligne depuis l'Arduino
Returns:
str: La ligne lue, ou None en cas d'erreur

---

## `send_command(self, command)` { #send_command }

```python
def send_command(self, command)
```

Envoyer une commande à l'Arduino
Args:
command: La commande à envoyer
Returns:
bool: True si la commande a été envoyée avec succès, False sinon

---

## `close(self)` { #close }

```python
def close(self)
```

Ferme proprement la connexion à l'Arduino
Returns:
bool: True si la fermeture a réussi ou si l'appareil était déjà fermé, False en cas d'erreur

---

