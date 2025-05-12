# Module `keithley_device`

*Fichier source : `keithley_device.py`*

## Fonctions
- [`_custom_excepthook(self, etype, evalue, etraceback)`](#_custom_excepthook)
- [`__init__(self, gpib_address=KEITHLEY_GPIB_ADDRESS)`](#__init__)
- [`connect(self)`](#connect)
- [`configure(self)`](#configure)
- [`read_resistance(self)`](#read_resistance)
- [`_async_delay(self, seconds)`](#_async_delay)
- [`turn_output_on(self)`](#turn_output_on)
- [`turn_output_off(self)`](#turn_output_off)
- [`close(self)`](#close)
- [`__del__(self)`](#__del__)

---

## `_custom_excepthook(self, etype, evalue, etraceback)` { #_custom_excepthook }

```python
def _custom_excepthook(self, etype, evalue, etraceback)
```

Pas de docstring

---

## `__init__(self, gpib_address=KEITHLEY_GPIB_ADDRESS)` { #__init__ }

```python
def __init__(self, gpib_address=KEITHLEY_GPIB_ADDRESS)
```

Initialise l'appareil Keithley
Args:
gpib_address: Adresse GPIB de l'appareil

---

## `connect(self)` { #connect }

```python
def connect(self)
```

Établit la connexion à l'appareil Keithley via GPIB
Returns:
bool: True si la connexion a réussi, False sinon

---

## `configure(self)` { #configure }

```python
def configure(self)
```

Configure l'appareil Keithley avec les paramètres nécessaires pour les mesures de résistance
Returns:
bool: True si la configuration a réussi, False sinon

---

## `read_resistance(self)` { #read_resistance }

```python
def read_resistance(self)
```

Lire la résistance depuis le Keithley
Returns:
float: Valeur de résistance en ohms, ou None en cas d'erreur

---

## `_async_delay(self, seconds)` { #_async_delay }

```python
def _async_delay(self, seconds)
```

Délai asynchrone pour ne pas bloquer l'exécution

---

## `turn_output_on(self)` { #turn_output_on }

```python
def turn_output_on(self)
```

Activer la sortie du Keithley

---

## `turn_output_off(self)` { #turn_output_off }

```python
def turn_output_off(self)
```

Désactiver la sortie du Keithley

---

## `close(self)` { #close }

```python
def close(self)
```

Fermer la connexion au Keithley

---

## `__del__(self)` { #__del__ }

```python
def __del__(self)
```

Destructeur - assure que la connexion est fermée lors de la suppression de l'objet

---

