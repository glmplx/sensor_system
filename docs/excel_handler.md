# Module `excel_handler`

*Fichier source : `excel_handler.py`*

## Fonctions
- [`__init__(self, mode="manual", base_dir=None)`](#__init__)
- [`initialize_folder(self)`](#initialize_folder)
- [`initialize_file(self, file_type)`](#initialize_file)
- [`_create_workbook_with_info(self, file_path, file_type)`](#_create_workbook_with_info)
- [`add_sheet_to_excel(self, file_path, sheet_name, data)`](#add_sheet_to_excel)
- [`_update_cumulative_sheet(self, file_path)`](#_update_cumulative_sheet)
- [`raz_conductance_data(self, timeList, conductanceList, resistanceList)`](#raz_conductance_data)
- [`raz_co2_temp_humidity_data(self, co2_timestamps, co2_values, temp_timestamps, temp_values, humidity_timestamps, humidity_values)`](#raz_co2_temp_humidity_data)
- [`raz_temp_res_data(self, timestamps, temperatures, tcons_values)`](#raz_temp_res_data)
- [`save_conductance_data(self, timeList, conductanceList, resistanceList, sheet_name=None)`](#save_conductance_data)
- [`save_co2_temp_humidity_data(self, co2_timestamps, co2_values, temp_timestamps, temp_values, humidity_timestamps, humidity_values, delta_c=None, carbon_mass=None, sheet_name=None)`](#save_co2_temp_humidity_data)
- [`save_temp_res_data(self, timestamps, temperatures, tcons_values, sheet_name=None)`](#save_temp_res_data)
- [`save_all_data(self, measurement_manager)`](#save_all_data)
- [`rename_test_folder(self, new_name)`](#rename_test_folder)
- [`add_charts_to_excel(self, file_path)`](#add_charts_to_excel)
- [`_add_conductance_charts(self, workbook)`](#_add_conductance_charts)
- [`_add_co2_temp_humidity_charts(self, workbook)`](#_add_co2_temp_humidity_charts)
- [`_add_temp_res_charts(self, workbook)`](#_add_temp_res_charts)
- [`_should_create_cumulative_sheet(self, file_path)`](#_should_create_cumulative_sheet)

---

## `__init__(self, mode="manual", base_dir=None)` { #__init__ }

```python
def __init__(self, mode="manual", base_dir=None)
```

Initialiser le gestionnaire Excel
Args:
mode: Mode de fonctionnement, soit "manual" soit "auto"
base_dir: Répertoire de base pour les fichiers Excel (par défaut: EXCEL_BASE_DIR)

---

## `initialize_folder(self)` { #initialize_folder }

```python
def initialize_folder(self)
```

Initialise le dossier de test basé sur la date et l'heure actuelles
Returns:
str: Chemin vers le dossier de test créé

---

## `initialize_file(self, file_type)` { #initialize_file }

```python
def initialize_file(self, file_type)
```

Initialise un fichier Excel pour un type de données spécifique
Args:
file_type: Type de fichier de données à initialiser ('conductance', 'co2_temp_humidity', 'temp_res')
Returns:
str: Chemin vers le fichier initialisé

---

## `_create_workbook_with_info(self, file_path, file_type)` { #_create_workbook_with_info }

```python
def _create_workbook_with_info(self, file_path, file_type)
```

Crée un classeur Excel sans feuille initiale
Args:
file_path: Chemin du fichier à créer
file_type: Type de fichier (non utilisé)
Returns:
str: Chemin du fichier créé

---

## `add_sheet_to_excel(self, file_path, sheet_name, data)` { #add_sheet_to_excel }

```python
def add_sheet_to_excel(self, file_path, sheet_name, data)
```

Pas de docstring

---

## `_update_cumulative_sheet(self, file_path)` { #_update_cumulative_sheet }

```python
def _update_cumulative_sheet(self, file_path)
```

Met à jour ou crée la feuille 'Essais cumulés' de manière plus robuste

---

## `raz_conductance_data(self, timeList, conductanceList, resistanceList)` { #raz_conductance_data }

```python
def raz_conductance_data(self, timeList, conductanceList, resistanceList)
```

Prépare les données pour un nouvel essai sans sauvegarder immédiatement

---

## `raz_co2_temp_humidity_data(self, co2_timestamps, co2_values, temp_timestamps, temp_values, humidity_timestamps, humidity_values)` { #raz_co2_temp_humidity_data }

```python
def raz_co2_temp_humidity_data(self, co2_timestamps, co2_values, temp_timestamps, temp_values, humidity_timestamps, humidity_values)
```

Prépare les données CO2/temp/humidity pour un nouvel essai

---

## `raz_temp_res_data(self, timestamps, temperatures, tcons_values)` { #raz_temp_res_data }

```python
def raz_temp_res_data(self, timestamps, temperatures, tcons_values)
```

Prépare les données temp/resistance pour un nouvel essai

---

## `save_conductance_data(self, timeList, conductanceList, resistanceList, sheet_name=None)` { #save_conductance_data }

```python
def save_conductance_data(self, timeList, conductanceList, resistanceList, sheet_name=None)
```

Sauvegarde les données de conductance dans le fichier Excel
Args:
timeList: Liste des timestamps (en secondes)
conductanceList: Liste des valeurs de conductance (en µS)
resistanceList: Liste des valeurs de résistance (en Ohms)
sheet_name: Nom de la feuille à utiliser (ou None pour créer un nom basé sur l'horodatage)
Returns:
bool: True si la sauvegarde a réussi, False sinon

---

## `save_co2_temp_humidity_data(self, co2_timestamps, co2_values, temp_timestamps, temp_values, humidity_timestamps, humidity_values, delta_c=None, carbon_mass=None, sheet_name=None)` { #save_co2_temp_humidity_data }

```python
def save_co2_temp_humidity_data(self, co2_timestamps, co2_values, temp_timestamps, temp_values, humidity_timestamps, humidity_values, delta_c=None, carbon_mass=None, sheet_name=None)
```

Sauvegarde les données de CO2, température et humidité dans le fichier Excel
Args:
co2_timestamps: Liste des timestamps CO2 (en secondes)
co2_values: Liste des valeurs CO2 (en ppm)
temp_timestamps: Liste des timestamps température (en secondes)
temp_values: Liste des valeurs température (en °C)
humidity_timestamps: Liste des timestamps humidité (en secondes)
humidity_values: Liste des valeurs humidité (en %)
delta_c: Différence de CO2 entre début et fin (en ppm, optionnel)
carbon_mass: Masse de carbone calculée (en µg, optionnel)
sheet_name: Nom de la feuille à utiliser (ou None pour créer un nom basé sur l'horodatage)
Returns:
bool: True si la sauvegarde a réussi, False sinon

---

## `save_temp_res_data(self, timestamps, temperatures, tcons_values, sheet_name=None)` { #save_temp_res_data }

```python
def save_temp_res_data(self, timestamps, temperatures, tcons_values, sheet_name=None)
```

Sauvegarde les données temp/resistance
Args:
timestamps: Liste des timestamps
temperatures: Liste des valeurs de température
tcons_values: Liste des valeurs de consigne de température
sheet_name: Nom de la feuille à utiliser (ou None pour créer un nom basé sur l'horodatage)

---

## `save_all_data(self, measurement_manager)` { #save_all_data }

```python
def save_all_data(self, measurement_manager)
```

Save all data to Excel files
Args:
measurement_manager: MeasurementManager instance with data
Returns:
bool: True if all data was saved successfully, False otherwise

---

## `rename_test_folder(self, new_name)` { #rename_test_folder }

```python
def rename_test_folder(self, new_name)
```

Rename the test folder with a custom name
Args:
new_name: New name for the test folder
Returns:
bool: True if the folder was renamed successfully, False otherwise

---

## `add_charts_to_excel(self, file_path)` { #add_charts_to_excel }

```python
def add_charts_to_excel(self, file_path)
```

Ajoute des graphiques aux feuilles Excel en fonction du type de données
Args:
file_path: Chemin du fichier Excel
Returns:
bool: True si les graphiques ont été ajoutés avec succès, False sinon

---

## `_add_conductance_charts(self, workbook)` { #_add_conductance_charts }

```python
def _add_conductance_charts(self, workbook)
```

Ajoute les graphiques pour les données de conductance
Args:
workbook: Classeur Excel ouvert

---

## `_add_co2_temp_humidity_charts(self, workbook)` { #_add_co2_temp_humidity_charts }

```python
def _add_co2_temp_humidity_charts(self, workbook)
```

Ajoute les graphiques pour les données CO2/température/humidité
Args:
workbook: Classeur Excel ouvert

---

## `_add_temp_res_charts(self, workbook)` { #_add_temp_res_charts }

```python
def _add_temp_res_charts(self, workbook)
```

Ajoute les graphiques pour les données température/résistance
Args:
workbook: Classeur Excel ouvert

---

## `_should_create_cumulative_sheet(self, file_path)` { #_should_create_cumulative_sheet }

```python
def _should_create_cumulative_sheet(self, file_path)
```

Détermine si une feuille 'Essais cumulés' doit être créée

---

