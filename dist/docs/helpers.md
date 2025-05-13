# Module `helpers`

*Fichier source : `helpers.py`*

## Fonctions
- [`calculate_slope(x_values, y_values, window_size=10)`](#calculate_slope)
- [`find_indices_for_sliding_window(time_values, current_time, half_window_size)`](#find_indices_for_sliding_window)
- [`parse_co2_data(line)`](#parse_co2_data)
- [`parse_pin_states(line)`](#parse_pin_states)

---

## `calculate_slope(x_values, y_values, window_size=10)` { #calculate_slope }

```python
def calculate_slope(x_values, y_values, window_size=10)
```

Calcule la pente d'une ligne ajustée aux valeurs données en utilisant la régression linéaire
Cette fonction utilise numpy.polyfit pour calculer la pente (coefficient de premier degré)
d'une droite ajustée aux données. Elle est utile pour déterminer le taux de variation
d'un signal, par exemple pour détecter l'augmentation de conductance.
Args:
x_values: Liste des valeurs x (généralement le temps)
y_values: Liste des valeurs y (généralement la conductance)
window_size: Nombre de points à inclure dans le calcul de la pente
Returns:
float: Pente de la ligne (taux de variation)

---

## `find_indices_for_sliding_window(time_values, current_time, half_window_size)` { #find_indices_for_sliding_window }

```python
def find_indices_for_sliding_window(time_values, current_time, half_window_size)
```

Trouve les indices pour une fenêtre glissante centrée autour d'un temps donné
Cette fonction détermine les indices de début et de fin dans une liste de temps
pour créer une fenêtre autour d'un temps spécifique. Elle est utile pour
isoler des segments temporels dans les données de mesure, par exemple pour
analyser une période spécifique avant et après un événement.
Args:
time_values: Liste des valeurs temporelles (timestamps)
current_time: Temps central pour la fenêtre
half_window_size: Demi-taille de la fenêtre en unités de temps
Returns:
tuple: (indice_début, indice_fin) définissant les bornes de la fenêtre

---

## `parse_co2_data(line)` { #parse_co2_data }

```python
def parse_co2_data(line)
```

Analyse les données de CO2, température et humidité à partir d'une ligne Arduino
Cette fonction extrait les valeurs de CO2 (ppm), température (°C) et humidité (%)
à partir d'une ligne de texte envoyée par l'Arduino. Le format attendu est:
"@[valeur_CO2] [valeur_température] [valeur_humidité]"
Args:
line: Ligne lue depuis le port série de l'Arduino
Returns:
tuple: (co2, température, humidité) ou None si l'analyse a échoué

---

## `parse_pin_states(line)` { #parse_pin_states }

```python
def parse_pin_states(line)
```

Analyse les états des pins à partir d'une ligne de données Arduino
Cette fonction extrait l'état des capteurs de position du système à partir
d'une ligne de texte envoyée par l'Arduino. Le format attendu est:
"VR:[HIGH/LOW] VS:[HIGH/LOW] TO:[HIGH/LOW] TF:[HIGH/LOW]"
où:
- VR: Vérin Rentré
- VS: Vérin Sorti
- TO: Trappe Ouverte
- TF: Trappe Fermée
Args:
line: Ligne lue depuis le port série contenant les états des pins
Returns:
dict: Dictionnaire des états des pins {'vr': bool, 'vs': bool, 'to': bool, 'tf': bool}
ou None si l'analyse a échoué

---

