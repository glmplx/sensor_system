#!/usr/bin/env python
"""
Manual mode application for the sensor system
"""

import sys
import time
import os
import signal
import threading
import matplotlib.pyplot as plt

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
    
    # Désactiver le bouton de régénération initialement - sera activé uniquement quand
    # les mesures CO2 et Tcons/Tmes seront activées simultanément
    if 'regeneration' in plot_manager.buttons:
        regeneration_button = plot_manager.buttons['regeneration']
        regeneration_button.ax.set_facecolor('lightgray')
        regeneration_button.color = 'lightgray'
        regeneration_button.label.set_color('black')
        regeneration_button.active = False
    
    # Initialize R0 display
    R0 = measurements.read_R0()
    if R0 is not None:
        plot_manager.update_R0_display(R0)
    
    # Define event handlers
    def toggle_conductance(event):
        nonlocal measure_conductance_active, conductance_file_initialized
        previous_state = measure_conductance_active
        measure_conductance_active = not measure_conductance_active
        
        # Si on initialise la mesure pour la première fois
        if measure_conductance_active and not conductance_file_initialized:
            data_handler.initialize_file("conductance")
            conductance_file_initialized = True
            
        # Si on met en pause (passage de True à False)
        if previous_state and not measure_conductance_active:
            # Enregistrer le temps d'arrêt pour plus tard
            current_time = time.time()
            if measurements.start_time_conductance is not None:
                measurements.pause_time_conductance = current_time
        
        # Si on reprend après pause (passage de False à True)
        if not previous_state and measure_conductance_active and measurements.pause_time_conductance is not None:
            # Calculer combien de temps s'est écoulé depuis la pause
            current_time = time.time()
            pause_duration = current_time - measurements.pause_time_conductance
            # Ajouter cette durée au temps d'offset pour ajuster les timestamps
            measurements.elapsed_time_conductance += pause_duration
            
        # Update UI
        plot_manager.update_raz_buttons_visibility({'conductance': measure_conductance_active})
    
    def toggle_co2_temp_humidity(event):
        nonlocal measure_co2_temp_humidity_active, co2_temp_humidity_file_initialized
        previous_state = measure_co2_temp_humidity_active
        measure_co2_temp_humidity_active = not measure_co2_temp_humidity_active
        
        # Si on initialise la mesure pour la première fois
        if measure_co2_temp_humidity_active and not co2_temp_humidity_file_initialized:
            data_handler.initialize_file("co2_temp_humidity")
            co2_temp_humidity_file_initialized = True
            
        # Si on met en pause (passage de True à False)
        if previous_state and not measure_co2_temp_humidity_active:
            # Enregistrer le temps d'arrêt pour plus tard
            current_time = time.time()
            if measurements.start_time_co2_temp_humidity is not None:
                measurements.pause_time_co2_temp_humidity = current_time
        
        # Si on reprend après pause (passage de False à True)
        if not previous_state and measure_co2_temp_humidity_active and measurements.pause_time_co2_temp_humidity is not None:
            # Calculer combien de temps s'est écoulé depuis la pause
            current_time = time.time()
            pause_duration = current_time - measurements.pause_time_co2_temp_humidity
            # Ajouter cette durée au temps d'offset pour ajuster les timestamps
            measurements.elapsed_time_co2_temp_humidity += pause_duration
            
        # Update UI
        plot_manager.update_raz_buttons_visibility({'co2_temp_humidity': measure_co2_temp_humidity_active})
        
        # Vérifier si le bouton de régénération doit être activé (CO2 et Tcons/Tmes actifs)
        update_regeneration_button_state()
    
    def toggle_res_temp(event):
        nonlocal measure_res_temp_active, temp_res_file_initialized
        previous_state = measure_res_temp_active
        measure_res_temp_active = not measure_res_temp_active
        
        # Si on initialise la mesure pour la première fois
        if measure_res_temp_active and not temp_res_file_initialized:
            data_handler.initialize_file("temp_res")
            temp_res_file_initialized = True
            
        # Si on met en pause (passage de True à False)
        if previous_state and not measure_res_temp_active:
            # Enregistrer le temps d'arrêt pour plus tard
            current_time = time.time()
            if measurements.start_time_res_temp is not None:
                measurements.pause_time_res_temp = current_time
        
        # Si on reprend après pause (passage de False à True)
        if not previous_state and measure_res_temp_active and measurements.pause_time_res_temp is not None:
            # Calculer combien de temps s'est écoulé depuis la pause
            current_time = time.time()
            pause_duration = current_time - measurements.pause_time_res_temp
            # Ajouter cette durée au temps d'offset pour ajuster les timestamps
            measurements.elapsed_time_res_temp += pause_duration
            
        # Update UI
        plot_manager.update_raz_buttons_visibility({'res_temp': measure_res_temp_active})
        
        # Vérifier si le bouton de régénération doit être activé (CO2 et Tcons/Tmes actifs)
        update_regeneration_button_state()
        
    def update_regeneration_button_state():
        """Met à jour l'état du bouton de régénération en fonction des mesures actives"""
        # Le bouton de régénération ne doit être actif que si CO2 et Tcons/Tmes sont actifs
        if 'regeneration' in plot_manager.buttons:
            regeneration_button = plot_manager.buttons['regeneration']
            
            # Si les deux mesures sont actives et qu'on n'est pas déjà en régénération
            if measure_co2_temp_humidity_active and measure_res_temp_active and not measurements.regeneration_in_progress:
                # Activer le bouton
                regeneration_button.ax.set_facecolor('firebrick')
                regeneration_button.color = 'firebrick'
                regeneration_button.label.set_color('white')
                regeneration_button.active = True
            else:
                # Désactiver le bouton si les conditions ne sont pas réunies 
                # et qu'on n'est pas déjà en régénération
                if not measurements.regeneration_in_progress:
                    regeneration_button.ax.set_facecolor('lightgray')
                    regeneration_button.color = 'lightgray'
                    regeneration_button.label.set_color('black')
                    regeneration_button.active = False
            
            # Forcer la mise à jour du canvas
            regeneration_button.ax.figure.canvas.draw_idle()
    
    def raz_conductance(event):
        data_handler.save_conductance_data(
            measurements.timeList,
            measurements.conductanceList,
            measurements.resistanceList
        )
        
        measurements.reset_data("conductance")
        measurements.reset_data("detection")
        
        plot_manager.update_conductance_plot([], [])
        plot_manager.update_detection_indicators(False, False)
    
    def raz_co2_temp_humidity(event):
        data_handler.save_co2_temp_humidity_data(
            measurements.timestamps_co2,
            measurements.values_co2,
            measurements.timestamps_temp,
            measurements.values_temp,
            measurements.timestamps_humidity,
            measurements.values_humidity
        )
        
        measurements.reset_data("co2_temp_humidity")
        
        plot_manager.update_co2_temp_humidity_plot([], [], [], [], [], [])
    
    def raz_res_temp(event):
        data_handler.save_temp_res_data(
            measurements.timestamps_res_temp,
            measurements.temperatures,
            measurements.Tcons_values
        )
        
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
                # Button will be reactivated when regeneration completes
    
    def cancel_regeneration(event):
        """Handle regeneration cancel button click"""
        # Only do something if button is active and visible
        if hasattr(plot_manager.buttons['cancel_regeneration'], 'active') and plot_manager.buttons['cancel_regeneration'].active:
            # Cancel regeneration protocol
            success = measurements.cancel_regeneration_protocol()
            if success:
                # Update button state
                plot_manager.update_regeneration_status({
                    'active': False,
                    'step': 0,
                    'message': "Regeneration cancelled",
                    'progress': 0
                })
            
    def quit_program(event):
        nonlocal escape_pressed
        # Définir Tcons à 0°C avant de fermer
        from core.constants import TCONS_LOW
        measurements.set_Tcons(str(TCONS_LOW))
        print(f"Tcons défini à {TCONS_LOW}°C avant fermeture")
        escape_pressed = True
        
        # Fermer immédiatement, sans attendre la fin de la boucle principale
        # Close all connections
        if keithley is not None:
            keithley.close()
        if arduino_connected:
            arduino.close()
        if regen_connected:
            regen.close()
        
        # Fermeture de tous les graphiques
        plot_manager.close()
        
        # Forcer la fermeture de toutes les figures matplotlib
        plt.ioff()
        plt.close('all')
        
        # Terminer l'exécution immédiatement
        import sys
        sys.exit(0)
    
    # Connect event handlers
    plot_manager.connect_button('conductance', toggle_conductance)
    plot_manager.connect_button('co2_temp_humidity', toggle_co2_temp_humidity)
    plot_manager.connect_button('res_temp', toggle_res_temp)
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
    plot_manager.connect_button('quit', quit_program)
    
    # Connect radiobutton for time unit selection
    plot_manager.connect_radiobutton('time_unit', plot_manager.on_time_unit_change)
    
    # Main loop
    while not escape_pressed:
        current_time = time.time()
        
        # Lire toutes les données disponibles du port série
        # Vérifier si données disponibles et les traiter en fonction du mode actif
        for _ in range(10):  # Lire jusqu'à 10 lignes par itération pour vider le buffer
            line = None
            if arduino.device and hasattr(arduino.device, 'in_waiting') and arduino.device.in_waiting > 0:
                try:
                    line = arduino.device.readline().decode('utf-8', errors='ignore').strip()
                except Exception as e:
                    print(f"Error reading from Arduino: {e}")
            
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
        
        # Handle conductance measurements
        if measure_conductance and measure_conductance_active:
            conductance_data = measurements.read_conductance()
            if conductance_data:
                # Detect increase and stabilization
                measurements.detect_increase()
                measurements.detect_stabilization()
                
                # Vérifier si les indicateurs doivent être réinitialisés (conductance < 5 µS)
                indicators_reset = measurements.check_reset_detection_indicators()
                
                # Update plots and indicators
                plot_manager.update_conductance_plot(
                    measurements.timeList,
                    measurements.conductanceList,
                    {
                        'increase_time': measurements.increase_time,
                        'stabilization_time': measurements.stabilization_time,
                        'max_slope_time': measurements.max_slope_time
                    }
                )
                
                plot_manager.update_detection_indicators(
                    measurements.increase_detected,
                    measurements.stabilized
                )
        
        # Handle resistance temperature measurements
        if measure_regen and measure_res_temp_active:
            temp_data = measurements.read_res_temp()
            if temp_data:
                plot_manager.update_res_temp_plot(
                    measurements.timestamps_res_temp,
                    measurements.temperatures,
                    measurements.Tcons_values,
                    measurements.regeneration_timestamps
                )
        
        # Handle regeneration protocol
        if measurements.regeneration_in_progress:
            regeneration_status = measurements.manage_regeneration_protocol()
            plot_manager.update_regeneration_status(regeneration_status, measurements.regeneration_results)
            
        # Update UI - délai court pour une meilleure réactivité tout en donnant une chance au ramasse-miettes Python de libérer la mémoire
        plt.pause(0.01)
    
    # Save data before exiting - only for active measurements
    if measure_conductance or measure_co2 or measure_regen:
        data_handler.save_all_data(measurements)
        
        # Proposer à l'utilisateur de renommer le dossier de données
        import tkinter as tk
        from tkinter import simpledialog
        
        root = tk.Tk()
        root.withdraw()  # Cacher la fenêtre principale
        
        # Vérifier si le chemin du dossier de test existe avant de l'utiliser
        initial_folder_name = ""
        if hasattr(data_handler, 'test_folder_path') and data_handler.test_folder_path is not None:
            initial_folder_name = os.path.basename(data_handler.test_folder_path)
        
        # Afficher la boîte de dialogue pour le nouveau nom
        new_folder_name = simpledialog.askstring(
            "Renommer le dossier de données", 
            "Voulez-vous renommer le dossier de données ? (Laissez vide pour conserver le nom actuel)",
            initialvalue=initial_folder_name
        )
        
        # Si l'utilisateur a fourni un nom et que le dossier test existe, renommer le dossier
        if new_folder_name and new_folder_name.strip() and hasattr(data_handler, 'test_folder_path') and data_handler.test_folder_path is not None:
            if new_folder_name.strip() != initial_folder_name:
                data_handler.rename_test_folder(new_folder_name.strip())
                print(f"Dossier renommé en: {new_folder_name.strip()}")
    
    # Close all connections
    if keithley is not None:
        keithley.close()
    if arduino_connected:
        arduino.close()
    if regen_connected:
        regen.close()
    
    # Forcer la fermeture de toutes les figures matplotlib
    plt.ioff()
    plt.close('all')
    
    # Fermer explicitement le plot_manager
    if plot_manager.fig is not None:
        plt.close(plot_manager.fig)
    plot_manager.fig = None
    
    # Fermer proprement les threads matplotlib en arrière-plan
    # Utilisation de sys.exit() au lieu de os.kill qui est incorrect pour les threads Python
    import matplotlib
    matplotlib.pyplot.close('all')
    
    # Fermer toutes les références aux traceurs pour libérer la mémoire
    plot_manager = None
    
    # Forcer le ramasse-miettes Python pour libérer la mémoire
    import gc
    gc.collect()
    
    # Terminer proprement le programme
    sys.exit(0)

if __name__ == "__main__":
    main()