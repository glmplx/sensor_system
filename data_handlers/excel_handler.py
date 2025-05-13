"""
Gestionnaire de fichiers Excel pour le stockage et l'exportation des données de mesure.
Permet l'organisation, la sauvegarde et la visualisation des données sous forme de graphiques.
"""

import os
import sys
import pandas as pd
from datetime import datetime
from openpyxl import Workbook, load_workbook
from openpyxl.chart import LineChart, Reference
from openpyxl.chart.axis import DateAxis

# Ajout du répertoire parent au chemin d'importation pour résoudre les dépendances
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.constants import EXCEL_BASE_DIR

class ExcelHandler:
    """Gère les opérations de fichiers Excel pour le stockage, l'organisation et la visualisation des données de mesure"""
    
    def __init__(self, mode="manual", base_dir=None):
        """
        Initialiser le gestionnaire Excel

        Args:
            mode: Mode de fonctionnement, soit "manual" soit "auto"
            base_dir: Répertoire de base pour les fichiers Excel (par défaut: EXCEL_BASE_DIR)
        """
        self.mode = mode
        self.base_dir = base_dir if base_dir else EXCEL_BASE_DIR
        self.test_folder_path = None
        self.conductance_file = None
        self.co2_temp_humidity_file = None
        self.temp_res_file = None
        
        # Compteurs pour suivre le nombre de séries de données
        self.conductance_series_count = 0
        self.co2_temp_humidity_series_count = 0 
        self.temp_res_series_count = 0

        # Pour suivre les feuilles actives
        self.active_conductance_sheet = None
        self.active_co2_temp_humidity_sheet = None
        self.active_temp_res_sheet = None
        
        # Pour indiquer si un RAZ a été effectué et si une nouvelle feuille est nécessaire
        self.new_conductance_sheet_needed = True
        self.new_co2_temp_humidity_sheet_needed = True  
        self.new_temp_res_sheet_needed = True

        
        # Stocke les données accumulées entre les sessions de réinitialisation (RAZ)
        self.accumulated_conductance_data = {
            'Minutes': [],
            'Temps (s)': [],
            'Conductance (µS)': [],
            'Resistance (Ohms)': []
        }
        
        self.accumulated_co2_temp_humidity_data = {
            'Minutes': [],
            'Temps (s)': [],
            'CO2 (ppm)': [],
            'Température (°C)': [],
            'Humidité (%)': [],
            'deltaC (ppm)': [],
            'masseC (µg)': []
        }
        
        self.accumulated_temp_res_data = {
            'Minutes': [],
            'Temps (s)': [],
            'Température mesurée': [],
            'Tcons': []
        }
    
    def initialize_folder(self):
        """
        Initialise le dossier de test basé sur la date et l'heure actuelles
        
        Returns:
            str: Chemin vers le dossier de test créé
        """
        # Récupérer le répertoire d'exécution de l'application
        if getattr(sys, 'frozen', False):
            # Exécution en tant qu'exécutable compilé
            application_path = os.path.dirname(sys.executable)
        else:
            # Exécution en tant que script Python
            application_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
        excel_folder_path = os.path.join(application_path, self.base_dir)
        
        # Essayer d'abord le dossier de l'application (où se trouve l'exécutable)
        try:
            if not os.path.exists(excel_folder_path):
                os.makedirs(excel_folder_path, exist_ok=True)
            
            mode_prefix = "Manual" if self.mode == "manual" else "Auto"
            test_folder_name = f"Test-{mode_prefix}-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
            self.test_folder_path = os.path.join(excel_folder_path, test_folder_name)
            
            os.makedirs(self.test_folder_path, exist_ok=True)
            print(f"Using application folder for data storage: {self.test_folder_path}")
        except Exception as e:
            # If application folder fails, try user documents folder
            print(f"Failed to create directory in application folder: {e}, trying Documents folder...")
            try:
                # Try Documents folder as fallback
                user_docs = os.path.join(os.path.expanduser('~'), 'Documents', 'ASNR', self.base_dir)
                if not os.path.exists(user_docs):
                    os.makedirs(user_docs, exist_ok=True)
                    
                mode_prefix = "Manual" if self.mode == "manual" else "Auto"
                test_folder_name = f"Test-{mode_prefix}-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
                self.test_folder_path = os.path.join(user_docs, test_folder_name)
                
                os.makedirs(self.test_folder_path, exist_ok=True)
                print(f"Using Documents folder for data storage: {self.test_folder_path}")
            except Exception as e:
                # Last resort: use temp directory
                import tempfile
                temp_dir = tempfile.gettempdir()
                print(f"Failed to create directory in Documents folder: {e}, using temp directory: {temp_dir}")

                mode_prefix = "Manual" if self.mode == "manual" else "Auto"
                test_folder_name = f"Test-{mode_prefix}-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
                self.test_folder_path = os.path.join(temp_dir, 'ASNR', self.base_dir, test_folder_name)
                
                os.makedirs(os.path.dirname(self.test_folder_path), exist_ok=True)
                os.makedirs(self.test_folder_path, exist_ok=True)
                print(f"Using temp directory for data storage: {self.test_folder_path}")
        return self.test_folder_path
    
    def initialize_file(self, file_type):
        """
        Initialise un fichier Excel pour un type de données spécifique
        
        Args:
            file_type: Type de fichier de données à initialiser ('conductance', 'co2_temp_humidity', 'temp_res')
            
        Returns:
            str: Chemin vers le fichier initialisé
        """
        if not self.test_folder_path:
            self.initialize_folder()
        
        # Obtenir la date et l'heure actuelles pour le nom du fichier
        current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        
        # Créer le fichier approprié en fonction du type
        if file_type == "conductance":
            self.conductance_file = os.path.join(self.test_folder_path, f'conductance_{current_datetime}.xlsx')
            return self._create_workbook_with_info(self.conductance_file, file_type)
        
        elif file_type == "co2_temp_humidity":
            self.co2_temp_humidity_file = os.path.join(self.test_folder_path, f'co2_temp_humidity_{current_datetime}.xlsx')
            return self._create_workbook_with_info(self.co2_temp_humidity_file, file_type)
        
        elif file_type == "temp_res":
            self.temp_res_file = os.path.join(self.test_folder_path, f'temperature_resistance_{current_datetime}.xlsx')
            return self._create_workbook_with_info(self.temp_res_file, file_type)
        
        return None
        
    def _create_workbook_with_info(self, file_path, file_type):
        """
        Crée un classeur Excel sans feuille initiale
        
        Args:
            file_path: Chemin du fichier à créer
            file_type: Type de fichier (non utilisé)
            
        Returns:
            str: Chemin du fichier créé
        """
        # Create a workbook with the default sheet
        wb = Workbook()
        
        # Garder la feuille par défaut mais la renommer avec un nom temporaire
        # Cette feuille sera ensuite supprimée lors de l'ajout de vraies données
        ws = wb.active
        ws.title = "_temp"
        
        # Sauvegarder le classeur vide
        wb.save(file_path)
        return file_path
        
    
    def add_sheet_to_excel(self, file_path, sheet_name, data):
        if not os.path.exists(file_path):
            print(f"Erreur: Le fichier {file_path} n'existe pas")
            return False
            
        try:
            wb = load_workbook(file_path)
            
            # Supprimer la feuille temporaire si elle existe
            if "_temp" in wb.sheetnames:
                wb.remove(wb["_temp"])
            
            # Vérifier si la feuille existe déjà
            sheet_exists = sheet_name in wb.sheetnames
            
            # Cas spécial pour "AutoSave": on remplace la feuille existante
            if sheet_exists and sheet_name == "AutoSave":
                # Supprimer la feuille existante pour la recréer
                wb.remove(wb[sheet_name])
                ws = wb.create_sheet(sheet_name)
                print(f"Mise à jour de la feuille 'AutoSave' existante")
            elif sheet_exists:
                # Générer un nom unique en ajoutant un suffixe numérique
                base_name = sheet_name
                counter = 1
                while sheet_name in wb.sheetnames:
                    sheet_name = f"{base_name}_{counter}"
                    counter += 1
                
                # Créer la nouvelle feuille avec le nom généré
                ws = wb.create_sheet(sheet_name)
            else:
                # Créer la nouvelle feuille
                ws = wb.create_sheet(sheet_name)
            
            # Ajouter les données
            for col_num, (key, values) in enumerate(data.items(), 1):
                # Vérifier que les valeurs existent et sont non vides
                if values:
                    ws.cell(row=1, column=col_num, value=key)
                    for row_num, value in enumerate(values, 2):
                        ws.cell(row=row_num, column=col_num, value=value)
            
            
            # Mettre à jour "Essais cumulés" si nécessaire et qu'on a plus d'une feuille de données
            # On ne met pas à jour la feuille cumulée si le nom de feuille est "AutoSave"
            if self._should_create_cumulative_sheet(file_path) and sheet_name != "AutoSave":
                # Sauvegarder avant de mettre à jour la feuille cumulée
                wb.save(file_path)
                self._update_cumulative_sheet(file_path)
                return True
            
            # Sauvegarder les modifications
            wb.save(file_path)
            return True
        except Exception as e:
            print(f"Error adding sheet to Excel file: {e}")
            return False
        
    def _update_cumulative_sheet(self, file_path):
        """
        Met à jour ou crée la feuille 'Essais cumulés' de manière plus robuste
        """
        try:
            # Déterminer le type de données basé sur le nom du fichier
            file_type = None
            if "conductance" in os.path.basename(file_path).lower():
                cumulative_data = self.accumulated_conductance_data
                required_fields = ['Minutes', 'Temps (s)', 'Conductance (µS)', 'Resistance (Ohms)']
                series_count = self.conductance_series_count
                file_type = "conductance"
            elif "co2_temp_humidity" in os.path.basename(file_path).lower():
                cumulative_data = self.accumulated_co2_temp_humidity_data
                required_fields = ['Minutes', 'Temps (s)', 'CO2 (ppm)', 'Température (°C)', 'Humidité (%)']
                series_count = self.co2_temp_humidity_series_count
                file_type = "co2_temp_humidity"
            elif "temperature_resistance" in os.path.basename(file_path).lower():
                cumulative_data = self.accumulated_temp_res_data
                required_fields = ['Minutes', 'Temps (s)', 'Température mesurée', 'Tcons']
                series_count = self.temp_res_series_count
                file_type = "temp_res"
            else:
                return
            
            # Vérifier que nous avons des données accumulées valides
            has_cumulative_data = all(key in cumulative_data for key in required_fields)
            has_data = any(len(cumulative_data.get(key, [])) > 0 for key in required_fields)
            
            if not has_cumulative_data or not has_data:
                return
                
            # Ne créer la feuille "Essais cumulés" que s'il y a plus d'une série de mesures
            if series_count < 2:
                return
                
            # Charger le fichier Excel
            wb = load_workbook(file_path)
            
            # Déterminer les feuilles de données (excluant celle cumulée, la temporaire et AutoSave)
            data_sheets = [s for s in wb.sheetnames if s != "Essais cumulés" and s != "_temp" and s != "AutoSave"]
            
            # Supprimer l'ancienne feuille "Essais cumulés" si elle existe
            if "Essais cumulés" in wb.sheetnames:
                wb.remove(wb["Essais cumulés"])
            
            # Créer la nouvelle feuille "Essais cumulés"
            ws = wb.create_sheet("Essais cumulés")
            
            # Écrire les en-têtes
            for col_num, header in enumerate(required_fields, 1):
                ws.cell(row=1, column=col_num, value=header)
            
            # Vérifier si les données accumulées sont cohérentes
            data_lengths = [len(cumulative_data.get(key, [])) for key in required_fields]
            
            if len(set(data_lengths)) > 1:
                # Les données ne sont pas de même longueur - trouver la longueur maximale valide
                valid_lengths = [l for l in data_lengths if l > 0]
                if not valid_lengths:
                    return
                max_rows = max(valid_lengths)
            else:
                # Toutes les données ont la même longueur
                max_rows = data_lengths[0] if data_lengths else 0
            
            # Écrire les données
            for row_num in range(max_rows):
                for col_num, key in enumerate(required_fields, 1):
                    if row_num < len(cumulative_data.get(key, [])):
                        ws.cell(row=row_num+2, column=col_num, value=cumulative_data[key][row_num])
            
            # Sauvegarder les modifications
            wb.save(file_path)
            
        except Exception as e:
            print(f"Erreur lors de la mise à jour de la feuille cumulée: {e}", exc_info=True)

    def raz_conductance_data(self, timeList, conductanceList, resistanceList):
        """Prépare les données pour un nouvel essai sans sauvegarder immédiatement"""
        if timeList and len(timeList) > 0:
            # Ajouter aux données accumulées
            lastTime = 0
            if self.accumulated_conductance_data['Temps (s)']:
                lastTime = self.accumulated_conductance_data['Temps (s)'][-1]
            
            self.accumulated_conductance_data['Minutes'].extend([(lastTime + t) / 60.0 for t in timeList])
            self.accumulated_conductance_data['Temps (s)'].extend([lastTime + t for t in timeList])
            self.accumulated_conductance_data['Conductance (µS)'].extend(conductanceList)
            self.accumulated_conductance_data['Resistance (Ohms)'].extend(resistanceList)
            
            # Marquer qu'une nouvelle feuille sera nécessaire au prochain enregistrement
            self.new_conductance_sheet_needed = True
        
        return True
    
    def raz_co2_temp_humidity_data(self, co2_timestamps, co2_values, temp_timestamps, temp_values, humidity_timestamps, humidity_values):
        """Prépare les données CO2/temp/humidity pour un nouvel essai"""
        if co2_timestamps and len(co2_timestamps) > 0:
            # Ajouter aux données accumulées
            lastTime = 0
            if self.accumulated_co2_temp_humidity_data['Temps (s)']:
                lastTime = self.accumulated_co2_temp_humidity_data['Temps (s)'][-1]
            
            timestamps = co2_timestamps if co2_timestamps else (temp_timestamps if temp_timestamps else humidity_timestamps)
            
            self.accumulated_co2_temp_humidity_data['Minutes'].extend([(lastTime + t) / 60.0 for t in timestamps])
            self.accumulated_co2_temp_humidity_data['Temps (s)'].extend([lastTime + t for t in timestamps])
            self.accumulated_co2_temp_humidity_data['CO2 (ppm)'].extend(co2_values)
            self.accumulated_co2_temp_humidity_data['Température (°C)'].extend(temp_values)
            self.accumulated_co2_temp_humidity_data['Humidité (%)'].extend(humidity_values)
            
            # Marquer qu'une nouvelle feuille sera nécessaire au prochain enregistrement
            self.new_co2_temp_humidity_sheet_needed = True
        
        return True

    def raz_temp_res_data(self, timestamps, temperatures, tcons_values):
        """Prépare les données temp/resistance pour un nouvel essai"""
        if timestamps and len(timestamps) > 0:
            # Ajouter aux données accumulées
            lastTime = 0
            if self.accumulated_temp_res_data['Temps (s)']:
                lastTime = self.accumulated_temp_res_data['Temps (s)'][-1]
            
            self.accumulated_temp_res_data['Minutes'].extend([(lastTime + t) / 60.0 for t in timestamps])
            self.accumulated_temp_res_data['Temps (s)'].extend([lastTime + t for t in timestamps])
            self.accumulated_temp_res_data['Température mesurée'].extend(temperatures)
            self.accumulated_temp_res_data['Tcons'].extend(tcons_values)
            
            # Marquer qu'une nouvelle feuille sera nécessaire au prochain enregistrement
            self.new_temp_res_sheet_needed = True
        
        return True
    
    def save_conductance_data(self, timeList, conductanceList, resistanceList, sheet_name=None):
        """
        Sauvegarde les données de conductance dans le fichier Excel
        
        Args:
            timeList: Liste des timestamps (en secondes)
            conductanceList: Liste des valeurs de conductance (en µS)
            resistanceList: Liste des valeurs de résistance (en Ohms)
            sheet_name: Nom de la feuille à utiliser (ou None pour créer un nom basé sur l'horodatage)
            
        Returns:
            bool: True si la sauvegarde a réussi, False sinon
        """
        if not self.conductance_file:
            self.initialize_file("conductance")
        
        if not timeList or len(timeList) == 0:
            return False
        
        # Déterminer si on doit créer une nouvelle feuille ou utiliser l'existante
        if sheet_name == "AutoSave":
            # Pour les autosaves, toujours utiliser la feuille AutoSave
            pass
        elif not self.new_conductance_sheet_needed and self.active_conductance_sheet:
            # Utiliser la feuille active si pas besoin de nouvelle feuille
            sheet_name = self.active_conductance_sheet
        else:
            # Si aucun nom de feuille n'est fourni ou si une nouvelle est nécessaire, créer un nom
            if sheet_name is None:
                sheet_name = f"Cond_{datetime.now().strftime('%H%M%S')}"
                
            # Vérifier si cette feuille existe déjà
            try:
                wb = load_workbook(self.conductance_file)
                if sheet_name in wb.sheetnames and sheet_name != "AutoSave":
                    # Génère un nom alternatif en ajoutant un suffixe (sauf pour AutoSave)
                    sheet_name = f"{sheet_name}_{self.conductance_series_count}"
            except Exception as e:
                print(f"Warning: Couldn't check for duplicate sheet names: {e}")
                
            # Mémoriser comme feuille active
            self.active_conductance_sheet = sheet_name
            self.new_conductance_sheet_needed = False
        
        # Définir les données à sauvegarder
        data = {}
        
        # Pour les données de la feuille courante, vérifier s'il faut ajouter le décalage temporel
        try:
            if sheet_name != "AutoSave" and sheet_name in load_workbook(self.conductance_file).sheetnames:
                # La feuille existe déjà, il faut maintenir la continuité temporelle
                wb = load_workbook(self.conductance_file)
                ws = wb[sheet_name]
                
                # Déterminer le dernier temps enregistré
                last_row = ws.max_row
                if last_row > 1:  # Si la feuille contient déjà des données
                    last_time = ws.cell(row=last_row, column=2).value  # Colonne 2 = Temps (s)
                    if last_time is not None:
                        # Ajuster les timestamps pour continuer après le dernier point
                        data['Minutes'] = [(last_time + t) / 60.0 for t in timeList]
                        data['Temps (s)'] = [last_time + t for t in timeList]
                    else:
                        data['Minutes'] = [t / 60.0 for t in timeList]
                        data['Temps (s)'] = timeList
                else:
                    data['Minutes'] = [t / 60.0 for t in timeList]
                    data['Temps (s)'] = timeList
            else:
                # Nouvelle feuille ou AutoSave
                data['Minutes'] = [t / 60.0 for t in timeList]
                data['Temps (s)'] = timeList
        except Exception as e:
            print(f"Error checking for existing data: {e}")
            data['Minutes'] = [t / 60.0 for t in timeList]
            data['Temps (s)'] = timeList
        
        data['Conductance (µS)'] = conductanceList
        data['Resistance (Ohms)'] = resistanceList
        
        # Pour les données accumulées (continuité entre les tests)
        if sheet_name != "AutoSave":
            # Calculer le dernier point temporel pour la continuité des données cumulées
            lastTime = 0
            if len(self.accumulated_conductance_data['Temps (s)']) > 0:
                lastTime = self.accumulated_conductance_data['Temps (s)'][-1]
            
            # Ajouter les nouvelles données aux données accumulées
            self.accumulated_conductance_data['Minutes'].extend([(lastTime + t) / 60.0 for t in timeList])
            self.accumulated_conductance_data['Temps (s)'].extend([lastTime + t for t in timeList])
            self.accumulated_conductance_data['Conductance (µS)'].extend(conductanceList)
            self.accumulated_conductance_data['Resistance (Ohms)'].extend(resistanceList)
        
        # Sauvegarder ou mettre à jour la feuille
        result = False
        try:
            # Vérifier si la feuille existe déjà pour l'ajouter ou la mettre à jour
            wb = load_workbook(self.conductance_file)
            if sheet_name in wb.sheetnames:
                # La feuille existe, mettre à jour les données
                ws = wb[sheet_name]
                
                # Déterminer la dernière ligne utilisée
                last_row = ws.max_row
                
                # Ajouter les nouvelles données à partir de la dernière ligne
                for i, (minute, second, conductance, resistance) in enumerate(zip(
                    data['Minutes'], data['Temps (s)'], 
                    data['Conductance (µS)'], data['Resistance (Ohms)'])):
                    
                    row = last_row + i + 1  # +1 car nous voulons ajouter après la dernière ligne
                    
                    ws.cell(row=row, column=1, value=minute)
                    ws.cell(row=row, column=2, value=second)
                    ws.cell(row=row, column=3, value=conductance)
                    ws.cell(row=row, column=4, value=resistance)
                
                wb.save(self.conductance_file)
                result = True
            else:
                # La feuille n'existe pas, utiliser la méthode existante pour la créer
                result = self.add_sheet_to_excel(self.conductance_file, sheet_name, data)
                
                # Incrémenter le compteur à chaque nouvelle feuille (sauf AutoSave)
                if sheet_name != "AutoSave":
                    self.conductance_series_count += 1
        except Exception as e:
            print(f"Error saving conductance data: {e}")
            result = self.add_sheet_to_excel(self.conductance_file, sheet_name, data)
        
        return result
    
    def save_co2_temp_humidity_data(self, co2_timestamps, co2_values, temp_timestamps, temp_values, humidity_timestamps, humidity_values, delta_c=None, carbon_mass=None, sheet_name=None):
        """
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
        """
        if not self.co2_temp_humidity_file:
            self.initialize_file("co2_temp_humidity")
        
        if not (co2_timestamps or temp_timestamps or humidity_timestamps):
            return False
        
        # Use the first non-empty timestamp list
        timestamps = co2_timestamps if co2_timestamps else (temp_timestamps if temp_timestamps else humidity_timestamps)
        
        # Déterminer si on doit créer une nouvelle feuille ou utiliser l'existante
        if sheet_name == "AutoSave":
            # Pour les autosaves, toujours utiliser la feuille AutoSave
            pass
        elif not self.new_co2_temp_humidity_sheet_needed and self.active_co2_temp_humidity_sheet:
            # Utiliser la feuille active si pas besoin de nouvelle feuille
            sheet_name = self.active_co2_temp_humidity_sheet
        else:
            # Si aucun nom de feuille n'est fourni ou si une nouvelle est nécessaire, créer un nom
            if sheet_name is None:
                sheet_name = f"CO2_{datetime.now().strftime('%H%M%S')}"
                
            # Vérifier si cette feuille existe déjà
            try:
                wb = load_workbook(self.co2_temp_humidity_file)
                if sheet_name in wb.sheetnames and sheet_name != "AutoSave":
                    # Génère un nom alternatif en ajoutant un suffixe (sauf pour AutoSave)
                    sheet_name = f"{sheet_name}_{self.co2_temp_humidity_series_count}"
            except Exception as e:
                print(f"Warning: Couldn't check for duplicate sheet names: {e}")
                
            # Mémoriser comme feuille active
            self.active_co2_temp_humidity_sheet = sheet_name
            self.new_co2_temp_humidity_sheet_needed = False
        
        # Définir les données à sauvegarder
        data = {}
        
        # Pour les données de la feuille courante, vérifier s'il faut ajouter le décalage temporel
        try:
            if sheet_name != "AutoSave" and sheet_name in load_workbook(self.co2_temp_humidity_file).sheetnames:
                # La feuille existe déjà, il faut maintenir la continuité temporelle
                wb = load_workbook(self.co2_temp_humidity_file)
                ws = wb[sheet_name]
                
                # Déterminer le dernier temps enregistré
                last_row = ws.max_row
                if last_row > 1:  # Si la feuille contient déjà des données
                    last_time = ws.cell(row=last_row, column=2).value  # Colonne 2 = Temps (s)
                    if last_time is not None:
                        # Ajuster les timestamps pour continuer après le dernier point
                        data['Minutes'] = [(last_time + t) / 60.0 for t in timestamps]
                        data['Temps (s)'] = [last_time + t for t in timestamps]
                    else:
                        data['Minutes'] = [t / 60.0 for t in timestamps]
                        data['Temps (s)'] = timestamps
                else:
                    data['Minutes'] = [t / 60.0 for t in timestamps]
                    data['Temps (s)'] = timestamps
            else:
                # Nouvelle feuille ou AutoSave
                data['Minutes'] = [t / 60.0 for t in timestamps]
                data['Temps (s)'] = timestamps
        except Exception as e:
            print(f"Error checking for existing data: {e}")
            data['Minutes'] = [t / 60.0 for t in timestamps]
            data['Temps (s)'] = timestamps
        
        data['CO2 (ppm)'] = co2_values
        data['Température (°C)'] = temp_values
        data['Humidité (%)'] = humidity_values
        
        # Pour les données accumulées (continuité entre les tests)
        if sheet_name != "AutoSave":
            # Calculer le dernier point temporel pour la continuité des données cumulées
            lastTime = 0
            if len(self.accumulated_co2_temp_humidity_data['Temps (s)']) > 0:
                lastTime = self.accumulated_co2_temp_humidity_data['Temps (s)'][-1]
            
            # Ajouter les nouvelles données aux données accumulées
            self.accumulated_co2_temp_humidity_data['Minutes'].extend([(lastTime + t) / 60.0 for t in timestamps])
            self.accumulated_co2_temp_humidity_data['Temps (s)'].extend([lastTime + t for t in timestamps])
            self.accumulated_co2_temp_humidity_data['CO2 (ppm)'].extend(co2_values)
            self.accumulated_co2_temp_humidity_data['Température (°C)'].extend(temp_values)
            self.accumulated_co2_temp_humidity_data['Humidité (%)'].extend(humidity_values)
        
        # Sauvegarder ou mettre à jour la feuille
        result = False
        try:
            # Vérifier si la feuille existe déjà pour l'ajouter ou la mettre à jour
            wb = load_workbook(self.co2_temp_humidity_file)
            if sheet_name in wb.sheetnames:
                # La feuille existe, mettre à jour les données
                ws = wb[sheet_name]
                
                # Déterminer la dernière ligne utilisée
                last_row = ws.max_row
                
                # Ajouter les nouvelles données à partir de la dernière ligne
                for i, (minute, second, co2, temp, humidity) in enumerate(zip(
                    data['Minutes'], data['Temps (s)'], 
                    data['CO2 (ppm)'], data['Température (°C)'], data['Humidité (%)'])):
                    
                    row = last_row + i + 1  # +1 car nous voulons ajouter après la dernière ligne
                    
                    ws.cell(row=row, column=1, value=minute)
                    ws.cell(row=row, column=2, value=second)
                    ws.cell(row=row, column=3, value=co2)
                    ws.cell(row=row, column=4, value=temp)
                    ws.cell(row=row, column=5, value=humidity)
                
                # Mettre à jour deltaC et masseC si fournis
                if delta_c is not None:
                    # Trouver la colonne de deltaC ou la créer
                    col_delta = None
                    for col in range(1, ws.max_column + 1):
                        if ws.cell(row=1, column=col).value == "deltaC (ppm)":
                            col_delta = col
                            break
                    
                    if col_delta is None:
                        col_delta = ws.max_column + 1
                        ws.cell(row=1, column=col_delta, value="deltaC (ppm)")
                    
                    ws.cell(row=2, column=col_delta, value=delta_c)
                
                if carbon_mass is not None:
                    # Trouver la colonne de masseC ou la créer
                    col_mass = None
                    for col in range(1, ws.max_column + 1):
                        if ws.cell(row=1, column=col).value == "masseC (µg)":
                            col_mass = col
                            break
                    
                    if col_mass is None:
                        col_mass = ws.max_column + 1
                        ws.cell(row=1, column=col_mass, value="masseC (µg)")
                    
                    ws.cell(row=2, column=col_mass, value=carbon_mass)
                
                wb.save(self.co2_temp_humidity_file)
                result = True
            else:
                # La feuille n'existe pas, utiliser la méthode existante pour la créer
                result = self.add_sheet_to_excel(self.co2_temp_humidity_file, sheet_name, data)
                
                # Ajouter deltaC et masseC après création si fournis
                if result and (delta_c is not None or carbon_mass is not None):
                    try:
                        wb = load_workbook(self.co2_temp_humidity_file)
                        if sheet_name in wb.sheetnames:
                            ws = wb[sheet_name]
                            last_col = ws.max_column
                            
                            if delta_c is not None:
                                ws.cell(row=1, column=last_col+1, value="deltaC (ppm)")
                                ws.cell(row=2, column=last_col+1, value=delta_c)
                            
                            if carbon_mass is not None:
                                ws.cell(row=1, column=last_col+2, value="masseC (µg)")
                                ws.cell(row=2, column=last_col+2, value=carbon_mass)
                            
                            wb.save(self.co2_temp_humidity_file)
                    except Exception as e:
                        print(f"Error adding deltaC and masseC cells: {e}")
                
                # Incrémenter le compteur à chaque nouvelle feuille (sauf AutoSave)
                if sheet_name != "AutoSave":
                    self.co2_temp_humidity_series_count += 1
        except Exception as e:
            print(f"Error saving CO2/temp/humidity data: {e}")
            result = self.add_sheet_to_excel(self.co2_temp_humidity_file, sheet_name, data)
        
        return result

    
    def save_temp_res_data(self, timestamps, temperatures, tcons_values, sheet_name=None):
        """
        Sauvegarde les données temp/resistance
        
        Args:
            timestamps: Liste des timestamps
            temperatures: Liste des valeurs de température
            tcons_values: Liste des valeurs de consigne de température
            sheet_name: Nom de la feuille à utiliser (ou None pour créer un nom basé sur l'horodatage)
        """
        if not self.temp_res_file:
            self.initialize_file("temp_res")
        
        if not timestamps or not (temperatures or tcons_values):
            return False
        
        # Déterminer si on doit créer une nouvelle feuille ou utiliser l'existante
        if sheet_name == "AutoSave":
            # Pour les autosaves, toujours utiliser la feuille AutoSave
            pass
        elif not self.new_temp_res_sheet_needed and self.active_temp_res_sheet:
            # Utiliser la feuille active si pas besoin de nouvelle feuille
            sheet_name = self.active_temp_res_sheet
        else:
            # Si aucun nom de feuille n'est fourni ou si une nouvelle est nécessaire, créer un nom
            if sheet_name is None:
                sheet_name = f"Temp_{datetime.now().strftime('%H%M%S')}"
                
            # Vérifier si cette feuille existe déjà
            try:
                wb = load_workbook(self.temp_res_file)
                if sheet_name in wb.sheetnames and sheet_name != "AutoSave":
                    # Génère un nom alternatif en ajoutant un suffixe (sauf pour AutoSave)
                    sheet_name = f"{sheet_name}_{self.temp_res_series_count}"
            except Exception as e:
                print(f"Warning: Couldn't check for duplicate sheet names: {e}")
                
            # Mémoriser comme feuille active
            self.active_temp_res_sheet = sheet_name
            self.new_temp_res_sheet_needed = False
        
        # Définir les données à sauvegarder
        data = {}
        
        # Pour les données de la feuille courante, vérifier s'il faut ajouter le décalage temporel
        try:
            if sheet_name != "AutoSave" and sheet_name in load_workbook(self.temp_res_file).sheetnames:
                # La feuille existe déjà, il faut maintenir la continuité temporelle
                wb = load_workbook(self.temp_res_file)
                ws = wb[sheet_name]
                
                # Déterminer le dernier temps enregistré
                last_row = ws.max_row
                if last_row > 1:  # Si la feuille contient déjà des données
                    last_time = ws.cell(row=last_row, column=2).value  # Colonne 2 = Temps (s)
                    if last_time is not None:
                        # Ajuster les timestamps pour continuer après le dernier point
                        data['Minutes'] = [(last_time + t) / 60.0 for t in timestamps]
                        data['Temps (s)'] = [last_time + t for t in timestamps]
                    else:
                        data['Minutes'] = [t / 60.0 for t in timestamps]
                        data['Temps (s)'] = timestamps
                else:
                    data['Minutes'] = [t / 60.0 for t in timestamps]
                    data['Temps (s)'] = timestamps
            else:
                # Nouvelle feuille ou AutoSave
                data['Minutes'] = [t / 60.0 for t in timestamps]
                data['Temps (s)'] = timestamps
        except Exception as e:
            print(f"Error checking for existing data: {e}")
            data['Minutes'] = [t / 60.0 for t in timestamps]
            data['Temps (s)'] = timestamps
        
        data['Température mesurée'] = temperatures
        data['Tcons'] = tcons_values
        
        # Pour les données accumulées (continuité entre les tests)
        if sheet_name != "AutoSave":
            # Calculer le dernier point temporel pour la continuité des données cumulées
            lastTime = 0
            if len(self.accumulated_temp_res_data['Temps (s)']) > 0:
                lastTime = self.accumulated_temp_res_data['Temps (s)'][-1]
            
            # Ajouter les nouvelles données aux données accumulées
            self.accumulated_temp_res_data['Minutes'].extend([(lastTime + t) / 60.0 for t in timestamps])
            self.accumulated_temp_res_data['Temps (s)'].extend([lastTime + t for t in timestamps])
            self.accumulated_temp_res_data['Température mesurée'].extend(temperatures)
            self.accumulated_temp_res_data['Tcons'].extend(tcons_values)
        
        # Sauvegarder ou mettre à jour la feuille
        result = False
        try:
            # Vérifier si la feuille existe déjà pour l'ajouter ou la mettre à jour
            wb = load_workbook(self.temp_res_file)
            if sheet_name in wb.sheetnames:
                # La feuille existe, mettre à jour les données
                ws = wb[sheet_name]
                
                # Déterminer la dernière ligne utilisée
                last_row = ws.max_row
                
                # Ajouter les nouvelles données à partir de la dernière ligne
                for i, (minute, second, temp, tcons) in enumerate(zip(
                    data['Minutes'], data['Temps (s)'], 
                    data['Température mesurée'], data['Tcons'])):
                    
                    row = last_row + i + 1  # +1 car nous voulons ajouter après la dernière ligne
                    
                    ws.cell(row=row, column=1, value=minute)
                    ws.cell(row=row, column=2, value=second)
                    ws.cell(row=row, column=3, value=temp)
                    ws.cell(row=row, column=4, value=tcons)
                
                wb.save(self.temp_res_file)
                result = True
            else:
                # La feuille n'existe pas, utiliser la méthode existante pour la créer
                result = self.add_sheet_to_excel(self.temp_res_file, sheet_name, data)
                
                # Incrémenter le compteur à chaque nouvelle feuille (sauf AutoSave)
                if sheet_name != "AutoSave":
                    self.temp_res_series_count += 1
        except Exception as e:
            print(f"Error saving temp/res data: {e}")
            result = self.add_sheet_to_excel(self.temp_res_file, sheet_name, data)
        
        return result
    
    def save_all_data(self, measurement_manager):
        """
        Save all data to Excel files
        
        Args:
            measurement_manager: MeasurementManager instance with data
            
        Returns:
            bool: True if all data was saved successfully, False otherwise
        """
        success = False  # Commence à False, met à True uniquement si des données ont été sauvegardées
        any_data_saved = False
        
        # Save conductance data
        if measurement_manager.timeList and len(measurement_manager.timeList) > 0:
            result = self.save_conductance_data(
                measurement_manager.timeList,
                measurement_manager.conductanceList,
                measurement_manager.resistanceList
            )
            success = result
            any_data_saved = any_data_saved or result
        
        # Save CO2, temperature and humidity data
        has_co2_data = (measurement_manager.timestamps_co2 and len(measurement_manager.timestamps_co2) > 0)
        has_temp_data = (measurement_manager.timestamps_temp and len(measurement_manager.timestamps_temp) > 0)
        has_humidity_data = (measurement_manager.timestamps_humidity and len(measurement_manager.timestamps_humidity) > 0)
        
        if has_co2_data or has_temp_data or has_humidity_data:
            # Get regeneration results (delta_c and carbon_mass) if available
            delta_c = None
            carbon_mass = None
            if hasattr(measurement_manager, 'regeneration_results') and measurement_manager.regeneration_results:
                delta_c = measurement_manager.regeneration_results.get('delta_c')
                carbon_mass = measurement_manager.regeneration_results.get('carbon_mass')
            
            result = self.save_co2_temp_humidity_data(
                measurement_manager.timestamps_co2,
                measurement_manager.values_co2,
                measurement_manager.timestamps_temp,
                measurement_manager.values_temp,
                measurement_manager.timestamps_humidity,
                measurement_manager.values_humidity,
                delta_c,
                carbon_mass
            )
            success = success and result
            any_data_saved = any_data_saved or result
        
        # Save temperature and resistance data
        if measurement_manager.timestamps_res_temp and len(measurement_manager.timestamps_res_temp) > 0:
            result = self.save_temp_res_data(
                measurement_manager.timestamps_res_temp,
                measurement_manager.temperatures,
                measurement_manager.Tcons_values
            )
            success = success and result
            any_data_saved = any_data_saved or result
        
        if any_data_saved:
            print(f"All data saved successfully to {self.test_folder_path}")
        else:
            print("Aucune donnée à sauvegarder")
            success = False
        
        return success
        
    def rename_test_folder(self, new_name):
        """
        Rename the test folder with a custom name
        
        Args:
            new_name: New name for the test folder
            
        Returns:
            bool: True if the folder was renamed successfully, False otherwise
        """
        if not self.test_folder_path or not os.path.exists(self.test_folder_path):
            return False
            
        try:
            # Get parent directory
            parent_dir = os.path.dirname(self.test_folder_path)
            
            # Create new path with the new name
            new_path = os.path.join(parent_dir, new_name)
            
            # Rename the folder
            os.rename(self.test_folder_path, new_path)
            
            # Update the path
            self.test_folder_path = new_path
            
            # Update file paths
            if self.conductance_file:
                filename = os.path.basename(self.conductance_file)
                self.conductance_file = os.path.join(new_path, filename)
                
            if self.co2_temp_humidity_file:
                filename = os.path.basename(self.co2_temp_humidity_file)
                self.co2_temp_humidity_file = os.path.join(new_path, filename)
                
            if self.temp_res_file:
                filename = os.path.basename(self.temp_res_file)
                self.temp_res_file = os.path.join(new_path, filename)
                
            return True
        except Exception as e:
            print(f"Error renaming test folder: {e}")
            return False
        
    def add_charts_to_excel(self, file_path):
        """
        Ajoute des graphiques aux feuilles Excel en fonction du type de données
        
        Args:
            file_path: Chemin du fichier Excel
            
        Returns:
            bool: True si les graphiques ont été ajoutés avec succès, False sinon
        """
        if not os.path.exists(file_path):
            return False
            
        try:
            wb = load_workbook(file_path)
            
            # Déterminer le type de données basé sur le nom du fichier
            if "conductance" in os.path.basename(file_path).lower():
                self._add_conductance_charts(wb)
            elif "co2_temp_humidity" in os.path.basename(file_path).lower():
                self._add_co2_temp_humidity_charts(wb)
            elif "temperature_resistance" in os.path.basename(file_path).lower():
                self._add_temp_res_charts(wb)
                
            wb.save(file_path)
            return True
        except Exception as e:
            print(f"Erreur lors de l'ajout des graphiques Excel: {e}")
            return False

    def _add_conductance_charts(self, workbook):
        """
        Ajoute les graphiques pour les données de conductance
        
        Args:
            workbook: Classeur Excel ouvert
        """
        for sheet_name in workbook.sheetnames:
            if sheet_name.startswith("Cond_") or sheet_name == "Essais cumulés":
                ws = workbook[sheet_name]
                
                # Créer un graphique
                chart = LineChart()
                chart.title = f"Conductance - {sheet_name}"
                chart.style = 1
                chart.y_axis.title = 'Conductance (µS)'
                chart.x_axis.title = 'Temps (s)'

                # Pour l'axe X :
                chart.x_axis.majorTickMark = "out"  # Affiche les marques de graduation
                chart.x_axis.minorTickMark = "none"  # Pas de graduations secondaires
                chart.x_axis.tickLblPos = "nextTo"  # Position des étiquettes

                # Pour l'axe Y :
                chart.y_axis.majorTickMark = "out"
                chart.y_axis.minorTickMark = "none"
                chart.y_axis.tickLblPos = "nextTo"

                # Optionnel: forcer une échelle spécifique si nécessaire
                # chart.y_axis.scaling.min = 0
                # chart.y_axis.scaling.max = 100
                
                # Références aux données
                data = Reference(ws, min_col=3, min_row=1, max_col=3, max_row=ws.max_row)
                categories = Reference(ws, min_col=2, min_row=2, max_row=ws.max_row)
                
                # Ajouter les données au graphique
                chart.add_data(data, titles_from_data=True)
                chart.set_categories(categories)
                
                # Ajouter le graphique à la feuille en position H5
                ws.add_chart(chart, "H5")
                
                # Configurer la série pour n'avoir que des lignes sans marqueurs et aucun symbole
                for series in chart.series:
                    series.marker = None  # Supprime les marqueurs
                    series.smooth = False  # Ligne droite entre les points
                    # Optionnel: définir l'épaisseur de la ligne
                    series.graphicalProperties.line.width = 20000  # Environ 1 pt

    def _add_co2_temp_humidity_charts(self, workbook):
        """
        Ajoute les graphiques pour les données CO2/température/humidité
        
        Args:
            workbook: Classeur Excel ouvert
        """
        for sheet_name in workbook.sheetnames:
            if sheet_name.startswith("CO2_") or sheet_name == "Essais cumulés":
                ws = workbook[sheet_name]
                
                # Graphique principal pour CO2
                chart1 = LineChart()
                chart1.title = f"CO2 - {sheet_name}"
                chart1.style = 1
                chart1.y_axis.title = 'CO2 (ppm)'
                chart1.x_axis.title = 'Temps (s)'
                # Pour l'axe X :
                chart1.x_axis.majorTickMark = "out"  # Affiche les marques de graduation
                chart1.x_axis.minorTickMark = "none"  # Pas de graduations secondaires
                chart1.x_axis.tickLblPos = "nextTo"  # Position des étiquettes

                # Pour l'axe Y :
                chart1.y_axis.majorTickMark = "out"
                chart1.y_axis.minorTickMark = "none"
                chart1.y_axis.tickLblPos = "nextTo"

                # Optionnel: forcer une échelle spécifique si nécessaire
                # chart1.y_axis.scaling.min = 0
                # chart1.y_axis.scaling.max = 100
                
                # Données CO2
                co2_data = Reference(ws, min_col=3, min_row=1, max_col=3, max_row=ws.max_row)
                categories = Reference(ws, min_col=2, min_row=2, max_row=ws.max_row)
                
                chart1.add_data(co2_data, titles_from_data=True)
                chart1.set_categories(categories)
                
                # Graphique secondaire pour température et humidité
                chart2 = LineChart()
                chart2.style = 1
                
                # Données température et humidité
                temp_data = Reference(ws, min_col=4, min_row=1, max_col=4, max_row=ws.max_row)
                hum_data = Reference(ws, min_col=5, min_row=1, max_col=5, max_row=ws.max_row)
                
                chart2.add_data(temp_data, titles_from_data=True)
                chart2.add_data(hum_data, titles_from_data=True)
                
                # Combiner les graphiques
                chart1.y_axis.majorGridlines = None
                chart2.y_axis.axId = 20
                chart1 += chart2
                
                # Configurer l'axe secondaire
                chart1.y_axis.crosses = "max"
                chart2.y_axis.title = "Température (°C) et Humidité (%)"
                
                # Ajouter le graphique combiné en position H5
                ws.add_chart(chart1, "H5")
                
                # Configurer les séries pour n'avoir que des lignes sans marqueurs et lignes droites
                for series in chart1.series:
                    series.marker = None  # Supprime les marqueurs
                    series.smooth = False  # Ligne droite entre les points
                    # Optionnel: définir l'épaisseur de la ligne
                    series.graphicalProperties.line.width = 20000  # Environ 1 pt

    def _add_temp_res_charts(self, workbook):
        """
        Ajoute les graphiques pour les données température/résistance
        
        Args:
            workbook: Classeur Excel ouvert
        """
        for sheet_name in workbook.sheetnames:
            if sheet_name.startswith("Temp_") or sheet_name == "Essais cumulés":
                ws = workbook[sheet_name]
                
                # Créer un graphique
                chart = LineChart()
                chart.title = f"Température - {sheet_name}"
                chart.style = 1
                # Pour l'axe X :
                chart.x_axis.majorTickMark = "out"  # Affiche les marques de graduation
                chart.x_axis.minorTickMark = "in"  # Pas de graduations secondaires
                chart.x_axis.tickLblPos = "nextTo"  # Position des étiquettes

                # Pour l'axe Y :
                chart.y_axis.majorTickMark = "out"
                chart.y_axis.minorTickMark = "in"
                chart.y_axis.tickLblPos = "nextTo"
                chart.y_axis.title = 'Température (°C)'
                chart.x_axis.title = 'Temps (s)'

                
                # Références aux données
                temp_data = Reference(ws, min_col=3, min_row=1, max_col=3, max_row=ws.max_row)
                tcons_data = Reference(ws, min_col=4, min_row=1, max_col=4, max_row=ws.max_row)
                categories = Reference(ws, min_col=2, min_row=2, max_row=ws.max_row)
                
                # Ajouter les données au graphique
                chart.add_data(temp_data, titles_from_data=True)
                chart.add_data(tcons_data, titles_from_data=True)
                chart.set_categories(categories)
                
                # Configurer les séries - Couleurs différentes mais sans marqueurs
                s1 = chart.series[0]
                s1.marker = None
                s1.smooth = False  # Ligne droite entre les points
                s1.graphicalProperties.line.solidFill = "FF0000"  # Rouge pour température mesurée
                s1.graphicalProperties.line.width = 20000  # Environ 1 pt
                
                s2 = chart.series[1]
                s2.marker = None
                s2.smooth = False  # Ligne droite entre les points
                s2.graphicalProperties.line.solidFill = "0000FF"  # Bleu pour Tcons
                s2.graphicalProperties.line.width = 20000  # Environ 1 pt
                
                # Ajouter le graphique à la feuille en position H5
                ws.add_chart(chart, "H5")

    def _should_create_cumulative_sheet(self, file_path):
        """Détermine si une feuille 'Essais cumulés' doit être créée"""
        if "conductance" in os.path.basename(file_path).lower():
            return self.conductance_series_count >= 2
        elif "co2_temp_humidity" in os.path.basename(file_path).lower():
            return self.co2_temp_humidity_series_count >= 2
        elif "temperature_resistance" in os.path.basename(file_path).lower():
            return self.temp_res_series_count >= 2
        return False