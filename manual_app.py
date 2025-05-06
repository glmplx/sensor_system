#!/usr/bin/env python
"""
Manual mode application for the sensor system
"""

import sys
import time
import os
import signal
import threading
import serial
import pyvisa
import matplotlib.pyplot as plt
from datetime import datetime

from devices.keithley_device import KeithleyDevice
from devices.arduino_device import ArduinoDevice
from devices.regen_device import RegenDevice
from core.measurement_manager import MeasurementManager
from data_handlers.excel_handler import ExcelHandler
from ui.plot_manager import PlotManager

def main(arduino_port=None, arduino_baud_rate=None, other_port=None, other_baud_rate=None,
         measure_conductance=1, measure_co2=1, measure_regen=1):
    """
    Main entry point for the manual mode application
    
    Args:
        arduino_port: COM port for the Arduino
        arduino_baud_rate: Baud rate for the Arduino
        other_port: COM port for the regeneration device
        other_baud_rate: Baud rate for the regeneration device
        measure_conductance: Whether to enable conductance measurements (1=enabled, 0=disabled)
        measure_co2: Whether to enable CO2/temp/humidity measurements (1=enabled, 0=disabled)
        measure_regen: Whether to enable regeneration/temp measurements (1=enabled, 0=disabled)
    """
    
    # If parameters aren't provided, try to get them from command line
    if arduino_port is None:
        # Check for required arguments
        if len(sys.argv) < 5:
            print("Usage: python manual_app.py <arduino_port> <arduino_baud_rate> <other_port> <other_baud_rate> [--measure_conductance 0|1] [--measure_co2 0|1] [--measure_regen 0|1]")
            sys.exit(1)
        
        # Parse required arguments
        arduino_port = sys.argv[1]
        arduino_baud_rate = int(sys.argv[2])
        other_port = sys.argv[3]
        other_baud_rate = int(sys.argv[4])
        
        # Parse optional arguments
        for i in range(5, len(sys.argv), 2):
            if i+1 < len(sys.argv):
                if sys.argv[i] == "--measure_conductance":
                    measure_conductance = int(sys.argv[i+1])
                elif sys.argv[i] == "--measure_co2":
                    measure_co2 = int(sys.argv[i+1])
                elif sys.argv[i] == "--measure_regen":
                    measure_regen = int(sys.argv[i+1])
    
    # Initialize devices (selon les mesures sélectionnées)
    arduino = None
    regen = None
    arduino_connected = False
    regen_connected = False
    
    # Vérifier si chaque appareil est requis et disponible
    import tkinter.messagebox as messagebox
    
    # Liste pour suivre quelles mesures sont effectivement disponibles
    available_measurements = []
    
    # Connecter à l'Arduino (si nécessaire pour CO2 uniquement)
    if measure_co2:
        # Vérifier si un port Arduino valide est fourni
        if arduino_port == "NONE":
            print("CO2 measurement selected but no Arduino port provided")
            
            # Si d'autres mesures sont sélectionnées, afficher un avertissement et continuer
            if measure_conductance or measure_regen:
                messagebox.showwarning(
                    "Appareil non disponible", 
                    "Impossible de se connecter à l'Arduino pour la mesure de CO2.\n\n"
                    "Les autres mesures sélectionnées seront effectuées."
                )
                measure_co2 = 0  # Désactiver la mesure CO2
                print("Continuing with other available measurements.")
            else:
                # Si c'était la seule mesure sélectionnée, quitter
                print("No other measurements selected, exiting.")
                sys.exit(1)
        else:
            arduino = ArduinoDevice(port=arduino_port, baud_rate=arduino_baud_rate)
            if not arduino.connect():
                print("Failed to connect to Arduino device")
                
                # Si d'autres mesures sont sélectionnées, afficher un avertissement et continuer
                if measure_conductance or measure_regen:
                    messagebox.showwarning(
                        "Appareil non disponible", 
                        "Impossible de se connecter à l'Arduino pour la mesure de CO2.\n\n"
                        "Les autres mesures sélectionnées seront effectuées."
                    )
                    measure_co2 = 0  # Désactiver la mesure CO2
                    print("Continuing with other available measurements.")
                else:
                    # Si c'était la seule mesure sélectionnée, quitter
                    print("No other measurements selected, exiting.")
                    sys.exit(1)
            else:
                arduino_connected = True
                available_measurements.append("CO2")
    
    if not arduino_connected:
        # Initialiser un objet Arduino simulé pour éviter les erreurs
        print("Arduino not needed or not available - using dummy device")
        arduino = type('DummyArduino', (), {
            'read_line': lambda *args: None,
            'send_command': lambda *args: None,
            'close': lambda *args: None,  # Accepte un self implicite
            'device': None
        })()
    
    # Connecter à la carte de régénération (seulement si nécessaire)
    if measure_regen:
        # Vérifier si un port de régénération valide est fourni
        if other_port == "NONE":
            print("Regeneration measurement selected but no port provided")
            
            # Si d'autres mesures sont sélectionnées, afficher un avertissement et continuer
            if measure_conductance or measure_co2:
                messagebox.showwarning(
                    "Appareil non disponible", 
                    "Impossible de se connecter à la carte de régénération.\n\n"
                    "Les autres mesures sélectionnées seront effectuées."
                )
                measure_regen = 0  # Désactiver la mesure de régénération
                print("Continuing with other available measurements.")
            else:
                # Si c'était la seule mesure sélectionnée, quitter
                print("No other measurements selected, exiting.")
                if arduino_connected:
                    arduino.close()
                sys.exit(1)
        else:
            regen = RegenDevice(port=other_port, baud_rate=other_baud_rate)
            if not regen.connect():
                print("Failed to connect to regeneration device")
                
                # Si d'autres mesures sont sélectionnées, afficher un avertissement et continuer
                if measure_conductance or measure_co2:
                    messagebox.showwarning(
                        "Appareil non disponible", 
                        "Impossible de se connecter à la carte de régénération.\n\n"
                        "Les autres mesures sélectionnées seront effectuées."
                    )
                    measure_regen = 0  # Désactiver la mesure de régénération
                    print("Continuing with other available measurements.")
                else:
                    # Si c'était la seule mesure sélectionnée, quitter
                    print("No other measurements selected, exiting.")
                    if arduino_connected:
                        arduino.close()
                    sys.exit(1)
            else:
                regen_connected = True
                available_measurements.append("Régénération")
    
    if not regen_connected:
        # Initialiser un objet Regen simulé pour éviter les erreurs
        print("Regeneration device not needed or not available - using dummy device")
        regen = type('DummyRegen', (), {
            'read_variable': lambda *args: "0",
            'write_parameter': lambda *args: None,
            'close': lambda *args: None,  # Accepte un self implicite
            'device': None
        })()
        
    # Connecter au Keithley (seulement si nécessaire pour conductance)
    keithley = None
    keithley_connected = False
    if measure_conductance:
        keithley = KeithleyDevice()
        if not keithley.connect():
            print("Failed to connect to Keithley device")
            
            # Vérifier si d'autres mesures sont sélectionnées
            if not measure_co2 and not measure_regen:
                # Si seule la conductance était sélectionnée, quitter
                print("No other measurements selected, exiting.")
                if arduino_connected:
                    arduino.close()
                if regen_connected:
                    regen.close()
                sys.exit(1)
            else:
                # Sinon, afficher un message et désactiver la mesure de conductance
                messagebox.showwarning(
                    "Appareil non disponible", 
                    "Impossible de se connecter au Keithley pour la mesure de conductance.\n\n"
                    "Les autres mesures sélectionnées seront effectuées."
                )
                measure_conductance = 0  # Désactiver la mesure
                print("Continuing with other available measurements.")
        else:
            keithley_connected = True
            available_measurements.append("Conductance")
    else:
        print("Conductance measurement disabled - skipping Keithley connection")
        
    if not keithley_connected:
        # Initialiser un objet Keithley simulé pour éviter les erreurs
        print("Keithley not needed or not available - using dummy device")
        keithley = type('DummyKeithley', (), {
            'read_resistance': lambda: 1000000.0,  # 1 MOhm par défaut
            'turn_output_on': lambda: True,
            'turn_output_off': lambda: True,
            'close': lambda *args: None,  # Accepte un self implicite
            'device': None
        })()
        
    # Vérifier qu'au moins une mesure est encore disponible
    if not available_measurements:
        messagebox.showerror(
            "Aucun appareil disponible", 
            "Aucun des appareils nécessaires pour les mesures sélectionnées n'est disponible.\n\n"
            "Veuillez vérifier les connexions et réessayer."
        )
        print("No available measurements - exiting")
        sys.exit(1)
    else:
        # Afficher les mesures disponibles
        print(f"Available measurements: {', '.join(available_measurements)}")
        
        # Pour la compatibilité avec le reste du code, créer des variables qui indiquent
        # quelles mesures sont réellement disponibles
        measure_conductance = "Conductance" in available_measurements
        measure_co2 = "CO2" in available_measurements
        measure_regen = "Régénération" in available_measurements
        print(f"Enabled measurements: Conductance={measure_conductance}, CO2={measure_co2}, Régénération={measure_regen}")
    
    # Initialize measurement manager
    measurements = MeasurementManager(keithley, arduino, regen)
    
    # Initialize data handler
    data_handler = ExcelHandler(mode="manual")
    
    # Initialize plots
    plot_manager = PlotManager(mode="manual")
    
    # Initialize variables for UI state based on selected measurements
    measure_conductance_active = False  # This is the runtime state
    measure_co2_temp_humidity_active = False  # This is the runtime state
    measure_res_temp_active = False  # This is the runtime state
    escape_pressed = False
    
    # Variables pour la sauvegarde de secours
    last_backup_time = time.time()
    backup_interval = 500  # Sauvegarde automatique toutes les 500 secondes (environ 8 minutes)
    last_notification_time = time.time()  # Pour limiter les notifications
    notification_cooldown = 30  # 30 secondes entre les notifications
    emergency_mode = False  # Indique si on est en mode d'urgence
    device_error_count = {
        'arduino': 0,
        'regen': 0,
        'keithley': 0
    }
    error_threshold = 5  # Nombre d'erreurs à partir duquel on déclenche une sauvegarde
    
    # Configuration pour le scan automatique des périphériques
    scan_for_devices_interval = 30  # Intervalle de scan en secondes (0 pour désactiver)
    last_device_scan_time = time.time()  # Temps du dernier scan
    last_backup_status = {
        'time': None,
        'success': False,
        'reason': "Aucune sauvegarde effectuée"
    }
    
    # Function to handle window X button close event
    def handle_window_close(event=None):
        nonlocal escape_pressed
        if not escape_pressed:  # Éviter une double fermeture
            # Call the same quit function used by the quit button
            quit_program(event)
        
    # Register the close handler
    plot_manager.set_close_callback(handle_window_close)
    
    # Initialize file state variables
    conductance_file_initialized = False
    co2_temp_humidity_file_initialized = False
    temp_res_file_initialized = False
    
    # Configure measurement panels and UI elements visibility
    plot_manager.configure_measurement_panels(
        measure_conductance=bool(measure_conductance),
        measure_co2=bool(measure_co2), 
        measure_regen=bool(measure_regen)
    )
    
    # Mettre à jour l'état des boutons d'ajout d'appareils
    plot_manager.update_add_device_buttons({
        'arduino': arduino_connected,
        'regen': regen_connected,
        'keithley': keithley_connected
    })
    
    # Initialiser l'indicateur de sauvegarde
    if hasattr(plot_manager, 'update_backup_status'):
        plot_manager.update_backup_status(last_backup_status)
    
    # Initialiser correctement les états des boutons de protocole basés sur les mesures actives
    plot_manager.update_protocol_button_states(
        measure_co2_temp_humidity_active, 
        measure_conductance_active, 
        measure_res_temp_active
    )
    
    # S'assurer que le bouton d'annulation de protocole est caché au démarrage
    if 'cancel_regeneration' in plot_manager.buttons:
        cancel_button = plot_manager.buttons['cancel_regeneration']
        cancel_button.ax.set_visible(False)
        cancel_button.active = False
    
    # Initialize R0 display
    R0 = measurements.read_R0()
    if R0 is not None:
        plot_manager.update_R0_display(R0)
    
    # Define event handlers
    def toggle_conductance(event):
        nonlocal measure_conductance_active, conductance_file_initialized
        previous_state = measure_conductance_active
        measure_conductance_active = not measure_conductance_active
        
        # Initialiser le fichier si nécessaire
        if measure_conductance_active and not conductance_file_initialized:
            data_handler.initialize_file("conductance")
            conductance_file_initialized = True
        
        # Si on arrête la mesure (passage de True à False)
        if previous_state and not measure_conductance_active:
            # Sauvegarder les données courantes
            if measurements.timeList and len(measurements.timeList) > 0:
                data_handler.save_conductance_data(
                    measurements.timeList,
                    measurements.conductanceList,
                    measurements.resistanceList
                )
        
        # Si on reprend après pause
        if not previous_state and measure_conductance_active and measurements.pause_time_conductance is not None:
            current_time = time.time()
            pause_duration = current_time - measurements.pause_time_conductance
            measurements.elapsed_time_conductance += pause_duration
        
        plot_manager.update_raz_buttons_visibility({'conductance': measure_conductance_active})
        
        # Update protocol button states based on active measurements
        plot_manager.update_protocol_button_states(
            measure_co2_temp_humidity_active,
            measure_conductance_active,
            measure_res_temp_active
        )
    
    def toggle_co2_temp_humidity(event):
        nonlocal measure_co2_temp_humidity_active, co2_temp_humidity_file_initialized
        previous_state = measure_co2_temp_humidity_active
        measure_co2_temp_humidity_active = not measure_co2_temp_humidity_active
        
        # Initialiser le fichier si nécessaire
        if measure_co2_temp_humidity_active and not co2_temp_humidity_file_initialized:
            data_handler.initialize_file("co2_temp_humidity")
            co2_temp_humidity_file_initialized = True
        
        # Si on arrête la mesure (passage de True à False)
        if previous_state and not measure_co2_temp_humidity_active:
            # Sauvegarder les données courantes
            if (measurements.timestamps_co2 and len(measurements.timestamps_co2) > 0) or \
            (measurements.timestamps_temp and len(measurements.timestamps_temp) > 0) or \
            (measurements.timestamps_humidity and len(measurements.timestamps_humidity) > 0):
                data_handler.save_co2_temp_humidity_data(
                    measurements.timestamps_co2,
                    measurements.values_co2,
                    measurements.timestamps_temp,
                    measurements.values_temp,
                    measurements.timestamps_humidity,
                    measurements.values_humidity
                )
        
        # Si on reprend après pause
        if not previous_state and measure_co2_temp_humidity_active and measurements.pause_time_co2_temp_humidity is not None:
            current_time = time.time()
            pause_duration = current_time - measurements.pause_time_co2_temp_humidity
            measurements.elapsed_time_co2_temp_humidity += pause_duration
        
        plot_manager.update_raz_buttons_visibility({'co2_temp_humidity': measure_co2_temp_humidity_active})
        
        # Update protocol button states based on active measurements
        plot_manager.update_protocol_button_states(
            measure_co2_temp_humidity_active,
            measure_conductance_active,
            measure_res_temp_active
        )
    
    def toggle_res_temp(event):
        nonlocal measure_res_temp_active, temp_res_file_initialized
        previous_state = measure_res_temp_active
        measure_res_temp_active = not measure_res_temp_active
        
        # Initialiser le fichier si nécessaire
        if measure_res_temp_active and not temp_res_file_initialized:
            data_handler.initialize_file("temp_res")
            temp_res_file_initialized = True
        
        # Si on arrête la mesure (passage de True à False)
        if previous_state and not measure_res_temp_active:
            # Sauvegarder les données courantes
            if measurements.timestamps_res_temp and len(measurements.timestamps_res_temp) > 0:
                data_handler.save_temp_res_data(
                    measurements.timestamps_res_temp,
                    measurements.temperatures,
                    measurements.Tcons_values
                )
        
        # Si on reprend après pause
        if not previous_state and measure_res_temp_active and measurements.pause_time_res_temp is not None:
            current_time = time.time()
            pause_duration = current_time - measurements.pause_time_res_temp
            measurements.elapsed_time_res_temp += pause_duration
        
        plot_manager.update_raz_buttons_visibility({'res_temp': measure_res_temp_active})
        
        # Update protocol button states based on active measurements
        plot_manager.update_protocol_button_states(
            measure_co2_temp_humidity_active,
            measure_conductance_active,
            measure_res_temp_active
        )
        
    def update_regeneration_button_state():
        """Met à jour l'état des boutons de protocole en fonction des mesures actives"""
        # Use the new method to update protocol button states
        plot_manager.update_protocol_button_states(
            measure_co2_temp_humidity_active,
            measure_conductance_active,
            measure_res_temp_active
        )
    
    def raz_conductance(event):
        # Préparer les données pour l'essai cumulé sans créer de nouvelle feuille
        if measurements.timeList and len(measurements.timeList) > 0:
            data_handler.raz_conductance_data(
                measurements.timeList,
                measurements.conductanceList,
                measurements.resistanceList
            )
        
        # Réinitialiser les données courantes
        measurements.reset_data("conductance")
        measurements.reset_data("detection")
        
        plot_manager.update_conductance_plot([], [])
        plot_manager.update_detection_indicators(False, False)
        
        # Ne pas réinitialiser l'indicateur de temps de percolation lors d'un RAZ
        # Si measurements.increase_time existe encore, afficher cette valeur, sinon afficher 0
        if 'percolation_time_display' in plot_manager.indicators:
            ax_percolation_time = plot_manager.indicators['percolation_time_display']
            ax_percolation_time.clear()
            # Utiliser la valeur de increase_time si elle existe, sinon afficher 0
            perco_value = measurements.increase_time if measurements.increase_time is not None else 0
            ax_percolation_time.text(0.5, 0.5, f"T perco: {perco_value:.1f} s", 
                                   ha="center", va="center", transform=ax_percolation_time.transAxes)
            ax_percolation_time.axis('off')
            ax_percolation_time.figure.canvas.draw_idle()
    
    def raz_co2_temp_humidity(event):
        # Préparer les données pour l'essai cumulé
        if (measurements.timestamps_co2 and len(measurements.timestamps_co2) > 0) or \
        (measurements.timestamps_temp and len(measurements.timestamps_temp) > 0) or \
        (measurements.timestamps_humidity and len(measurements.timestamps_humidity) > 0):
            data_handler.raz_co2_temp_humidity_data(
                measurements.timestamps_co2,
                measurements.values_co2,
                measurements.timestamps_temp,
                measurements.values_temp,
                measurements.timestamps_humidity,
                measurements.values_humidity
            )
        
        # Réinitialiser les données courantes
        measurements.reset_data("co2_temp_humidity")
        plot_manager.update_co2_temp_humidity_plot([], [], [], [], [], [])
    
    def raz_res_temp(event):
        # Préparer les données pour l'essai cumulé
        if measurements.timestamps_res_temp and len(measurements.timestamps_res_temp) > 0:
            data_handler.raz_temp_res_data(
                measurements.timestamps_res_temp,
                measurements.temperatures,
                measurements.Tcons_values
            )
        
        # Réinitialiser les données courantes
        measurements.reset_data("res_temp")
        plot_manager.update_res_temp_plot([], [], [])
    
    def set_R0(event):
        value = plot_manager.textboxes['R0'].text
        measurements.set_R0(value)
    
    def set_Tcons(event):
        value = plot_manager.textboxes['Tcons'].text
        success = measurements.set_Tcons(value)
        if success and measure_res_temp_active:
            # Forcer une lecture immédiate pour mettre à jour l'affichage
            temp_data = measurements.read_res_temp()
            if temp_data:
                plot_manager.update_res_temp_plot(
                    measurements.timestamps_res_temp,
                    measurements.temperatures,
                    measurements.Tcons_values
                )
    
    def update_read_R0(event):
        R0 = measurements.read_R0()
        if R0 is not None:
            plot_manager.update_R0_display(R0)
    
    def push_open(event):
        measurements.push_open_sensor()
        # Les voyants seront mis à jour par la lecture des pins
    
    def retract_close(event):
        measurements.retract_close_sensor()
        # Les voyants seront mis à jour par la lecture des pins
    
    def init_system(event):
        measurements.init_system()
        # La couleur est maintenue automatiquement par le connect_button modifié
    
    def start_regeneration(event):
        """Handle regeneration button click"""
        # Only do something if button is active (not already in regeneration)
        if hasattr(plot_manager.buttons['regeneration'], 'active') and plot_manager.buttons['regeneration'].active:
            # Check if conductance regen is in progress - don't allow both at the same time
            if measurements.conductance_regen_in_progress:
                print("Impossible de démarrer le protocole CO2 pendant que le protocole Conductance est actif")
                return
                
            # Start regeneration protocol
            success = measurements.start_regeneration_protocol()
            if success:
                # Update button state
                plot_manager.update_regeneration_status({
                    'active': True,
                    'step': 1,
                    'message': "Starting regeneration protocol",
                    'progress': 0
                })
                
                # Disable conductance regeneration button while this protocol is active
                if 'conductance_regen' in plot_manager.buttons:
                    conductance_regen_button = plot_manager.buttons['conductance_regen']
                    conductance_regen_button.ax.set_facecolor('lightgray')
                    conductance_regen_button.color = 'lightgray'
                    conductance_regen_button.label.set_color('black')
                    conductance_regen_button.active = False
                    conductance_regen_button.ax.figure.canvas.draw_idle()
                
                # Mettre à jour l'état du bouton regeneration (CO2)
                regeneration_button = plot_manager.buttons['regeneration']
                regeneration_button.ax.set_facecolor('lightgray')
                regeneration_button.color = 'lightgray'
                regeneration_button.label.set_color('black')
                regeneration_button.active = False
                # Button will be reactivated when regeneration completes
    
    def cancel_regeneration(event):
        """Handle regeneration cancel button click"""
        # Only do something if button is active and visible
        if hasattr(plot_manager.buttons['cancel_regeneration'], 'active') and plot_manager.buttons['cancel_regeneration'].active:
            if measurements.regeneration_in_progress:
                # Cancel CO2 regeneration protocol
                success = measurements.cancel_regeneration_protocol()
                if success:
                    # Update button state
                    plot_manager.update_regeneration_status({
                        'active': False,
                        'step': 0,
                        'message': "Regeneration cancelled",
                        'progress': 0
                    })
                    
                    # Re-enable protocol buttons based on measurement conditions
                    plot_manager.update_protocol_button_states(
                        measure_co2_temp_humidity_active,
                        measure_conductance_active,
                        measure_res_temp_active
                    )
            elif measurements.conductance_regen_in_progress:
                # Cancel conductance regeneration protocol
                success = measurements.cancel_conductance_regen_protocol()
                if success:
                    # Update button state
                    plot_manager.update_regeneration_status({
                        'active': False,
                        'step': 0,
                        'message': "Conductance protocol cancelled",
                        'progress': 0
                    })
                    
                    # Re-enable protocol buttons based on measurement conditions
                    plot_manager.update_protocol_button_states(
                        measure_co2_temp_humidity_active,
                        measure_conductance_active,
                        measure_res_temp_active
                    )
            
    def quit_program(event):
        nonlocal escape_pressed
        # Définir Tcons à 0°C avant de fermer
        from core.constants import TCONS_LOW
        try:
            measurements.set_Tcons(str(TCONS_LOW))
            print(f"Tcons défini à {TCONS_LOW}°C avant fermeture")
        except Exception as e:
            print(f"Erreur lors de la définition de Tcons: {e}")
        
        # Désactiver le flag de fonctionnement
        escape_pressed = True
        
        # Sauvegarder les données avant de fermer les connexions
        try:
            # Vérifier si des fichiers ont été initialisés (même si les mesures sont arrêtées)
            files_initialized = (
                data_handler.conductance_file is not None or
                data_handler.co2_temp_humidity_file is not None or
                data_handler.temp_res_file is not None
            )
            
            # Vérifier si nous avons eu une sauvegarde d'urgence récente
            current_time = time.time()
            recent_emergency_backup = hasattr(perform_emergency_backup, 'last_emergency_time') and \
                                    (current_time - perform_emergency_backup.last_emergency_time < 60)
                
            if recent_emergency_backup:
                print("Une sauvegarde d'urgence a été effectuée récemment. Pas besoin de sauvegarder à nouveau.")
            else:
                # Sauvegarder les données si elles sont en cours d'acquisition
                if measure_conductance_active and measurements.timeList and len(measurements.timeList) > 0:
                    print("Sauvegarde des données de conductance avant fermeture...")
                    sheet_name = f"Cond_{datetime.now().strftime('%H%M%S')}"
                    data_handler.save_conductance_data(
                        measurements.timeList,
                        measurements.conductanceList,
                        measurements.resistanceList
                    )
                
                if measure_co2_temp_humidity_active and ((measurements.timestamps_co2 and len(measurements.timestamps_co2) > 0) or \
                   (measurements.timestamps_temp and len(measurements.timestamps_temp) > 0) or \
                   (measurements.timestamps_humidity and len(measurements.timestamps_humidity) > 0)):
                    print("Sauvegarde des données CO2/temp/humidity avant fermeture...")
                    sheet_name = f"CO2_{datetime.now().strftime('%H%M%S')}"
                    data_handler.save_co2_temp_humidity_data(
                        measurements.timestamps_co2,
                        measurements.values_co2,
                        measurements.timestamps_temp,
                        measurements.values_temp,
                        measurements.timestamps_humidity,
                        measurements.values_humidity
                    )
                    
                if measure_res_temp_active and measurements.timestamps_res_temp and len(measurements.timestamps_res_temp) > 0:
                    print("Sauvegarde des données temp/resistance avant fermeture...")
                    sheet_name = f"Temp_{datetime.now().strftime('%H%M%S')}"
                    data_handler.save_temp_res_data(
                        measurements.timestamps_res_temp,
                        measurements.temperatures,
                        measurements.Tcons_values
                    )
                
            # Forcer la création des feuilles cumulées pour tous les fichiers initialisés
            if data_handler.conductance_file and data_handler.conductance_series_count >= 2:
                print("Création de la feuille 'Essais cumulés' pour conductance...")
                data_handler._update_cumulative_sheet(data_handler.conductance_file)
                
            if data_handler.co2_temp_humidity_file and data_handler.co2_temp_humidity_series_count >= 2:
                print("Création de la feuille 'Essais cumulés' pour CO2/temp/humidity...")
                data_handler._update_cumulative_sheet(data_handler.co2_temp_humidity_file)
                
            if data_handler.temp_res_file and data_handler.temp_res_series_count >= 2:
                print("Création de la feuille 'Essais cumulés' pour temp/resistance...")
                data_handler._update_cumulative_sheet(data_handler.temp_res_file)
                
            # La création de graphiques dans les fichiers Excel est désactivée
            # Les graphiques peuvent être créés directement dans Excel après l'exportation

            # Ajouter les graphiques aux fichiers Excel
            if data_handler.conductance_file:
                print("Ajout des graphiques pour conductance...")
                data_handler.add_charts_to_excel(data_handler.conductance_file)
                
            if data_handler.co2_temp_humidity_file:
                print("Ajout des graphiques pour CO2/temp/humidity...")
                data_handler.add_charts_to_excel(data_handler.co2_temp_humidity_file)
                
            if data_handler.temp_res_file:
                print("Ajout des graphiques pour temp/resistance...")
                data_handler.add_charts_to_excel(data_handler.temp_res_file)
                
            # Proposer à l'utilisateur de renommer le dossier de données si des fichiers ont été initialisés
            if files_initialized and hasattr(data_handler, 'test_folder_path') and data_handler.test_folder_path is not None:
                print(f"Les données ont été enregistrées dans: {data_handler.test_folder_path}")
                
                import tkinter as tk
                from tkinter import simpledialog
                
                # Créer une fenêtre Tkinter et la configurer pour être au premier plan
                root = tk.Tk()
                root.withdraw()  # Cacher la fenêtre principale
                root.attributes('-topmost', True)  # Mettre au premier plan
                
                # Obtenir le nom initial du dossier
                initial_folder_name = os.path.basename(data_handler.test_folder_path)
                
                # Afficher la boîte de dialogue pour le nouveau nom avec focus
                new_folder_name = simpledialog.askstring(
                    "Renommer le dossier de données", 
                    "Voulez-vous renommer le dossier de données ? (Laissez vide pour conserver le nom actuel)",
                    initialvalue=initial_folder_name,
                    parent=root  # Utiliser root comme parent pour hériter du topmost
                )
                
                # Si l'utilisateur a fourni un nom différent, renommer le dossier
                if new_folder_name and new_folder_name.strip() and new_folder_name.strip() != initial_folder_name:
                    data_handler.rename_test_folder(new_folder_name.strip())
                    print(f"Dossier renommé en: {new_folder_name.strip()}")
            else:
                print("Aucune donnée à sauvegarder")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des données: {e}")

        # Close all connections
        print("Fermeture des connexions...")
        try:
            if keithley is not None:
                keithley.close()
            if arduino_connected:
                arduino.close()
            if regen_connected:
                regen.close()
        except Exception as e:
            print(f"Erreur lors de la fermeture des connexions: {e}")
        
        # Fermeture de tous les graphiques
        try:
            # Fermer proprement les threads matplotlib en arrière-plan
            import matplotlib
            matplotlib.pyplot.close('all')
            
            # Forcer la fermeture de toutes les figures matplotlib
            plt.ioff()
            plt.close('all')
            
            # Fermeture explicite du plot_manager
            if plot_manager.fig is not None:
                plt.close(plot_manager.fig)
                plot_manager.fig = None
            
            # Fermer toutes les références aux traceurs pour libérer la mémoire
            print("Fermeture de l'interface graphique...")
            plot_manager.close()
        except Exception as e:
            print(f"Erreur lors de la fermeture des graphiques: {e}")
        
        # Forcer le ramasse-miettes Python pour libérer la mémoire
        import gc
        gc.collect()
        
        # Terminer l'exécution immédiatement
        import sys
        print("Arrêt du programme")
        sys.exit(0)
    
    # Function to toggle all measurements together
    def toggle_all_measurements(event):
        # Call toggle functions only for available measurements
        if measure_conductance:
            toggle_conductance(event)
        if measure_co2:
            toggle_co2_temp_humidity(event)
        if measure_regen:
            toggle_res_temp(event)
            
        # Update protocol button states based on active measurements
        plot_manager.update_protocol_button_states(
            measure_co2_temp_humidity_active,
            measure_conductance_active,
            measure_res_temp_active
        )
            
    def perform_emergency_backup(reason="sauvegarde automatique"):
        """
        Effectue une sauvegarde d'urgence des données en cas de problème avec un appareil
        ou périodiquement pour éviter la perte de données
        
        Args:
            reason: Raison de la sauvegarde (pour le journal et les notifications)
            
        Returns:
            bool: True si des données ont été sauvegardées, False sinon
        """
        nonlocal last_backup_status, emergency_mode
        
        try:
            data_saved = False
            timestamp = time.time()
            backup_time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
            has_active_measurements = measure_conductance_active or measure_co2_temp_humidity_active or measure_res_temp_active
            
            # Si aucune mesure n'est active, pas besoin de sauvegarde
            if not has_active_measurements:
                print(f"Aucune mesure active - pas de sauvegarde nécessaire")
                last_backup_status = {
                    'time': timestamp,
                    'success': True,
                    'reason': "Aucune mesure active"
                }
                return False
            
            # N'afficher qu'un message court si c'est une sauvegarde automatique en mode normal
            if "automatique" in reason and not emergency_mode:
                print(f"\n--- Sauvegarde automatique ({backup_time_str}) ---")
            else:
                print(f"\n=== SAUVEGARDE D'URGENCE ({backup_time_str}) : {reason} ===")
            
            # Pour les sauvegardes automatiques, on ne crée pas de nouvelles feuilles Excel
            # sauf en cas d'urgence où on veut être sûr de ne pas perdre de données
            is_auto_backup = "automatique" in reason and not emergency_mode
            
            # Variables pour garder trace de la dernière feuille si besoin
            sheet_name_conductance = None
            sheet_name_co2 = None
            sheet_name_temp_res = None
            
            # Sauvegarde des données de conductance si actives
            if measure_conductance_active and measurements.timeList and len(measurements.timeList) > 0:
                try:
                    print(f"Sauvegarde des données de conductance...")
                    
                    # Vérifier si une feuille existe déjà pour ce fichier
                    if is_auto_backup:
                        # Pour les sauvegardes automatiques, utiliser "AutoSave" comme nom de feuille fixe
                        # La fonction save_conductance_data va mettre à jour cette feuille si elle existe déjà
                        sheet_name_conductance = "AutoSave"
                    else:
                        # En cas d'urgence, créer une nouvelle feuille avec un timestamp
                        sheet_name_conductance = f"Cond_{datetime.now().strftime('%H%M%S')}"
                    
                    # On utilise toujours save_conductance_data, mais avec un nom de feuille spécifique 
                    # pour les sauvegardes automatiques
                    data_handler.save_conductance_data(
                        measurements.timeList,
                        measurements.conductanceList,
                        measurements.resistanceList,
                        sheet_name=sheet_name_conductance
                    )
                    
                    print(f"✓ {len(measurements.timeList)} points de conductance sauvegardés")
                    data_saved = True
                except Exception as e:
                    print(f"✗ Erreur lors de la sauvegarde des données de conductance: {e}")
            
            # Sauvegarde des données CO2/temp/humidity si actives
            if measure_co2_temp_humidity_active and measurements.timestamps_co2 and len(measurements.timestamps_co2) > 0:
                try:
                    print(f"Sauvegarde des données CO2/température/humidité...")
                    
                    if is_auto_backup:
                        # Pour les sauvegardes automatiques, utiliser "AutoSave" comme nom de feuille fixe
                        sheet_name_co2 = "AutoSave"
                    else:
                        # En cas d'urgence, créer une nouvelle feuille
                        sheet_name_co2 = f"CO2_{datetime.now().strftime('%H%M%S')}"
                    
                    data_handler.save_co2_temp_humidity_data(
                        measurements.timestamps_co2,
                        measurements.values_co2,
                        measurements.timestamps_temp,
                        measurements.values_temp,
                        measurements.timestamps_humidity,
                        measurements.values_humidity,
                        sheet_name=sheet_name_co2
                    )
                    
                    print(f"✓ {len(measurements.timestamps_co2)} points de CO2/T/H sauvegardés")
                    data_saved = True
                except Exception as e:
                    print(f"✗ Erreur lors de la sauvegarde des données CO2/T/H: {e}")
            
            # Sauvegarde des données de température/résistance si actives
            if measure_res_temp_active and measurements.timestamps_res_temp and len(measurements.timestamps_res_temp) > 0:
                try:
                    print(f"Sauvegarde des données de température/résistance...")
                    
                    if is_auto_backup:
                        # Pour les sauvegardes automatiques, utiliser "AutoSave" comme nom de feuille fixe
                        sheet_name_temp_res = "AutoSave"
                    else:
                        # En cas d'urgence, créer une nouvelle feuille
                        sheet_name_temp_res = f"Temp_{datetime.now().strftime('%H%M%S')}"
                    
                    data_handler.save_temp_res_data(
                        measurements.timestamps_res_temp,
                        measurements.temperatures,
                        measurements.Tcons_values,
                        sheet_name=sheet_name_temp_res
                    )
                    
                    print(f"✓ {len(measurements.timestamps_res_temp)} points de température/résistance sauvegardés")
                    data_saved = True
                except Exception as e:
                    print(f"✗ Erreur lors de la sauvegarde des données de température/résistance: {e}")
            
            # Mettre à jour le statut de la dernière sauvegarde
            last_backup_status = {
                'time': timestamp,
                'success': data_saved,
                'reason': reason
            }
            
            if data_saved:
                # Afficher un message différent selon le type de sauvegarde
                if "automatique" in reason and not emergency_mode:
                    print(f"--- Sauvegarde terminée ({backup_time_str}) ---\n")
                else:
                    print(f"=== SAUVEGARDE RÉUSSIE ({backup_time_str}) ===\n")
                
                # Le mode d'urgence est géré dans la boucle principale
            else:
                # Afficher un message différent selon le type de sauvegarde
                if "automatique" in reason and not emergency_mode:
                    print(f"--- Aucune donnée à sauvegarder ({backup_time_str}) ---\n")
                else:
                    print(f"=== AUCUNE DONNÉE SAUVEGARDÉE ({backup_time_str}) ===\n")
            
            return data_saved
            
        except Exception as e:
            print(f"=== ERREUR LORS DE LA SAUVEGARDE D'URGENCE: {e} ===\n")
            last_backup_status = {
                'time': time.time(),
                'success': False,
                'reason': f"Erreur: {str(e)}"
            }
            return False
            
    def show_backup_notification(reason):
        """
        Affiche une notification à l'utilisateur concernant la sauvegarde d'urgence
        
        Args:
            reason: Raison de la sauvegarde
        """
        nonlocal last_notification_time, notification_cooldown
        
        current_time = time.time()
        # Limiter les notifications pour éviter de spammer l'utilisateur
        if current_time - last_notification_time < notification_cooldown:
            return
            
        # Mettre à jour le timestamp de la dernière notification
        last_notification_time = current_time
        
        try:
            # Créer une notification visuelle dans une nouvelle fenêtre indépendante
            import tkinter as tk
            from tkinter import messagebox
            
            # Créer une fenêtre Tkinter invisible pour éviter de perturber l'interface principale
            root = tk.Tk()
            root.withdraw()
            
            # Afficher le message contextuel
            messagebox.showinfo(
                "Sauvegarde d'urgence",
                f"Une sauvegarde d'urgence a été effectuée.\n\n"
                f"Raison: {reason}\n\n"
                f"Les données ont été sauvegardées dans le dossier des résultats."
            )
            
            # Détruire la fenêtre Tkinter
            root.destroy()
        except Exception as e:
            print(f"Erreur lors de l'affichage de la notification: {e}")
            
    def check_device_errors():
        """
        Vérifie les erreurs des appareils pour détecter des problèmes de connexion
        
        Returns:
            dict: Informations sur les erreurs détectées
        """
        nonlocal device_error_count, emergency_mode, error_threshold
        
        errors_detected = False
        error_info = {
            'total_errors': sum(device_error_count.values()),
            'arduino_errors': device_error_count['arduino'],
            'regen_errors': device_error_count['regen'],
            'keithley_errors': device_error_count['keithley'],
            'critical': False,
            'message': ""
        }
        
        # Vérifier le nombre total d'erreurs
        if error_info['total_errors'] >= error_threshold:
            errors_detected = True
            error_info['critical'] = True
            
            # Déterminer quel(s) appareil(s) cause(nt) le problème
            problem_devices = []
            if device_error_count['arduino'] >= 2 and arduino_connected:
                problem_devices.append("Arduino")
            if device_error_count['regen'] >= 2 and regen_connected:
                problem_devices.append("Carte de régénération")
            if device_error_count['keithley'] >= 2 and keithley_connected:
                problem_devices.append("Keithley")
                
            if problem_devices:
                device_list = ", ".join(problem_devices)
                error_info['message'] = f"Problèmes de communication avec: {device_list}"
            else:
                error_info['message'] = "Problèmes de communication avec plusieurs appareils"
        
        # Si c'est la première détection d'une erreur critique, passer en mode d'urgence
        if error_info['critical'] and not emergency_mode:
            emergency_mode = True
            print(f"\n=== ALERTE: PROBLÈMES DE COMMUNICATION DÉTECTÉS ===")
            print(f"Appareils problématiques: {error_info['message']}")
            print("Activation du mode de sauvegarde d'urgence")
            print("Les données seront sauvegardées automatiquement plus fréquemment.")
            print("=== SAUVEGARDE DE SECOURS INITIÉE ===\n")
        
        return error_info
            
    def add_arduino_device(event):
        """Fonction pour ajouter un Arduino en cours d'exécution"""
        nonlocal arduino, arduino_connected, measure_co2
        
        if arduino_connected:
            return  # L'Arduino est déjà connecté
        
        # Utiliser la classe MenuUI pour détecter automatiquement le port Arduino
        from ui.menu import MenuUI
        
        # Créer une instance temporaire invisible pour scanner les ports
        temp_menu = MenuUI()
        temp_menu.window.withdraw()  # Rendre la fenêtre invisible
        
        # Scanner les ports disponibles
        port_info = temp_menu.refresh_ports(show_message=False)
        temp_menu.window.destroy()  # Fermer la fenêtre temporaire
        
        arduino_port = None
        arduino_port_index = port_info.get('arduino_port_index')
        ports_display = port_info.get('ports_display', [])
        
        # Si un Arduino a été détecté automatiquement
        if arduino_port_index is not None and arduino_port_index < len(ports_display):
            # Extraire le port COM (avant le premier espace)
            arduino_port = ports_display[arduino_port_index].split()[0]
            print(f"Arduino détecté automatiquement sur le port: {arduino_port}")
        else:
            # Si aucun Arduino n'est détecté automatiquement, ouvrir une boîte de dialogue
            import tkinter as tk
            from tkinter import simpledialog
            
            root = tk.Tk()
            root.withdraw()  # Cacher la fenêtre principale
            
            # Créer une liste de choix à partir des ports disponibles
            choices = [port.split()[0] for port in ports_display] if ports_display else [""]
            choice_str = "\n".join([f"{i+1}. {port}" for i, port in enumerate(ports_display)])
            
            # Demander à l'utilisateur de choisir un port
            port_choice = simpledialog.askinteger(
                "Sélection du port Arduino",
                f"Aucun Arduino n'a été détecté automatiquement.\nVeuillez sélectionner un port (numéro):\n\n{choice_str}",
                minvalue=1, maxvalue=len(choices) if choices else 1
            )
            
            if port_choice and port_choice <= len(choices):
                arduino_port = choices[port_choice-1]
            else:
                # L'utilisateur a annulé ou n'a pas sélectionné de port valide
                print("Ajout de l'Arduino annulé")
                # Réactiver le bouton d'ajout
                plot_manager.add_device_buttons['arduino'].active = True
                plot_manager.add_device_buttons['arduino'].ax.set_facecolor('lightskyblue')
                plot_manager.add_device_buttons['arduino'].color = 'lightskyblue'
                plot_manager.fig.canvas.draw_idle()
                return
        
        # Essayer de connecter l'Arduino
        if arduino_port:
            # Créer un nouvel appareil Arduino et tenter de le connecter
            arduino = ArduinoDevice(port=arduino_port, baud_rate=115200)  # Valeur par défaut
            if arduino.connect():
                arduino_connected = True
                measure_co2 = True  # Activer la mesure de CO2
                
                # Mettre à jour l'interface
                plot_manager.update_add_device_buttons({'arduino': True})
                plot_manager.configure_measurement_panels(
                    measure_conductance=bool(measure_conductance),
                    measure_co2=True,  # Maintenant disponible
                    measure_regen=bool(measure_regen)
                )
                
                # Si on était en train de mesurer le CO2, il faut redémarrer la mesure
                if measure_co2_temp_humidity_active:
                    toggle_co2_temp_humidity(None)  # Arrêter
                    toggle_co2_temp_humidity(None)  # Redémarrer
                
                print(f"Arduino connecté avec succès sur le port {arduino_port}")
            else:
                # Échec de la connexion
                print(f"Échec de la connexion à l'Arduino sur le port {arduino_port}")
                
                # Réactiver le bouton d'ajout
                plot_manager.add_device_buttons['arduino'].active = True
                plot_manager.add_device_buttons['arduino'].ax.set_facecolor('lightskyblue')
                plot_manager.add_device_buttons['arduino'].color = 'lightskyblue'
                plot_manager.fig.canvas.draw_idle()
    
    # Définir les fonctions d'ajout d'appareils
    def add_keithley_device(event=None):
        """Fonction pour ajouter un Keithley en cours d'exécution"""
        nonlocal keithley, keithley_connected, measure_conductance
        
        if keithley_connected:
            return  # Le Keithley est déjà connecté
        
        # Essayer de connecter le Keithley
        print("Tentative de connexion au Keithley...")
        
        # On supprime toute instance précédente
        if 'keithley' in globals():
            try:
                if hasattr(keithley, 'close'):
                    keithley.close()
            except:
                pass
            
        # Create fresh instance
        keithley = KeithleyDevice()
        
        # Temps de pause avant connexion
        time.sleep(1)  # Attendre 1 seconde
        
        # Tentative de connexion
        if keithley.connect():
            keithley_connected = True
            measure_conductance = True  # Activer la mesure de conductance
            
            # Réinitialiser les flags de déconnexion
            add_keithley_device.disconnection_reported = False
            
            # IMPORTANT: Mettre à jour le dispositif dans le gestionnaire de mesures
            # Synchronisation complète
            if hasattr(measurements, 'read_conductance'):
                measurements.keithley = keithley
                # On a besoin d'une référence partagée pour le device
                # pour que les changements soient visibles des deux côtés
                print(f"Mise à jour du Keithley dans MeasurementManager: {keithley}")
                print(f"Vérification état Keithley après mise à jour: measurements.keithley = {measurements.keithley}, device = {measurements.keithley.device if hasattr(measurements.keithley, 'device') else 'None'}")
                
                # Force la réinitialisation du flag d'erreur dans MeasurementManager
                if hasattr(measurements, '_keithley_error_reported'):
                    measurements._keithley_error_reported = False
            
            # Mettre à jour l'interface
            plot_manager.update_add_device_buttons({'keithley': True})
            plot_manager.configure_measurement_panels(
                measure_conductance=True,
                measure_co2=bool(measure_co2),
                measure_regen=bool(measure_regen)
            )
            
            print("Keithley connecté avec succès")
        else:
            print("Échec de la connexion au Keithley")
            
            # Réactiver le bouton d'ajout
            if 'keithley' in plot_manager.add_device_buttons:
                plot_manager.add_device_buttons['keithley'].active = True
                plot_manager.add_device_buttons['keithley'].ax.set_facecolor('lightcoral')
                plot_manager.add_device_buttons['keithley'].color = 'lightcoral'
                plot_manager.fig.canvas.draw_idle()
    
    # Initialiser les flags de déconnexion
    add_keithley_device.disconnection_reported = False
    
    def add_regen_device(event):
        """Fonction pour ajouter une carte de régénération en cours d'exécution"""
        nonlocal regen, regen_connected, measure_regen
        
        if regen_connected:
            return  # La carte de régénération est déjà connectée
        
        # Utiliser la classe MenuUI pour détecter automatiquement le port
        from ui.menu import MenuUI
        
        # Créer une instance temporaire invisible pour scanner les ports
        temp_menu = MenuUI()
        temp_menu.window.withdraw()  # Rendre la fenêtre invisible
        
        # Scanner les ports disponibles
        port_info = temp_menu.refresh_ports(show_message=False)
        temp_menu.window.destroy()  # Fermer la fenêtre temporaire
        
        regen_port = None
        regen_port_index = port_info.get('regen_port_index')
        ports_display = port_info.get('ports_display', [])
        
        # Si une carte de régénération a été détectée automatiquement
        if regen_port_index is not None and regen_port_index < len(ports_display):
            # Extraire le port COM (avant le premier espace)
            regen_port = ports_display[regen_port_index].split()[0]
            print(f"Carte de régénération détectée automatiquement sur le port: {regen_port}")
        else:
            # Si aucune carte n'est détectée automatiquement, ouvrir une boîte de dialogue
            import tkinter as tk
            from tkinter import simpledialog
            
            root = tk.Tk()
            root.withdraw()  # Cacher la fenêtre principale
            
            # Créer une liste de choix à partir des ports disponibles
            choices = [port.split()[0] for port in ports_display] if ports_display else [""]
            choice_str = "\n".join([f"{i+1}. {port}" for i, port in enumerate(ports_display)])
            
            # Demander à l'utilisateur de choisir un port
            port_choice = simpledialog.askinteger(
                "Sélection du port pour la carte de régénération",
                f"Aucune carte de régénération n'a été détectée automatiquement.\nVeuillez sélectionner un port (numéro):\n\n{choice_str}",
                minvalue=1, maxvalue=len(choices) if choices else 1
            )
            
            if port_choice and port_choice <= len(choices):
                regen_port = choices[port_choice-1]
            else:
                # L'utilisateur a annulé ou n'a pas sélectionné de port valide
                print("Ajout de la carte de régénération annulé")
                # Réactiver le bouton d'ajout
                plot_manager.add_device_buttons['regen'].active = True
                plot_manager.add_device_buttons['regen'].ax.set_facecolor('lightcoral')
                plot_manager.add_device_buttons['regen'].color = 'lightcoral'
                plot_manager.fig.canvas.draw_idle()
                return
        
        # Essayer de connecter la carte de régénération
        if regen_port:
            # Créer un nouvel appareil et tenter de le connecter
            regen = RegenDevice(port=regen_port, baud_rate=115200)  # Valeur par défaut
            if regen.connect():
                regen_connected = True
                measure_regen = True  # Activer la mesure de régénération
                
                # Réinitialiser les flags de déconnexion/erreur
                if hasattr(add_regen_device, 'disconnection_reported'):
                    add_regen_device.disconnection_reported = False
                if hasattr(add_regen_device, 'error_reported'):
                    add_regen_device.error_reported = False
                
                # IMPORTANT: Mettre à jour le dispositif dans le gestionnaire de mesures
                measurements.regen = regen
                print(f"Mise à jour du dispositif dans MeasurementManager: {regen}")
                
                # Mettre à jour l'interface
                plot_manager.update_add_device_buttons({'regen': True})
                plot_manager.configure_measurement_panels(
                    measure_conductance=bool(measure_conductance),
                    measure_co2=bool(measure_co2),
                    measure_regen=True  # Maintenant disponible
                )
                
                # Si on était en train de mesurer la température, il faut redémarrer la mesure
                if measure_res_temp_active:
                    toggle_res_temp(None)  # Arrêter
                    toggle_res_temp(None)  # Redémarrer
                
                print(f"Carte de régénération connectée avec succès sur le port {regen_port}")
                
                # Test silencieux pour vérifier que la communication fonctionne
                measurements.read_R0()
            else:
                # Échec de la connexion
                print(f"Échec de la connexion à la carte de régénération sur le port {regen_port}")
                
                # Réactiver le bouton d'ajout
                plot_manager.add_device_buttons['regen'].active = True
                plot_manager.add_device_buttons['regen'].ax.set_facecolor('lightcoral')
                plot_manager.add_device_buttons['regen'].color = 'lightcoral'
                plot_manager.fig.canvas.draw_idle()
    
    def start_conductance_regen(event):
        """Handle conductance regeneration button click"""
        # Only do something if button is active and not already in protocol
        if hasattr(plot_manager.buttons['conductance_regen'], 'active') and plot_manager.buttons['conductance_regen'].active:
            # Check if CO2 regeneration is in progress - don't allow both at the same time
            if measurements.regeneration_in_progress:
                print("Impossible de démarrer le protocole Conductance pendant que le protocole CO2 est actif")
                return
                
            # Start conductance regeneration protocol
            success = measurements.start_conductance_regen_protocol()
            if success:
                # Update button state
                plot_manager.update_regeneration_status({
                    'active': True,
                    'step': 1,
                    'message': "Starting conductance protocol",
                    'progress': 0
                })
                
                # Disable CO2 regeneration button while this protocol is active
                if 'regeneration' in plot_manager.buttons:
                    regeneration_co2_button = plot_manager.buttons['regeneration']
                    regeneration_co2_button.ax.set_facecolor('lightgray')
                    regeneration_co2_button.color = 'lightgray'
                    regeneration_co2_button.label.set_color('black')
                    regeneration_co2_button.active = False
                    regeneration_co2_button.ax.figure.canvas.draw_idle()
                
                # Mettre à jour l'état du bouton conductance
                regeneration_button = plot_manager.buttons['conductance_regen']
                regeneration_button.ax.set_facecolor('lightgray')
                regeneration_button.color = 'lightgray'
                regeneration_button.label.set_color('black')
                regeneration_button.active = False
    
    def cancel_conductance_regen(event):
        """Handle conductance regeneration cancel button click - redirects to unified cancel function"""
        # Redirect to the unified cancel function
        cancel_regeneration(event)
    
    # Connect event handlers
    plot_manager.connect_button('conductance', toggle_conductance)
    plot_manager.connect_button('co2_temp_humidity', toggle_co2_temp_humidity)
    plot_manager.connect_button('res_temp', toggle_res_temp)
    plot_manager.connect_button('start_all', toggle_all_measurements)
    plot_manager.connect_button('raz_conductance', raz_conductance)
    plot_manager.connect_button('raz_co2_temp_humidity', raz_co2_temp_humidity)
    plot_manager.connect_button('raz_res_temp', raz_res_temp)
    plot_manager.connect_button('set_R0', set_R0)
    plot_manager.connect_button('set_Tcons', set_Tcons)
    plot_manager.connect_button('update_R0', update_read_R0)
    plot_manager.connect_button('push_open', push_open)
    plot_manager.connect_button('retract_close', retract_close)
    plot_manager.connect_button('init', init_system)
    plot_manager.connect_button('regeneration', start_regeneration)
    plot_manager.connect_button('cancel_regeneration', cancel_regeneration)
    plot_manager.connect_button('conductance_regen', start_conductance_regen)
    plot_manager.connect_button('quit', quit_program)
    
    def add_keithley_device(event):
        """Fonction pour ajouter un Keithley en cours d'exécution"""
        nonlocal keithley, keithley_connected, measure_conductance
        
        if keithley_connected:
            return  # Le Keithley est déjà connecté
        
        # Essayer de connecter le Keithley (il n'a pas besoin de port série)
        import tkinter as tk
        from tkinter import messagebox
        
        print("Tentative de connexion au Keithley...")
        
        # Créer un nouvel appareil Keithley et tenter de le connecter
        keithley = KeithleyDevice()
        
        try:
            if keithley.connect():
                keithley_connected = True
                measure_conductance = True  # Activer la mesure de conductance
                
                # Mettre à jour l'interface
                plot_manager.update_add_device_buttons({'keithley': True})
                plot_manager.configure_measurement_panels(
                    measure_conductance=True,  # Maintenant disponible
                    measure_co2=bool(measure_co2),
                    measure_regen=bool(measure_regen)
                )
                
                # Si on était en train de mesurer la conductance, il faut redémarrer la mesure
                if measure_conductance_active:
                    toggle_conductance(None)  # Arrêter
                    toggle_conductance(None)  # Redémarrer
                
                print("Keithley connecté avec succès")
                
                # Afficher un message de succès
                root = tk.Tk()
                root.withdraw()
                messagebox.showinfo("Connexion réussie", "Keithley connecté avec succès.\nLa mesure de conductance est maintenant disponible.")
                root.destroy()
            else:
                # Échec de la connexion
                print("Échec de la connexion au Keithley")
                
                # Afficher un message d'erreur
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror("Erreur de connexion", 
                                   "Impossible de se connecter au Keithley.\n\n"
                                   "Vérifiez que :\n"
                                   "- L'appareil est bien allumé\n"
                                   "- Le câble USB est correctement branché\n"
                                   "- Aucun autre logiciel n'utilise déjà l'appareil")
                root.destroy()
                
                # Réactiver le bouton d'ajout
                plot_manager.add_device_buttons['keithley'].active = True
                plot_manager.add_device_buttons['keithley'].ax.set_facecolor('lightgreen')
                plot_manager.add_device_buttons['keithley'].color = 'lightgreen'
                plot_manager.fig.canvas.draw_idle()
        except Exception as e:
            print(f"Erreur lors de la connexion au Keithley: {e}")
            
            # Afficher un message d'erreur
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Erreur de connexion", 
                               f"Erreur lors de la connexion au Keithley:\n{str(e)}\n\n"
                               "Vérifiez que les pilotes sont correctement installés.")
            root.destroy()
            
            # Réactiver le bouton d'ajout
            plot_manager.add_device_buttons['keithley'].active = True
            plot_manager.add_device_buttons['keithley'].ax.set_facecolor('lightgreen')
            plot_manager.add_device_buttons['keithley'].color = 'lightgreen'
            plot_manager.fig.canvas.draw_idle()
    
    # Connect add device buttons
    plot_manager.connect_add_device_button('arduino', add_arduino_device)
    plot_manager.connect_add_device_button('regen', add_regen_device)
    plot_manager.connect_add_device_button('keithley', add_keithley_device)
    
    # Connect radiobutton for time unit selection
    plot_manager.connect_radiobutton('time_unit', plot_manager.on_time_unit_change)
    
    # Main loop
    while not escape_pressed:
        current_time = time.time()
        
        # Lire toutes les données disponibles du port série
        # Vérifier si données disponibles et les traiter en fonction du mode actif
        # Ne tenter de lire que si l'Arduino est connecté
        if arduino_connected:
            for _ in range(10):  # Lire jusqu'à 10 lignes par itération pour vider le buffer
                line = None
                try:
                    # Vérification sécurisée pour éviter les erreurs série critiques
                    if arduino.device and hasattr(arduino.device, 'in_waiting'):
                        try:
                            # Tenter d'accéder à in_waiting de manière sécurisée
                            waiting_bytes = arduino.device.in_waiting
                            if waiting_bytes > 0:
                                line = arduino.device.readline().decode('utf-8', errors='ignore').strip()
                        except (serial.SerialException, IOError, OSError, PermissionError) as serial_err:
                            print(f"Erreur critique sur le port série Arduino: {serial_err}")
                            device_error_count['arduino'] += 2  # Augmentation plus importante pour les erreurs critiques
                            # Tentative de fermeture et réinitialisation de l'appareil
                            try:
                                if arduino.device:
                                    arduino.device.close()
                            except:
                                pass  # Ignorer les erreurs lors de la fermeture
                            arduino.device = None
                            arduino_connected = False
                            # Mettre à jour l'interface
                            plot_manager.update_add_device_buttons({'arduino': False})
                            
                            # Mettre automatiquement en pause la mesure de CO2/temp/humidity
                            if measure_co2_temp_humidity_active:
                                print("Mise en pause automatique de la mesure de CO2/température/humidité")
                                
                                # Sauvegarder immédiatement les données de CO2/temp/humidity
                                if ((measurements.timestamps_co2 and len(measurements.timestamps_co2) > 0) or
                                    (measurements.timestamps_temp and len(measurements.timestamps_temp) > 0) or
                                    (measurements.timestamps_humidity and len(measurements.timestamps_humidity) > 0)):
                                    
                                    print("Sauvegarde immédiate des données de CO2/temp/humidity suite à la déconnexion...")
                                    try:
                                        # S'assurer que le fichier est initialisé
                                        if not co2_temp_humidity_file_initialized:
                                            data_handler.initialize_file("co2_temp_humidity")
                                            co2_temp_humidity_file_initialized = True
                                        
                                        # Sauvegarde
                                        data_handler.save_co2_temp_humidity_data(
                                            measurements.timestamps_co2,
                                            measurements.values_co2,
                                            measurements.timestamps_temp,
                                            measurements.values_temp,
                                            measurements.timestamps_humidity,
                                            measurements.values_humidity
                                        )
                                        print(f"✓ {len(measurements.timestamps_co2)} points de CO2/temp/humidity sauvegardés")
                                    except Exception as e:
                                        print(f"Erreur lors de la sauvegarde des données de CO2/temp/humidity: {e}")
                                
                                measure_co2_temp_humidity_active = False
                                # Mettre à jour l'interface
                                if 'co2_temp_humidity' in plot_manager.buttons:
                                    plot_manager.buttons['co2_temp_humidity'].ax.set_facecolor('darkred')
                                    plot_manager.buttons['co2_temp_humidity'].color = 'darkred'
                                    plot_manager.buttons['co2_temp_humidity'].label.set_color('white')
                                    plot_manager.fig.canvas.draw_idle()
                            
                            # Sauvegarde d'urgence seulement si pas de sauvegarde récente
                            current_time = time.time()
                            if (not hasattr(perform_emergency_backup, 'last_emergency_time') or 
                                current_time - perform_emergency_backup.last_emergency_time >= 60):
                                perform_emergency_backup("Déconnexion Arduino détectée")
                                # Mettre à jour le timestamp pour éviter les sauvegardes en rafale
                                perform_emergency_backup.last_emergency_time = current_time
                                
                            # Sortir complètement des tentatives de lecture
                            break
                        except Exception as e:
                            print(f"Error reading from Arduino: {e}")
                            device_error_count['arduino'] += 1
                except Exception as e:
                    # Ne pas spammer la console - réduire les messages d'erreur
                    # Incrémenter le compteur quand même
                    device_error_count['arduino'] += 1
                    
                    # N'afficher l'erreur que toutes les 20 itérations environ
                    if sum(device_error_count.values()) % 20 == 0:
                        print(f"Erreur générale lors de l'accès à l'Arduino: {e}")
                        
                    # Si on a une erreur générale, marquer l'Arduino comme déconnecté
                    arduino.device = None
                    arduino_connected = False
                    plot_manager.update_add_device_buttons({'arduino': False})
                    
                    # Mettre automatiquement en pause la mesure de CO2/temp/humidity
                    if measure_co2_temp_humidity_active:
                        print("Mise en pause automatique de la mesure de CO2/température/humidité")
                        
                        # Sauvegarder immédiatement les données de CO2/temp/humidity
                        if ((measurements.timestamps_co2 and len(measurements.timestamps_co2) > 0) or
                            (measurements.timestamps_temp and len(measurements.timestamps_temp) > 0) or
                            (measurements.timestamps_humidity and len(measurements.timestamps_humidity) > 0)):
                            
                            print("Sauvegarde immédiate des données de CO2/temp/humidity suite à la déconnexion...")
                            try:
                                # S'assurer que le fichier est initialisé
                                if not co2_temp_humidity_file_initialized:
                                    data_handler.initialize_file("co2_temp_humidity")
                                    co2_temp_humidity_file_initialized = True
                                
                                # Sauvegarde
                                data_handler.save_co2_temp_humidity_data(
                                    measurements.timestamps_co2,
                                    measurements.values_co2,
                                    measurements.timestamps_temp,
                                    measurements.values_temp,
                                    measurements.timestamps_humidity,
                                    measurements.values_humidity
                                )
                                print(f"✓ {len(measurements.timestamps_co2)} points de CO2/temp/humidity sauvegardés")
                            except Exception as e:
                                print(f"Erreur lors de la sauvegarde des données de CO2/temp/humidity: {e}")
                        
                        measure_co2_temp_humidity_active = False
                        # Mettre à jour l'interface
                        if 'co2_temp_humidity' in plot_manager.buttons:
                            plot_manager.buttons['co2_temp_humidity'].ax.set_facecolor('darkred')
                            plot_manager.buttons['co2_temp_humidity'].color = 'darkred'
                            plot_manager.buttons['co2_temp_humidity'].label.set_color('white')
                            plot_manager.fig.canvas.draw_idle()
                    break
                
                if not line:
                    break  # Aucune donnée disponible, sortir de la boucle
                
                # Traiter les états des pins (pour les voyants)
                if "VR:" in line and "VS:" in line and "TO:" in line and "TF:" in line:
                    try:
                        # Parse individual pin states
                        vr_part = line.split("VR:")[1].split()[0]
                        vs_part = line.split("VS:")[1].split()[0]
                        to_part = line.split("TO:")[1].split()[0]
                        tf_part = line.split("TF:")[1].split()[0]
                        
                        # Clarify status parsing (HIGH = True, LOW = False)
                        vr_state = vr_part == "HIGH"
                        vs_state = vs_part == "HIGH"
                        to_state = to_part == "HIGH"
                        tf_state = tf_part == "HIGH"
                        
                        # Store the pin states for UI updating
                        measurements.pin_states = {
                            'vr': vr_state,  # Vérin Rentré
                            'vs': vs_state,  # Vérin Sorti
                            'to': to_state,  # Trappe Ouverte
                            'tf': tf_state   # Trappe Fermée
                        }
                        
                        # Update indicator LEDs if pin states changed
                        plot_manager.update_sensor_indicators(measurements.pin_states)
                    except Exception as e:
                        print(f"Error parsing pin states: {e}, line: {line}")
                        # Incrémenter le compteur d'erreurs Arduino (erreur de parsing)
                        device_error_count['arduino'] += 1
                
                # Traiter les données CO2/temp/humidity uniquement si le mode est actif
                elif line.startswith('@') and measure_co2 and measure_co2_temp_humidity_active:
                    data = line[1:].split()
                    if len(data) == 3:
                        try:
                            co2 = float(data[0])
                            temperature = float(data[1])
                            humidity = float(data[2])
                            
                            # Only initialize start_time when we actually get data to plot
                            if measurements.start_time_co2_temp_humidity is None:
                                measurements.start_time_co2_temp_humidity = current_time
                            
                            # Calculate timestamp
                            timestamp = current_time - measurements.start_time_co2_temp_humidity - measurements.elapsed_time_co2_temp_humidity
                            
                            # Store data
                            measurements.timestamps_co2.append(timestamp)
                            measurements.values_co2.append(co2)
                            measurements.timestamps_temp.append(timestamp)
                            measurements.values_temp.append(temperature)
                            measurements.timestamps_humidity.append(timestamp)
                            measurements.values_humidity.append(humidity)
                            
                            # Update plot
                            plot_manager.update_co2_temp_humidity_plot(
                                measurements.timestamps_co2,
                                measurements.values_co2,
                                measurements.timestamps_temp,
                                measurements.values_temp,
                                measurements.timestamps_humidity,
                                measurements.values_humidity,
                                measurements.regeneration_timestamps
                            )
                        except ValueError:
                            print(f"Error parsing CO2/temp/humidity data: {line}")
                            # Incrémenter le compteur d'erreurs Arduino (erreur de parsing CO2/temp/humidity)
                            device_error_count['arduino'] += 1
        
        # Handle conductance measurements
        if measure_conductance and measure_conductance_active:
            try:
                # Synchroniser les références pour être sûr qu'ils partagent le même objet
                measurements.keithley = keithley
                
                # Vérifier d'abord que le Keithley est toujours connecté
                if keithley.device is None:
                    # Éviter les messages répétés
                    if not hasattr(add_keithley_device, 'disconnection_reported') or not add_keithley_device.disconnection_reported:
                        print("Le Keithley n'est plus disponible")
                        add_keithley_device.disconnection_reported = True
                    
                    device_error_count['keithley'] += 2
                    keithley_connected = False
                    
                    # Mettre à jour l'interface
                    plot_manager.update_add_device_buttons({'keithley': False})
                    
                    # Tenter une reconnexion automatique (nouvelle fonctionnalité)
                    current_time = time.time()
                    if scan_for_devices_interval > 0 and (current_time - last_device_scan_time) >= scan_for_devices_interval:
                        print("Tentative de reconnexion automatique du Keithley...")
                        last_device_scan_time = current_time
                        add_keithley_device(None)
                    
                    # Mettre automatiquement en pause la mesure de conductance
                    if measure_conductance_active:
                        print("Mise en pause automatique de la mesure de conductance")
                        
                        # Sauvegarder immédiatement les données de conductance
                        if measurements.timeList and len(measurements.timeList) > 0:
                            print("Sauvegarde immédiate des données de conductance suite à la déconnexion...")
                            try:
                                # S'assurer que le fichier est initialisé
                                if not conductance_file_initialized:
                                    data_handler.initialize_file("conductance")
                                    conductance_file_initialized = True
                                
                                # Sauvegarde
                                data_handler.save_conductance_data(
                                    measurements.timeList,
                                    measurements.conductanceList,
                                    measurements.resistanceList
                                )
                                print(f"✓ {len(measurements.timeList)} points de conductance sauvegardés")
                            except Exception as e:
                                print(f"Erreur lors de la sauvegarde des données de conductance: {e}")
                        
                        measure_conductance_active = False
                        # Mettre à jour l'interface
                        if 'conductance' in plot_manager.buttons:
                            plot_manager.buttons['conductance'].ax.set_facecolor('darkred')
                            plot_manager.buttons['conductance'].color = 'darkred'
                            plot_manager.buttons['conductance'].label.set_color('white')
                            plot_manager.fig.canvas.draw_idle()
                    
                    # Sauvegarde d'urgence seulement si pas de sauvegarde récente
                    current_time = time.time()
                    if (not hasattr(perform_emergency_backup, 'last_emergency_time') or 
                        current_time - perform_emergency_backup.last_emergency_time >= 60):
                        perform_emergency_backup("Déconnexion Keithley détectée")
                        # Mettre à jour le timestamp pour éviter les sauvegardes en rafale
                        perform_emergency_backup.last_emergency_time = current_time
                        
                    conductance_data = None
                else:
                    try:
                        conductance_data = measurements.read_conductance()
                        if conductance_data:
                            # Si la lecture réussit, réduire le compteur d'erreurs (mais pas en dessous de 0)
                            device_error_count['keithley'] = max(0, device_error_count['keithley'] - 1)
                    except pyvisa.errors.VisaIOError as visa_err:
                        print(f"Erreur critique VISA avec le Keithley: {visa_err}")
                        device_error_count['keithley'] += 2
                        # Tentative de fermeture et réinitialisation de l'appareil
                        try:
                            if keithley.device:
                                keithley.device.close()
                        except:
                            pass  # Ignorer les erreurs lors de la fermeture
                        keithley.device = None
                        keithley_connected = False
                        # Mettre à jour l'interface
                        plot_manager.update_add_device_buttons({'keithley': False})
                        
                        # Tenter une reconnexion automatique (nouvelle fonctionnalité)
                        current_time = time.time()
                        if scan_for_devices_interval > 0 and (current_time - last_device_scan_time) >= scan_for_devices_interval:
                            print("Tentative de reconnexion automatique du Keithley...")
                            last_device_scan_time = current_time
                            add_keithley_device(None)
                        
                        # Mettre automatiquement en pause la mesure de conductance
                        if measure_conductance_active:
                            print("Mise en pause automatique de la mesure de conductance")
                            
                            # Sauvegarder immédiatement les données de conductance
                            if measurements.timeList and len(measurements.timeList) > 0:
                                print("Sauvegarde immédiate des données de conductance suite à la déconnexion...")
                                try:
                                    # S'assurer que le fichier est initialisé
                                    if not conductance_file_initialized:
                                        data_handler.initialize_file("conductance")
                                        conductance_file_initialized = True
                                    
                                    # Sauvegarde
                                    data_handler.save_conductance_data(
                                        measurements.timeList,
                                        measurements.conductanceList,
                                        measurements.resistanceList
                                    )
                                    print(f"✓ {len(measurements.timeList)} points de conductance sauvegardés")
                                except Exception as e:
                                    print(f"Erreur lors de la sauvegarde des données de conductance: {e}")
                            
                            measure_conductance_active = False
                            # Mettre à jour l'interface
                            if 'conductance' in plot_manager.buttons:
                                plot_manager.buttons['conductance'].ax.set_facecolor('darkred')
                                plot_manager.buttons['conductance'].color = 'darkred'
                                plot_manager.buttons['conductance'].label.set_color('white')
                                plot_manager.fig.canvas.draw_idle()
                        
                        # Sauvegarde d'urgence seulement si pas de sauvegarde récente
                        current_time = time.time()
                        if (not hasattr(perform_emergency_backup, 'last_emergency_time') or 
                            current_time - perform_emergency_backup.last_emergency_time >= 60):
                            perform_emergency_backup("Déconnexion Keithley détectée")
                            # Mettre à jour le timestamp pour éviter les sauvegardes en rafale
                            perform_emergency_backup.last_emergency_time = current_time
                            
                        conductance_data = None
                    except Exception as e:
                        print(f"Error reading conductance data: {e}")
                        device_error_count['keithley'] += 1
                        conductance_data = None
            except Exception as e:
                print(f"Erreur générale lors de l'accès au Keithley: {e}")
                device_error_count['keithley'] += 1
                conductance_data = None
                
            if conductance_data:
                # Detect increase and stabilization
                increase_detected = measurements.detect_increase()
                stabilization_detected = measurements.detect_stabilization()
                
                # Vérifier si les indicateurs doivent être réinitialisés (conductance < 5 µS)
                # Cela ne réinitialise plus le temps de percolation, juste les indicateurs de détection
                indicators_reset = measurements.check_reset_detection_indicators()
                
                # Détecter la restabilisation post-régénération si nécessaire
                post_stability_detected = measurements.detect_post_regen_stability()
                
                # Update plots and indicators
                plot_manager.update_conductance_plot(
                    measurements.timeList,
                    measurements.conductanceList,
                    {
                        'increase_time': measurements.increase_time,
                        'stabilization_time': measurements.stabilization_time,
                        'max_slope_time': measurements.max_slope_time,
                        'conductance_decrease_time': measurements.conductance_decrease_time,
                        'post_regen_stability_time': measurements.post_regen_stability_time
                    }
                )
                
                # Mettre à jour l'indicateur du temps de percolation si une augmentation est détectée
                if increase_detected or measurements.increase_detected:
                    if 'percolation_time_display' in plot_manager.indicators and measurements.increase_time is not None:
                        ax_percolation_time = plot_manager.indicators['percolation_time_display']
                        ax_percolation_time.clear()
                        ax_percolation_time.text(0.5, 0.5, f"T perco: {measurements.increase_time:.1f} s", 
                                              ha="center", va="center", transform=ax_percolation_time.transAxes)
                        ax_percolation_time.axis('off')
                        # Redessiner pour mettre à jour l'indicateur
                        ax_percolation_time.figure.canvas.draw_idle()
                
                plot_manager.update_detection_indicators(
                    measurements.increase_detected,
                    measurements.stabilized
                )
        
        # Handle resistance temperature measurements
        if measure_regen and measure_res_temp_active:
            try:
                # Vérifier d'abord que l'appareil de régénération est toujours connecté
                if regen.device is None or not hasattr(regen.device, 'write') or not hasattr(regen.device, 'is_open') or not regen.device.is_open:
                    # Éviter les messages répétés
                    if not hasattr(add_regen_device, 'disconnection_reported') or not add_regen_device.disconnection_reported:
                        print("L'appareil de régénération n'est plus disponible")
                        add_regen_device.disconnection_reported = True
                    
                    device_error_count['regen'] += 2
                    regen_connected = False
                    
                    # Mettre à jour l'interface
                    plot_manager.update_add_device_buttons({'regen': False})
                    
                    # Mettre automatiquement en pause la mesure de température/résistance
                    if measure_res_temp_active:
                        print("Mise en pause automatique de la mesure de température/résistance")
                        
                        # Sauvegarder immédiatement les données de température/résistance
                        if measurements.timestamps_res_temp and len(measurements.timestamps_res_temp) > 0:
                            print("Sauvegarde immédiate des données de température/résistance suite à la déconnexion...")
                            try:
                                # S'assurer que le fichier est initialisé
                                if not temp_res_file_initialized:
                                    data_handler.initialize_file("temp_res")
                                    temp_res_file_initialized = True
                                
                                # Sauvegarde
                                data_handler.save_temp_res_data(
                                    measurements.timestamps_res_temp,
                                    measurements.temperatures,
                                    measurements.Tcons_values
                                )
                                print(f"✓ {len(measurements.timestamps_res_temp)} points de température/résistance sauvegardés")
                            except Exception as e:
                                print(f"Erreur lors de la sauvegarde des données de température/résistance: {e}")
                        
                        measure_res_temp_active = False
                        # Mettre à jour l'interface
                        if 'res_temp' in plot_manager.buttons:
                            plot_manager.buttons['res_temp'].ax.set_facecolor('darkred')
                            plot_manager.buttons['res_temp'].color = 'darkred'
                            plot_manager.buttons['res_temp'].label.set_color('white')
                            plot_manager.fig.canvas.draw_idle()
                    
                    # Sauvegarde d'urgence seulement si pas de sauvegarde récente
                    current_time = time.time()
                    if (not hasattr(perform_emergency_backup, 'last_emergency_time') or 
                        current_time - perform_emergency_backup.last_emergency_time >= 60):
                        perform_emergency_backup("Déconnexion carte de régénération détectée")
                        # Mettre à jour le timestamp pour éviter les sauvegardes en rafale
                        perform_emergency_backup.last_emergency_time = current_time
                    
                    temp_data = None
                    
                    # Tenter une reconnexion automatique (nouvelle fonctionnalité)
                    if scan_for_devices_interval > 0 and (current_time - last_device_scan_time) >= scan_for_devices_interval:
                        print("Tentative de reconnexion automatique de la carte de régénération...")
                        last_device_scan_time = current_time
                        
                        # Appeler directement - maintenant que nous savons ce qui cause le problème, 
                        # nous pouvons éviter le threading qui peut causer des problèmes
                        add_regen_device(None)
                else:
                    try:
                        temp_data = measurements.read_res_temp()
                        if temp_data:
                            # Si la lecture réussit, réduire le compteur d'erreurs (mais pas en dessous de 0)
                            device_error_count['regen'] = max(0, device_error_count['regen'] - 1)
                    except (serial.SerialException, IOError, OSError, PermissionError) as serial_err:
                        # Éviter les messages répétés
                        if not hasattr(add_regen_device, 'error_reported') or not add_regen_device.error_reported:
                            print(f"Erreur critique sur le port série de régénération: {serial_err}")
                            add_regen_device.error_reported = True
                            
                        device_error_count['regen'] += 2
                        # Tentative de fermeture et réinitialisation de l'appareil
                        try:
                            if regen.device:
                                if hasattr(regen.device, 'is_open') and regen.device.is_open:
                                    regen.device.close()
                        except:
                            pass  # Ignorer les erreurs lors de la fermeture
                        regen.device = None
                        regen_connected = False
                        # Mettre à jour l'interface
                        plot_manager.update_add_device_buttons({'regen': False})
                        
                        # Mettre automatiquement en pause la mesure de température/résistance
                        if measure_res_temp_active:
                            print("Mise en pause automatique de la mesure de température/résistance")
                            
                            # Sauvegarder immédiatement les données de température/résistance
                            if measurements.timestamps_res_temp and len(measurements.timestamps_res_temp) > 0:
                                print("Sauvegarde immédiate des données de température/résistance suite à la déconnexion...")
                                try:
                                    # S'assurer que le fichier est initialisé
                                    if not temp_res_file_initialized:
                                        data_handler.initialize_file("temp_res")
                                        temp_res_file_initialized = True
                                    
                                    # Sauvegarde
                                    data_handler.save_temp_res_data(
                                        measurements.timestamps_res_temp,
                                        measurements.temperatures,
                                        measurements.Tcons_values
                                    )
                                    print(f"✓ {len(measurements.timestamps_res_temp)} points de température/résistance sauvegardés")
                                except Exception as e:
                                    print(f"Erreur lors de la sauvegarde des données de température/résistance: {e}")
                            
                            measure_res_temp_active = False
                            # Mettre à jour l'interface
                            if 'res_temp' in plot_manager.buttons:
                                plot_manager.buttons['res_temp'].ax.set_facecolor('darkred')
                                plot_manager.buttons['res_temp'].color = 'darkred'
                                plot_manager.buttons['res_temp'].label.set_color('white')
                                plot_manager.fig.canvas.draw_idle()
                        
                        # Sauvegarde d'urgence seulement si pas de sauvegarde récente
                        current_time = time.time()
                        if (not hasattr(perform_emergency_backup, 'last_emergency_time') or 
                            current_time - perform_emergency_backup.last_emergency_time >= 60):
                            perform_emergency_backup("Déconnexion carte de régénération détectée")
                            # Mettre à jour le timestamp pour éviter les sauvegardes en rafale
                            perform_emergency_backup.last_emergency_time = current_time
                        
                        temp_data = None
                    except Exception as e:
                        print(f"Error reading temperature/resistance data: {e}")
                        device_error_count['regen'] += 1
                        temp_data = None
            except Exception as e:
                print(f"Erreur générale lors de l'accès à la carte de régénération: {e}")
                device_error_count['regen'] += 1
                temp_data = None
                
            if temp_data:
                plot_manager.update_res_temp_plot(
                    measurements.timestamps_res_temp,
                    measurements.temperatures,
                    measurements.Tcons_values,
                    measurements.regeneration_timestamps
                )
        
        # Handle regeneration protocol
        if measurements.regeneration_in_progress:
            try:
                regeneration_status = measurements.manage_regeneration_protocol()
                plot_manager.update_regeneration_status(regeneration_status, measurements.regeneration_results)
                
                # Force completion de protocole s'il atteint 100%
                if regeneration_status.get('progress', 0) >= 100:
                    print("CO2 protocol completed at 100%")
                    regeneration_status['active'] = False
                    measurements.regeneration_in_progress = False
                
                # Réactiver le bouton de protocole si terminé
                if not regeneration_status['active']:
                    # Re-enable both protocol buttons based on measurement conditions
                    plot_manager.update_protocol_button_states(
                        measure_co2_temp_humidity_active,
                        measure_conductance_active,
                        measure_res_temp_active
                    )
                    
                    # Hide the cancel button
                    if 'cancel_regeneration' in plot_manager.buttons:
                        cancel_button = plot_manager.buttons['cancel_regeneration']
                        cancel_button.ax.set_visible(False)
                        cancel_button.active = False
                        cancel_button.ax.figure.canvas.draw_idle()
                else:
                    # Show the cancel button during the protocol
                    if 'cancel_regeneration' in plot_manager.buttons:
                        cancel_button = plot_manager.buttons['cancel_regeneration']
                        if not cancel_button.ax.get_visible():
                            cancel_button.ax.set_visible(True)
                            cancel_button.active = True
                            cancel_button.ax.figure.canvas.draw_idle()
            except Exception as e:
                print(f"Error managing regeneration protocol: {e}")
                # Incrémenter les compteurs d'erreurs des deux appareils impliqués dans la régénération
                device_error_count['regen'] += 1
                device_error_count['arduino'] += 1
                
        # Handle conductance regeneration protocol
        if measurements.conductance_regen_in_progress:
            try:
                conductance_regen_status = measurements.manage_conductance_regen_protocol()
                plot_manager.update_regeneration_status(conductance_regen_status)
                
                # Force completion de protocole s'il atteint 100%
                if conductance_regen_status.get('progress', 0) >= 100:
                    print("Conductance protocol completed at 100%")
                    conductance_regen_status['active'] = False
                    measurements.conductance_regen_in_progress = False
                
                # Réactiver les boutons de protocole si terminé
                if not conductance_regen_status['active']:
                    # Re-enable protocol buttons based on measurement conditions
                    plot_manager.update_protocol_button_states(
                        measure_co2_temp_humidity_active,
                        measure_conductance_active,
                        measure_res_temp_active
                    )
                    
                    # Hide the cancel button
                    if 'cancel_regeneration' in plot_manager.buttons:
                        cancel_button = plot_manager.buttons['cancel_regeneration']
                        cancel_button.ax.set_visible(False)
                        cancel_button.active = False
                        cancel_button.ax.figure.canvas.draw_idle()
                else:
                    # Show the cancel button during the protocol
                    if 'cancel_regeneration' in plot_manager.buttons:
                        cancel_button = plot_manager.buttons['cancel_regeneration']
                        if not cancel_button.ax.get_visible():
                            cancel_button.ax.set_visible(True)
                            cancel_button.active = True
                            cancel_button.ax.figure.canvas.draw_idle()
            except Exception as e:
                print(f"Error managing conductance regeneration protocol: {e}")
                # Incrémenter les compteurs d'erreurs des deux appareils impliqués
                device_error_count['regen'] += 1
                device_error_count['keithley'] += 1
                
        # S'assurer que le bouton d'annulation est caché si aucun protocole n'est en cours
        if not measurements.regeneration_in_progress and not measurements.conductance_regen_in_progress:
            if 'cancel_regeneration' in plot_manager.buttons:
                cancel_button = plot_manager.buttons['cancel_regeneration']
                if cancel_button.ax.get_visible():
                    cancel_button.ax.set_visible(False)
                    cancel_button.active = False
                    cancel_button.ax.figure.canvas.draw_idle()
            
        # Vérifier si des erreurs d'appareils ont été détectées ou si l'intervalle de sauvegarde automatique est écoulé
        current_time = time.time()
        should_backup = False
        backup_reason = "sauvegarde périodique"
        
        # Limiter la fréquence des sauvegardes d'urgence pour éviter le flood
        min_time_between_emergency_backups = 60  # 60 secondes minimum entre deux sauvegardes d'urgence
        
        # Vérifier les erreurs d'appareils avec la nouvelle fonction de vérification
        error_info = check_device_errors()
        
        # Désactiver le mode d'urgence si les compteurs d'erreur sont bas 
        # et qu'au moins un appareil est connecté
        if emergency_mode and sum(device_error_count.values()) < 2 and (arduino_connected or regen_connected or keithley_connected):
            print("Mode d'urgence désactivé - connexion des appareils stabilisée")
            emergency_mode = False
        
        # Adapter l'intervalle de sauvegarde au mode d'urgence
        effective_interval = backup_interval / 2 if emergency_mode else backup_interval
        
        # Variables pour suivre la dernière sauvegarde d'urgence
        if not hasattr(perform_emergency_backup, 'last_emergency_time'):
            perform_emergency_backup.last_emergency_time = 0
            
        # Vérifier le temps écoulé depuis la dernière sauvegarde d'urgence
        time_since_last_emergency = current_time - perform_emergency_backup.last_emergency_time
        
        if error_info['critical'] and time_since_last_emergency >= min_time_between_emergency_backups:
            backup_reason = error_info['message']
            should_backup = True
            # Mettre à jour le timestamp de la dernière sauvegarde d'urgence
            perform_emergency_backup.last_emergency_time = current_time
            # Réinitialiser partiellement les compteurs d'erreurs après la sauvegarde
            # Ne pas les remettre complètement à zéro pour maintenir une certaine "mémoire" des problèmes
            device_error_count = {k: max(0, v - 2) for k, v in device_error_count.items()}
        
        # Sauvegarde périodique (seulement si des mesures sont actives)
        elif current_time - last_backup_time > effective_interval and (measure_conductance_active or measure_co2_temp_humidity_active or measure_res_temp_active):
            time_since_last = int(current_time - last_backup_time)
            backup_reason = f"sauvegarde automatique après {time_since_last} secondes"
            should_backup = True
            last_backup_time = current_time
        
        # Effectuer la sauvegarde si nécessaire
        if should_backup:
            backup_successful = perform_emergency_backup(backup_reason)
            
            # Mettre à jour l'indicateur de sauvegarde dans l'interface
            if hasattr(plot_manager, 'update_backup_status'):
                plot_manager.update_backup_status(last_backup_status)
            
            # Notification supprimée pour éviter d'interrompre l'utilisateur
            # Nous gardons uniquement la mise à jour de l'indicateur dans l'interface
            
        # Update UI - délai court pour une meilleure réactivité tout en donnant une chance au ramasse-miettes Python de libérer la mémoire
        plt.pause(0.01)
    
    # Cette section n'est exécutée que si le programme termine naturellement
    # sans passer par quit_program (ce qui est peu probable)
    if escape_pressed:
        print("Programme terminé via quit_program()")
    else:
        print("Programme terminé naturellement - sauvegarde des données")
        
        # Sauvegarder les données avant de fermer les connexions
        try:
            # Vérifier si des fichiers ont été initialisés (même si les mesures sont arrêtées)
            files_initialized = (
                data_handler.conductance_file is not None or
                data_handler.co2_temp_humidity_file is not None or
                data_handler.temp_res_file is not None
            )
            
            # Sauvegarder les données si elles sont en cours d'acquisition
            if measure_conductance_active and measurements.timeList and len(measurements.timeList) > 0:
                print("Sauvegarde des données de conductance avant fermeture...")
                sheet_name = f"Cond_{datetime.now().strftime('%H%M%S')}"
                data_handler.save_conductance_data(
                    measurements.timeList,
                    measurements.conductanceList,
                    measurements.resistanceList
                )
                
            if measure_co2_temp_humidity_active and ((measurements.timestamps_co2 and len(measurements.timestamps_co2) > 0) or \
               (measurements.timestamps_temp and len(measurements.timestamps_temp) > 0) or \
               (measurements.timestamps_humidity and len(measurements.timestamps_humidity) > 0)):
                print("Sauvegarde des données CO2/temp/humidity avant fermeture...")
                sheet_name = f"CO2_{datetime.now().strftime('%H%M%S')}"
                data_handler.save_co2_temp_humidity_data(
                    measurements.timestamps_co2,
                    measurements.values_co2,
                    measurements.timestamps_temp,
                    measurements.values_temp,
                    measurements.timestamps_humidity,
                    measurements.values_humidity
                )
                
            if measure_res_temp_active and measurements.timestamps_res_temp and len(measurements.timestamps_res_temp) > 0:
                print("Sauvegarde des données temp/resistance avant fermeture...")
                sheet_name = f"Temp_{datetime.now().strftime('%H%M%S')}"
                data_handler.save_temp_res_data(
                    measurements.timestamps_res_temp,
                    measurements.temperatures,
                    measurements.Tcons_values
                )
                
            # Forcer la création des feuilles cumulées pour tous les fichiers initialisés
            if data_handler.conductance_file and data_handler.conductance_series_count >= 2:
                print("Création de la feuille 'Essais cumulés' pour conductance...")
                data_handler._update_cumulative_sheet(data_handler.conductance_file)
                
            if data_handler.co2_temp_humidity_file and data_handler.co2_temp_humidity_series_count >= 2:
                print("Création de la feuille 'Essais cumulés' pour CO2/temp/humidity...")
                data_handler._update_cumulative_sheet(data_handler.co2_temp_humidity_file)
                
            if data_handler.temp_res_file and data_handler.temp_res_series_count >= 2:
                print("Création de la feuille 'Essais cumulés' pour temp/resistance...")
                data_handler._update_cumulative_sheet(data_handler.temp_res_file)
            
            # La création de graphiques dans les fichiers Excel est désactivée
            # Les graphiques peuvent être créés directement dans Excel après l'exportation
            
            # Proposer à l'utilisateur de renommer le dossier de données
            if files_initialized and hasattr(data_handler, 'test_folder_path') and data_handler.test_folder_path is not None:
                print(f"Les données ont été enregistrées dans: {data_handler.test_folder_path}")
                
                import tkinter as tk
                from tkinter import simpledialog
                
                root = tk.Tk()
                root.withdraw()  # Cacher la fenêtre principale
                root.attributes('-topmost', True)  # Mettre au premier plan
                
                # Obtenir le nom initial du dossier
                initial_folder_name = os.path.basename(data_handler.test_folder_path)
                
                # Afficher la boîte de dialogue pour le nouveau nom
                new_folder_name = simpledialog.askstring(
                    "Renommer le dossier de données", 
                    "Voulez-vous renommer le dossier de données ? (Laissez vide pour conserver le nom actuel)",
                    initialvalue=initial_folder_name,
                    parent=root  # Utiliser root comme parent pour hériter du topmost
                )
                
                # Si l'utilisateur a fourni un nom différent, renommer le dossier
                if new_folder_name and new_folder_name.strip() and new_folder_name.strip() != initial_folder_name:
                    data_handler.rename_test_folder(new_folder_name.strip())
                    print(f"Dossier renommé en: {new_folder_name.strip()}")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des données: {e}")
            
        # Close all connections if they haven't been closed yet
        if keithley is not None and hasattr(keithley, 'device') and keithley.device is not None:
            keithley.close()
        if arduino_connected and hasattr(arduino, 'device') and arduino.device is not None:
            arduino.close()
        if regen_connected and hasattr(regen, 'device') and regen.device is not None:
            regen.close()
    
    # Nettoyer les ressources matplotlib et mémoire
    # Ceci est exécuté dans tous les cas pour assurer un nettoyage complet
    
    # Fermer proprement les threads matplotlib en arrière-plan
    import matplotlib
    matplotlib.pyplot.close('all')
    
    # Fermer explicitement le plot_manager si ce n'est pas déjà fait
    if plot_manager is not None and plot_manager.fig is not None:
        plt.close(plot_manager.fig)
    
    # Fermer toutes les références pour libérer la mémoire
    plot_manager = None
    
    # Forcer le ramasse-miettes Python
    import gc
    gc.collect()
    
    # Terminer proprement le programme
    sys.exit(0)

if __name__ == "__main__":
    main()