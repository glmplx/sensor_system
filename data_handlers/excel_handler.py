"""
Gestionnaire de fichiers Excel pour le stockage des données
"""

import os
import sys
import pandas as pd
from datetime import datetime
from openpyxl import Workbook, load_workbook
from core.constants import EXCEL_BASE_DIR

class ExcelHandler:
    """Gère les opérations de fichiers Excel pour le stockage des données"""
    
    def __init__(self, mode="manual"):
        """
        Initialiser le gestionnaire Excel
        
        Args:
            mode: Mode de fonctionnement, soit "manual" soit "auto"
        """
        self.mode = mode
        self.test_folder_path = None
        self.conductance_file = None
        self.co2_temp_humidity_file = None
        self.temp_res_file = None
        
        # Stores accumulated data between RAZ sessions
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
            'Humidité (%)': []
        }
        
        self.accumulated_temp_res_data = {
            'Minutes': [],
            'Temps (s)': [],
            'Température mesurée': [],
            'Tcons': []
        }
    
    def initialize_folder(self):
        """
        Initialize the test folder based on the current date and time
        
        Returns:
            str: Path to the test folder
        """
        # Get the directory where the application is running from
        if getattr(sys, 'frozen', False):
            # Running as executable
            application_path = os.path.dirname(sys.executable)
        else:
            # Running as script
            application_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
        excel_folder_path = os.path.join(application_path, EXCEL_BASE_DIR)
        
        if not os.path.exists(excel_folder_path):
            os.makedirs(excel_folder_path)
        
        mode_prefix = "Manual" if self.mode == "manual" else "Auto"
        test_folder_name = f"Test-{mode_prefix}-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
        self.test_folder_path = os.path.join(excel_folder_path, test_folder_name)
        
        os.makedirs(self.test_folder_path)
        return self.test_folder_path
    
    def initialize_file(self, file_type):
        """
        Initialize an Excel file for a specific data type
        
        Args:
            file_type: Type of data file to initialize
            
        Returns:
            str: Path to the initialized file
        """
        if not self.test_folder_path:
            self.initialize_folder()
        
        # Get current date for filename
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Create the appropriate file based on the type
        if file_type == "conductance":
            self.conductance_file = os.path.join(self.test_folder_path, f'conductance_{current_date}.xlsx')
            # Create a workbook with the default sheet
            wb = Workbook()
            # Rename the default sheet to a temporary name
            ws = wb.active
            ws.title = "_temp"
            wb.save(self.conductance_file)
            return self.conductance_file
        
        elif file_type == "co2_temp_humidity":
            self.co2_temp_humidity_file = os.path.join(self.test_folder_path, f'co2_temp_humidity_{current_date}.xlsx')
            # Create a workbook with the default sheet
            wb = Workbook()
            # Rename the default sheet to a temporary name
            ws = wb.active
            ws.title = "_temp"
            wb.save(self.co2_temp_humidity_file)
            return self.co2_temp_humidity_file
        
        elif file_type == "temp_res":
            self.temp_res_file = os.path.join(self.test_folder_path, f'temperature_resistance_{current_date}.xlsx')
            # Create a workbook with the default sheet
            wb = Workbook()
            # Rename the default sheet to a temporary name
            ws = wb.active
            ws.title = "_temp"
            wb.save(self.temp_res_file)
            return self.temp_res_file
        
        return None
    
    def add_sheet_to_excel(self, file_path, sheet_name, data):
        """
        Add a new sheet to an Excel file
        
        Args:
            file_path: Path to the Excel file
            sheet_name: Name of the sheet to add
            data: Dictionary of column names and values
            
        Returns:
            bool: True if the sheet was added successfully, False otherwise
        """
        try:
            # Check if we need to replace an existing "Essais cumulés" sheet
            wb = load_workbook(file_path)
            if sheet_name == "Essais cumulés" and sheet_name in wb.sheetnames:
                # Remove the existing sheet first
                cumul_sheet = wb[sheet_name]
                wb.remove(cumul_sheet)
                wb.save(file_path)
            
            # Write our data to the Excel file
            with pd.ExcelWriter(file_path, engine='openpyxl', mode='a') as writer:
                df = pd.DataFrame(data)
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Now remove the temporary sheet if it exists
            wb = load_workbook(file_path)
            if "_temp" in wb.sheetnames:
                temp_sheet = wb["_temp"]
                wb.remove(temp_sheet)
                wb.save(file_path)
                
            return True
        except Exception as e:
            print(f"Error adding sheet to Excel file: {e}")
            return False
    
    def save_conductance_data(self, timeList, conductanceList, resistanceList):
        """
        Save conductance data to Excel
        
        Args:
            timeList: List of timestamps
            conductanceList: List of conductance values
            resistanceList: List of resistance values
            
        Returns:
            bool: True if the data was saved successfully, False otherwise
        """
        if not self.conductance_file:
            self.initialize_file("conductance")
        
        if not timeList:
            return False
        
        # Calculate last time point for cumulative data continuation
        lastTime = 0
        if self.accumulated_conductance_data['Temps (s)']:
            lastTime = self.accumulated_conductance_data['Temps (s)'][-1]
        
        # Add new data to accumulated data with adjusted timestamps
        self.accumulated_conductance_data['Minutes'].extend([(lastTime + t) / 60.0 for t in timeList])
        self.accumulated_conductance_data['Temps (s)'].extend([lastTime + t for t in timeList])
        self.accumulated_conductance_data['Conductance (µS)'].extend(conductanceList)
        self.accumulated_conductance_data['Resistance (Ohms)'].extend(resistanceList)
        
        # Create current test data sheet
        sheet_name = f"Conductance_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
        data = {
            'Minutes': [t / 60.0 for t in timeList],
            'Temps (s)': timeList,
            'Conductance (µS)': conductanceList,
            'Resistance (Ohms)': resistanceList
        }
        
        # Save current test data
        result = self.add_sheet_to_excel(self.conductance_file, sheet_name, data)
        
        # Save accumulated data only if we have multiple data entries
        if len(set(self.accumulated_conductance_data['Temps (s)'])) > len(timeList):
            self.add_sheet_to_excel(self.conductance_file, "Essais cumulés", self.accumulated_conductance_data)
        
        return result
    
    def save_co2_temp_humidity_data(self, co2_timestamps, co2_values, temp_timestamps, temp_values, humidity_timestamps, humidity_values):
        """
        Save CO2, temperature and humidity data to Excel
        
        Args:
            co2_timestamps: List of timestamps for CO2 measurements
            co2_values: List of CO2 values
            temp_timestamps: List of timestamps for temperature measurements
            temp_values: List of temperature values
            humidity_timestamps: List of timestamps for humidity measurements
            humidity_values: List of humidity values
            
        Returns:
            bool: True if the data was saved successfully, False otherwise
        """
        if not self.co2_temp_humidity_file:
            self.initialize_file("co2_temp_humidity")
        
        if not (co2_timestamps or temp_timestamps or humidity_timestamps):
            return False
        
        # Use the first non-empty timestamp list
        timestamps = co2_timestamps if co2_timestamps else (temp_timestamps if temp_timestamps else humidity_timestamps)
        
        # Calculate last time point for cumulative data continuation
        lastTime = 0
        if self.accumulated_co2_temp_humidity_data['Temps (s)']:
            lastTime = self.accumulated_co2_temp_humidity_data['Temps (s)'][-1]
        
        # Add new data to accumulated data with adjusted timestamps
        self.accumulated_co2_temp_humidity_data['Minutes'].extend([(lastTime + t) / 60.0 for t in timestamps])
        self.accumulated_co2_temp_humidity_data['Temps (s)'].extend([lastTime + t for t in timestamps])
        self.accumulated_co2_temp_humidity_data['CO2 (ppm)'].extend(co2_values)
        self.accumulated_co2_temp_humidity_data['Température (°C)'].extend(temp_values)
        self.accumulated_co2_temp_humidity_data['Humidité (%)'].extend(humidity_values)
        
        # Create current test data sheet
        sheet_name = f"CO2_Temp_H_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
        data = {
            'Minutes': [t / 60.0 for t in timestamps],
            'Temps (s)': timestamps,
            'CO2 (ppm)': co2_values,
            'Température (°C)': temp_values,
            'Humidité (%)': humidity_values
        }
        
        # Save current test data
        result = self.add_sheet_to_excel(self.co2_temp_humidity_file, sheet_name, data)
        
        # Save accumulated data only if we have multiple data entries
        if len(set(self.accumulated_co2_temp_humidity_data['Temps (s)'])) > len(timestamps):
            self.add_sheet_to_excel(self.co2_temp_humidity_file, "Essais cumulés", self.accumulated_co2_temp_humidity_data)
        
        return result
    
    def save_temp_res_data(self, timestamps, temperatures, tcons_values):
        """
        Save temperature and resistance data to Excel
        
        Args:
            timestamps: List of timestamps
            temperatures: List of temperature values
            tcons_values: List of Tcons values
            
        Returns:
            bool: True if the data was saved successfully, False otherwise
        """
        if not self.temp_res_file:
            self.initialize_file("temp_res")
        
        if not timestamps or not (temperatures or tcons_values):
            return False
        
        # Calculate last time point for cumulative data continuation
        lastTime = 0
        if self.accumulated_temp_res_data['Temps (s)']:
            lastTime = self.accumulated_temp_res_data['Temps (s)'][-1]
        
        # Add new data to accumulated data with adjusted timestamps
        self.accumulated_temp_res_data['Minutes'].extend([(lastTime + t) / 60.0 for t in timestamps])
        self.accumulated_temp_res_data['Temps (s)'].extend([lastTime + t for t in timestamps])
        self.accumulated_temp_res_data['Température mesurée'].extend(temperatures)
        self.accumulated_temp_res_data['Tcons'].extend(tcons_values)
        
        # Create current test data sheet
        sheet_name = f"Temp_Res_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
        data = {
            'Minutes': [t / 60.0 for t in timestamps],
            'Temps (s)': timestamps,
            'Température mesurée': temperatures,
            'Tcons': tcons_values
        }
        
        # Save current test data
        result = self.add_sheet_to_excel(self.temp_res_file, sheet_name, data)
        
        # Save accumulated data only if we have multiple data entries
        if len(set(self.accumulated_temp_res_data['Temps (s)'])) > len(timestamps):
            self.add_sheet_to_excel(self.temp_res_file, "Essais cumulés", self.accumulated_temp_res_data)
        
        return result
    
    def save_all_data(self, measurement_manager):
        """
        Save all data to Excel files
        
        Args:
            measurement_manager: MeasurementManager instance with data
            
        Returns:
            bool: True if all data was saved successfully, False otherwise
        """
        success = True
        
        # Save conductance data
        if measurement_manager.timeList:
            result = self.save_conductance_data(
                measurement_manager.timeList,
                measurement_manager.conductanceList,
                measurement_manager.resistanceList
            )
            success = success and result
        
        # Save CO2, temperature and humidity data
        if measurement_manager.timestamps_co2 or measurement_manager.timestamps_temp or measurement_manager.timestamps_humidity:
            result = self.save_co2_temp_humidity_data(
                measurement_manager.timestamps_co2,
                measurement_manager.values_co2,
                measurement_manager.timestamps_temp,
                measurement_manager.values_temp,
                measurement_manager.timestamps_humidity,
                measurement_manager.values_humidity
            )
            success = success and result
        
        # Save temperature and resistance data
        if measurement_manager.timestamps_res_temp:
            result = self.save_temp_res_data(
                measurement_manager.timestamps_res_temp,
                measurement_manager.temperatures,
                measurement_manager.Tcons_values
            )
            success = success and result
        
        if success:
            print(f"All data saved successfully to {self.test_folder_path}")
        else:
            print("Error saving some data")
        
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