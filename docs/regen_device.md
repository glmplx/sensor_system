# Module `regen_device`

*Fichier source : `regen_device.py`*

## Fonctions
- [`__init__(self, port=None, baud_rate=115200, timeout=2)`](#__init__)
- [`connect(self)`](#connect)
- [`read_variable(self, command, address)`](#read_variable)
- [`write_parameter(self, command, address, value)`](#write_parameter)
- [`close(self)`](#close)

---

## `__init__(self, port=None, baud_rate=115200, timeout=2)` { #__init__ }

```python
def __init__(self, port=None, baud_rate=115200, timeout=2)
```

Initialise l'appareil de régénération
Args:
port: Port série à connecter
baud_rate: Vitesse en bauds pour la connexion série
timeout: Délai d'expiration pour les opérations série en secondes

---

## `connect(self)` { #connect }

```python
def connect(self)
```

Établit la connexion à l'appareil de régénération
Returns:
bool: True si la connexion a réussi, False sinon

---

## `read_variable(self, command, address)` { #read_variable }

```python
def read_variable(self, command, address)
```

Lire une variable depuis l'appareil de régénération
Args:
command: Caractère de commande (par exemple, 'L')
address: Caractère d'adresse (par exemple, 'a', 'b', 'c', 'd')
Returns:
str: La valeur lue, ou "0.0" en cas d'erreur (jamais None)

---

## `write_parameter(self, command, address, value)` { #write_parameter }

```python
def write_parameter(self, command, address, value)
```

Écrire un paramètre dans l'appareil de régénération
Args:
command: Caractère de commande (par exemple, 'e')
address: Caractère d'adresse (par exemple, 'a', 'b')
value: Valeur à écrire
Returns:
bool: True si le paramètre a été écrit avec succès, False sinon

---

## `close(self)` { #close }

```python
def close(self)
```

Ferme proprement la connexion à l'appareil de régénération
Returns:
bool: True si la fermeture a réussi ou si l'appareil était déjà fermé, False en cas d'erreur

---

