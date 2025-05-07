#!/usr/bin/env python
"""
Application en mode automatique pour le système de capteurs

Ce module gère l'application en mode automatique qui permet la détection et la mesure
automatisée de conductance avec régénération automatique du capteur.
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
    """
    Point d'entrée principal pour l'application en mode automatique
    
    Cette fonction initialise les appareils, configure l'interface graphique et exécute
    la boucle principale qui gère la détection de conductance et la régénération automatiques.
    
    Args:
        arduino_port: Port COM de l'Arduino (CO2, température, humidité)
        arduino_baud_rate: Débit en bauds pour la communication avec l'Arduino
        other_port: Port COM de la carte de régénération
        other_baud_rate: Débit en bauds pour la communication avec la carte de régénération
    """
    
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
    
    # Fonction pour gérer l'événement de fermeture de la fenêtre par le bouton X
    def handle_window_close(event=None):
        """
        Gère l'événement de fermeture de la fenêtre par le bouton X
        
        Args:
            event: Événement de fermeture de la fenêtre
        """
        nonlocal escape_pressed
        if not escape_pressed:  # Éviter une double fermeture
            # Appeler la même fonction que le bouton Quitter
            quit_program(event)
        
    # Enregistrer le gestionnaire de fermeture
    plot_manager.set_close_callback(handle_window_close)
    
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
    
    # Définir les gestionnaires d'événements
    def toggle_auto(event):
        """
        Active ou désactive les mesures automatiques
        
        Cette fonction gère l'activation/désactivation des mesures automatiques,
        incluant l'initialisation des fichiers, l'activation du Keithley et la 
        gestion des temps de pause pour maintenir des timestamps cohérents.
        
        Args:
            event: Événement déclencheur (clic sur le bouton)
        """
        nonlocal measure_auto
        previous_state = measure_auto
        measure_auto = not measure_auto
        
        if measure_auto:
            # Initialiser les fichiers si nécessaire
            data_handler.initialize_file("conductance")
            data_handler.initialize_file("co2_temp_humidity")
            data_handler.initialize_file("temp_res")
            
            # Démarrer les mesures
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
            # Arrêter les mesures
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
        
        # Mettre à jour l'interface utilisateur
        plot_manager.update_raz_buttons_visibility({'auto': measure_auto})
    
    def raz_auto(event):
        """
        Réinitialise les données de mesure en mode automatique
        
        Cette fonction sauvegarde d'abord les données actuelles dans les fichiers Excel,
        puis réinitialise les données de mesure et les graphiques. Elle conserve l'historique
        des données déjà enregistrées.
        
        Args:
            event: Événement déclencheur (clic sur le bouton)
        """
        # Sauvegarder les données actuelles avant réinitialisation
        # Sauvegarder les données de conductance
        if len(measurements.timeList) > 0:
            data_handler.save_conductance_data(
                measurements.timeList,
                measurements.conductanceList,
                measurements.resistanceList
            )
            # Ne pas réinitialiser les données accumulées pour garder l'historique
            # Les temps sont ajustés automatiquement dans save_conductance_data
        
        # Sauvegarder les données de CO2/température/humidité
        if len(measurements.timestamps_co2) > 0 or len(measurements.timestamps_temp) > 0 or len(measurements.timestamps_humidity) > 0:
            data_handler.save_co2_temp_humidity_data(
                measurements.timestamps_co2,
                measurements.values_co2,
                measurements.timestamps_temp,
                measurements.values_temp,
                measurements.timestamps_humidity,
                measurements.values_humidity
            )
            # Ne pas réinitialiser les données accumulées pour garder l'historique
            # Les temps sont ajustés automatiquement dans save_co2_temp_humidity_data
        
        # Sauvegarder les données de température/résistance
        if len(measurements.timestamps_res_temp) > 0:
            data_handler.save_temp_res_data(
                measurements.timestamps_res_temp,
                measurements.temperatures,
                measurements.Tcons_values
            )
            # Ne pas réinitialiser les données accumulées pour garder l'historique
            # Les temps sont ajustés automatiquement dans save_temp_res_data
        
        # Réinitialiser toutes les données
        measurements.reset_data()
        
        # Réinitialiser les graphiques
        plot_manager.update_conductance_plot([], [])
        plot_manager.update_co2_temp_humidity_plot([], [], [], [], [], [])
        plot_manager.update_res_temp_plot([], [], [])
        
        # Réinitialiser les indicateurs de détection
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
        """
        Gère le clic sur le bouton de régénération
        
        Cette fonction démarre le protocole de régénération du capteur qui implique
        le chauffage du capteur pour éliminer les molécules adsorbées.
        
        Args:
            event: Événement déclencheur (clic sur le bouton)
        """
        # Agir uniquement si le bouton est actif (pas déjà en régénération)
        if hasattr(plot_manager.buttons['regeneration'], 'active') and plot_manager.buttons['regeneration'].active:
            # Démarrer le protocole de régénération
            success = measurements.start_regeneration_protocol()
            if success:
                # Mettre à jour l'état du bouton
                plot_manager.update_regeneration_status({
                    'active': True,
                    'step': 1,
                    'message': "Démarrage du protocole de régénération",
                    'progress': 0
                })
                # Le bouton sera réactivé lorsque la régénération sera terminée
    
    def cancel_regeneration(event):
        """
        Gère le clic sur le bouton d'annulation de régénération
        
        Cette fonction annule le protocole de régénération en cours et
        ramène le système à son état normal.
        
        Args:
            event: Événement déclencheur (clic sur le bouton)
        """
        # Agir uniquement si le bouton est actif et visible
        if hasattr(plot_manager.buttons['cancel_regeneration'], 'active') and plot_manager.buttons['cancel_regeneration'].active:
            # Annuler le protocole de régénération
            success = measurements.cancel_regeneration_protocol()
            if success:
                # Mettre à jour l'état du bouton
                plot_manager.update_regeneration_status({
                    'active': False,
                    'step': 0,
                    'message': "Régénération annulée",
                    'progress': 0
                })
    
    def quit_program(event):
        """
        Gère la fermeture propre du programme
        
        Cette fonction sauvegarde les données, propose de renommer le dossier de données,
        réinitialise la température consigne, ferme les connexions avec les appareils et
        nettoie les ressources graphiques avant de quitter le programme.
        
        Args:
            event: Événement déclencheur (clic sur le bouton ou fermeture de fenêtre)
        """
        nonlocal escape_pressed
        # Définir Tcons à 0°C avant de fermer
        try:
            measurements.set_Tcons(str(TCONS_LOW))
            print(f"Tcons défini à {TCONS_LOW}°C avant fermeture")
        except Exception as e:
            print(f"Erreur lors de la définition de Tcons: {e}")
        
        # Désactiver le flag de fonctionnement
        escape_pressed = True
        
        # Sauvegarder les données immédiatement avant de fermer les connexions
        try:
            # Vérifier si des fichiers ont été initialisés (même si les mesures sont arrêtées)
            files_initialized = (
                data_handler.conductance_file is not None or
                data_handler.co2_temp_humidity_file is not None or
                data_handler.temp_res_file is not None
            )
            
            if measure_auto:
                print("Sauvegarde des données...")
                saved = data_handler.save_all_data(measurements)
            else:
                saved = False
                if files_initialized:
                    print("Mesures automatiques arrêtées - aucune sauvegarde supplémentaire nécessaire")
            
            # Proposer à l'utilisateur de renommer le dossier de données si des fichiers ont été initialisés
            if files_initialized and hasattr(data_handler, 'test_folder_path') and data_handler.test_folder_path is not None:
                if saved:
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
                print("Mode auto inactif - aucune donnée à sauvegarder")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des données: {e}")

        # Fermer toutes les connexions
        print("Fermeture des connexions...")
        try:
            keithley.close()
            arduino.close()
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
                """
                Traite les informations d'état des pins et met à jour l'interface
                
                Cette fonction analyse les états des pins (capteurs de position) depuis
                une ligne de données Arduino et met à jour les indicateurs visuels correspondants.
                
                Args:
                    line: Ligne de texte contenant les informations d'état des pins
                    
                Returns:
                    bool: True si des états de pins ont été traités, False sinon
                """
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
                    
                    # Détecter les éléments du cycle de conductance
                    measurements.detect_increase()
                    measurements.detect_stabilization()
                    measurements.check_reset_detection_indicators()
                    measurements.detect_post_regen_stability()
                    
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
        # Utiliser un délai court pour la réactivité de l'UI mais donner une chance au ramasse-miettes Python de libérer la mémoire
    plt.pause(0.01)
    
    # Cette section n'est exécutée que si le programme termine naturellement
    # sans passer par quit_program (ce qui est peu probable)
    if escape_pressed:
        print("Programme terminé via quit_program()")
    else:
        print("Programme terminé naturellement - sauvegarde des données")
        # Save data before exiting
        data_handler.save_all_data(measurements)
        
        # Vérifier que le dossier de données existe
        if hasattr(data_handler, 'test_folder_path') and data_handler.test_folder_path is not None:
            print(f"Les données ont été enregistrées dans: {data_handler.test_folder_path}")
            
            # Proposer à l'utilisateur de renommer le dossier de données
            import tkinter as tk
            from tkinter import simpledialog
            
            root = tk.Tk()
            root.withdraw()  # Cacher la fenêtre principale
            
            # Obtenir le nom initial du dossier
            initial_folder_name = os.path.basename(data_handler.test_folder_path)
            
            # Afficher la boîte de dialogue pour le nouveau nom
            new_folder_name = simpledialog.askstring(
                "Renommer le dossier de données", 
                "Voulez-vous renommer le dossier de données ? (Laissez vide pour conserver le nom actuel)",
                initialvalue=initial_folder_name
            )
            
            # Si l'utilisateur a fourni un nom différent, renommer le dossier
            if new_folder_name and new_folder_name.strip() and new_folder_name.strip() != initial_folder_name:
                data_handler.rename_test_folder(new_folder_name.strip())
                print(f"Dossier renommé en: {new_folder_name.strip()}")
        
        # Close all connections if they haven't been closed yet
        if hasattr(keithley, 'device') and keithley.device is not None:
            keithley.close()
        if hasattr(arduino, 'device') and arduino.device is not None:
            arduino.close()
        if hasattr(regen, 'device') and regen.device is not None:
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