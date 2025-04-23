#!/usr/bin/env python
"""
Application en mode automatique pour le système de capteurs
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
from core.constants import TCONS_LOW
from data_handlers.excel_handler import ExcelHandler
from ui.plot_manager import PlotManager
from utils.helpers import parse_pin_states

def main(arduino_port=None, arduino_baud_rate=None, other_port=None, other_baud_rate=None):
    """Point d'entrée principal pour l'application en mode automatique"""
    
    # If parameters aren't provided, try to get them from command line
    if arduino_port is None:
        # Check arguments
        if len(sys.argv) != 5:
            print("Usage: python auto_app.py <arduino_port> <arduino_baud_rate> <other_port> <other_baud_rate>")
            sys.exit(1)
        
        # Parse arguments
        arduino_port = sys.argv[1]
        arduino_baud_rate = int(sys.argv[2])
        other_port = sys.argv[3]
        other_baud_rate = int(sys.argv[4])
    
    # Initialize devices
    keithley = KeithleyDevice()
    arduino = ArduinoDevice(port=arduino_port, baud_rate=arduino_baud_rate)
    regen = RegenDevice(port=other_port, baud_rate=other_baud_rate)
    
    # Connect to devices
    if not keithley.connect():
        print("Failed to connect to Keithley device")
        sys.exit(1)
    
    if not arduino.connect():
        print("Failed to connect to Arduino device")
        keithley.close()
        sys.exit(1)
    
    if not regen.connect():
        print("Failed to connect to regeneration device")
        keithley.close()
        arduino.close()
        sys.exit(1)
    
    # Initialize measurement manager
    measurements = MeasurementManager(keithley, arduino, regen)
    
    # Initialize data handler
    data_handler = ExcelHandler(mode="auto")
    
    # Initialize plots
    plot_manager = PlotManager(mode="auto")
    
    # Initialize variables for UI state
    measure_auto = False
    escape_pressed = False
    
    # Initialize R0 display
    R0 = measurements.read_R0()
    if R0 is not None:
        plot_manager.update_R0_display(R0)
    
    # En mode auto, le bouton de régénération ne doit être actif que lorsque les mesures sont activées
    if 'regeneration' in plot_manager.buttons:
        regeneration_button = plot_manager.buttons['regeneration']
        regeneration_button.ax.set_facecolor('lightgray')
        regeneration_button.color = 'lightgray'
        regeneration_button.label.set_color('black')
        regeneration_button.active = False
    
    # Define event handlers
    def toggle_auto(event):
        nonlocal measure_auto
        previous_state = measure_auto
        measure_auto = not measure_auto
        
        if measure_auto:
            # Initialize files if needed
            data_handler.initialize_file("conductance")
            data_handler.initialize_file("co2_temp_humidity")
            data_handler.initialize_file("temp_res")
            
            # Start measurements
            keithley.turn_output_on()
            print("Automatic measurements started")
            
            # Si on reprend après pause (passage de False à True)
            if not previous_state and measurements.pause_time_conductance is not None:
                # Calculer combien de temps s'est écoulé depuis la pause
                current_time = time.time()
                pause_duration = current_time - measurements.pause_time_conductance
                # Ajouter cette durée aux temps d'offset pour ajuster les timestamps
                measurements.elapsed_time_conductance += pause_duration
                measurements.elapsed_time_co2_temp_humidity += pause_duration
                measurements.elapsed_time_res_temp += pause_duration
                print(f"Reprise des mesures après {pause_duration:.2f}s de pause")
                
            # Activer le bouton de régénération si les mesures auto sont actives
            if 'regeneration' in plot_manager.buttons and not measurements.regeneration_in_progress:
                regeneration_button = plot_manager.buttons['regeneration']
                regeneration_button.ax.set_facecolor('firebrick')
                regeneration_button.color = 'firebrick'
                regeneration_button.label.set_color('white')
                regeneration_button.active = True
                regeneration_button.ax.figure.canvas.draw_idle()
        else:
            # Stop measurements
            keithley.turn_output_off()
            print("Automatic measurements stopped")
            
            # Si on met en pause (passage de True à False)
            if previous_state:
                # Enregistrer le temps d'arrêt pour plus tard
                current_time = time.time()
                measurements.pause_time_conductance = current_time
                measurements.pause_time_co2_temp_humidity = current_time
                measurements.pause_time_res_temp = current_time
                
            # Désactiver le bouton de régénération si les mesures auto sont arrêtées
            if 'regeneration' in plot_manager.buttons and not measurements.regeneration_in_progress:
                regeneration_button = plot_manager.buttons['regeneration']
                regeneration_button.ax.set_facecolor('lightgray')
                regeneration_button.color = 'lightgray'
                regeneration_button.label.set_color('black')
                regeneration_button.active = False
                regeneration_button.ax.figure.canvas.draw_idle()
        
        # Update UI
        plot_manager.update_raz_buttons_visibility({'auto': measure_auto})
    
    def raz_auto(event):
        # Save current data before reset
        data_handler.save_conductance_data(
            measurements.timeList,
            measurements.conductanceList,
            measurements.resistanceList
        )
        
        data_handler.save_co2_temp_humidity_data(
            measurements.timestamps_co2,
            measurements.values_co2,
            measurements.timestamps_temp,
            measurements.values_temp,
            measurements.timestamps_humidity,
            measurements.values_humidity
        )
        
        data_handler.save_temp_res_data(
            measurements.timestamps_res_temp,
            measurements.temperatures,
            measurements.Tcons_values
        )
        
        # Reset all data
        measurements.reset_data()
        
        # Reset plots
        plot_manager.update_conductance_plot([], [])
        plot_manager.update_co2_temp_humidity_plot([], [], [], [], [], [])
        plot_manager.update_res_temp_plot([], [], [])
        
        # Reset detection indicators
        plot_manager.update_detection_indicators(False, False)
    
    def set_R0(event):
        value = plot_manager.textboxes['R0'].text
        measurements.set_R0(value)
    
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
        measurements.set_Tcons(str(TCONS_LOW))
        print(f"Tcons défini à {TCONS_LOW}°C avant fermeture")
        escape_pressed = True
        plot_manager.close()
    
    # Connect event handlers
    plot_manager.connect_button('auto', toggle_auto)
    plot_manager.connect_button('raz_auto', raz_auto)
    plot_manager.connect_button('set_R0', set_R0)
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
    last_conductance_time = 0
    last_temp_data_time = 0
    measurement_cycle = 0  # Pour alterner entre les différentes mesures
    
    while not escape_pressed:
        current_time = time.time()
        
        # Lire l'état des capteurs (indépendamment du mode de mesure)
        # Pour que les voyants soient mis à jour en continu
        if not measure_auto:  # Seulement quand le mode auto n'est pas actif
            # Fonction pour traiter les états des pins et mettre à jour l'UI
            def process_pin_states(line):
                pin_states = parse_pin_states(line)
                if pin_states:
                    # Stocker les états des pins pour la mise à jour de l'UI
                    measurements.pin_states = pin_states
                    # Mettre à jour les indicateurs LED si les états des pins ont changé
                    plot_manager.update_sensor_indicators(measurements.pin_states)
                    return True
                return False
            
            # Lire jusqu'à 3 lignes en mode non-auto
            for _ in range(3):
                if not arduino.device or not hasattr(arduino.device, 'in_waiting') or arduino.device.in_waiting <= 0:
                    break  # Aucune donnée disponible
                    
                line = arduino.device.readline().decode('utf-8', errors='ignore').strip()
                if not line:
                    continue
                
                # Traiter uniquement les messages d'état des pins
                process_pin_states(line)
                
                # En mode non-auto, on ignore les données CO2/temp/humidity
        
        if measure_auto:
            # Rotation des mesures pour éviter de surcharger l'appareil
            measurement_cycle = (measurement_cycle + 1) % 10
            
            # Lire toutes les données disponibles du port série (à chaque cycle)
            # Vérifier si données disponibles et les traiter en fonction du mode actif
            for _ in range(10):  # Lire jusqu'à 10 lignes par itération pour vider le buffer
                if not arduino.device or not hasattr(arduino.device, 'in_waiting') or arduino.device.in_waiting <= 0:
                    break  # Aucune donnée disponible, sortir de la boucle
                
                line = arduino.device.readline().decode('utf-8', errors='ignore').strip()
                if not line:
                    continue
                
                # Traiter les états des pins (pour les voyants) en utilisant la fonction définie précédemment
                if process_pin_states(line):
                    continue
                
                # Traiter les données CO2/temp/humidity
                elif line.startswith('@'):
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
            
            # Lecture du Keithley (conductance) tous les 5 cycles avec un délai minimum de 1 seconde
            if measurement_cycle % 5 == 0 and current_time - last_conductance_time >= 1:
                conductance_data = measurements.read_conductance()
                if conductance_data:
                    last_conductance_time = current_time
                    plot_manager.update_conductance_plot(
                        measurements.timeList,
                        measurements.conductanceList,
                        {
                            'increase_time': measurements.increase_time,
                            'stabilization_time': measurements.stabilization_time,
                            'max_slope_time': measurements.max_slope_time
                        }
                    )
            
            # Lecture de la température tous les 3 cycles avec un délai minimum de 1 seconde
            elif measurement_cycle % 3 == 0 and current_time - last_temp_data_time >= 1:
                temp_data = measurements.read_res_temp()
                if temp_data:
                    last_temp_data_time = current_time
                    plot_manager.update_res_temp_plot(
                        measurements.timestamps_res_temp,
                        measurements.temperatures,
                        measurements.Tcons_values,
                        measurements.regeneration_timestamps
                    )
            
            # Exécuter l'automate de détection à chaque itération, mais après avoir lu les données
            if measurement_cycle % 10 == 0:
                measurements.automatic_mode_handler()
                
                # Update detection indicators
                plot_manager.update_detection_indicators(
                    measurements.increase_detected,
                    measurements.stabilized
                )
                
            # Gérer le protocole de régénération si actif
            if measurements.regeneration_in_progress:
                regeneration_status = measurements.manage_regeneration_protocol()
                plot_manager.update_regeneration_status(regeneration_status, measurements.regeneration_results)
        
        # Update UI - délai court pour une meilleure réactivité
        plt.pause(0.01)
    
    # Save data before exiting
    data_handler.save_all_data(measurements)
    
    # Proposer à l'utilisateur de renommer le dossier de données
    import tkinter as tk
    from tkinter import simpledialog
    
    root = tk.Tk()
    root.withdraw()  # Cacher la fenêtre principale
    
    # Afficher la boîte de dialogue pour le nouveau nom
    new_folder_name = simpledialog.askstring(
        "Renommer le dossier de données", 
        "Voulez-vous renommer le dossier de données ? (Laissez vide pour conserver le nom actuel)",
        initialvalue=os.path.basename(data_handler.test_folder_path)
    )
    
    # Si l'utilisateur a fourni un nom, renommer le dossier
    if new_folder_name and new_folder_name.strip() and new_folder_name != os.path.basename(data_handler.test_folder_path):
        data_handler.rename_test_folder(new_folder_name.strip())
        print(f"Dossier renommé en: {new_folder_name.strip()}")
    else:
        # Afficher le chemin où les données ont été enregistrées
        if data_handler.test_folder_path:
            print(f"Les données ont été enregistrées dans: {data_handler.test_folder_path}")
    
    # Close all connections
    keithley.close()
    arduino.close()
    regen.close()
    
    # Forcer la fermeture de toutes les figures matplotlib
    plt.ioff()
    plt.close('all')
    
    # Fermer explicitement le plot_manager
    if plot_manager.fig is not None:
        plt.close(plot_manager.fig)
    plot_manager.fig = None
    
    # Tuer tous les threads matplotlib en arrière-plan
    for thread in sys._current_frames().keys():
        try:
            if thread != threading.current_thread().ident:
                os.kill(thread, signal.SIGTERM)
        except:
            pass
            
    # Forcer la sortie immédiate en tuant le processus actuel
    pid = os.getpid()
    os.kill(pid, signal.SIGTERM)

if __name__ == "__main__":
    main()