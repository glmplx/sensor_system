"""
Interface utilisateur du menu pour le système de capteurs
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import serial.tools.list_ports
import os
import sys
import importlib
import inspect
from core.constants import (
    EXCEL_BASE_DIR,
    # Constantes de conductance
    STABILITY_DURATION, INCREASE_SLOPE_MIN, INCREASE_SLOPE_MAX,
    DECREASE_SLOPE_THRESHOLD, SLIDING_WINDOW, R0_THRESHOLD,
    REGENERATION_TEMP, TCONS_LOW, VALVE_DELAY, CONDUCTANCE_DECREASE_THRESHOLD,
    # Constantes de CO2
    CO2_STABILITY_THRESHOLD, CO2_STABILITY_DURATION, REGENERATION_DURATION,
    CELL_VOLUME, CO2_INCREASE_THRESHOLD,
    # Constantes Keithley
    KEITHLEY_POLARIZATION_VOLTAGE
)

class MenuUI:
    """Interface utilisateur du menu principal pour le système de capteurs"""
    
    def __init__(self):
        """Initialiser l'interface utilisateur du menu"""
        self.window = tk.Tk()
        self.window.title("Système de capteurs - Interface de sélection")
        self.window.geometry("500x650")
        
        # Variables
        self.arduino_com_var = tk.StringVar()
        self.other_com_var = tk.StringVar()
        self.arduino_baud_rate_var = tk.IntVar(value=115200)
        self.other_baud_rate_var = tk.IntVar(value=230400)
        self.mode_manual_var = tk.IntVar(value=1)  # Présélection du mode manuel
        self.mode_auto_var = tk.IntVar()

        # Measurement selection variables (for manual mode)
        self.measure_conductance_var = tk.IntVar(value=0)  # Conductance désactivée par défaut
        self.measure_co2_var = tk.IntVar(value=1)
        self.measure_regen_var = tk.IntVar(value=1)

        # Options générales
        self.auto_save_var = tk.IntVar(value=1)  # Sauvegardes automatiques - activé par défaut
        self.save_data_var = tk.IntVar(value=1)  # Enregistrement des données - activé par défaut
        self.custom_save_location_var = tk.IntVar(value=0)  # Emplacement personnalisé - désactivé par défaut
        
        # Set up UI elements
        self.setup_ui()
        
        # Initialiser le mode manuel dès le démarrage
        self.set_manual_mode()
    
    def scan_ports(self):
        """
        Analyse les ports COM disponibles et identifie les types d'appareils
        
        Returns:
            tuple: (ports_info, ports_display, arduino_port_index, regen_port_index)
                - ports_info: Liste de tuples (port.device, port.description)
                - ports_display: Liste des ports formatés pour l'affichage
                - arduino_port_index: Index du port Arduino détecté ou None
                - regen_port_index: Index du port de régénération détecté ou None
        """
        # Récupérer les ports disponibles
        ports = serial.tools.list_ports.comports()
        ports_info = [(port.device, port.description) for port in ports]
        ports_display = [f"{port[0]} - {port[1]}" for port in ports_info]
        
        # Pré-sélection des ports selon leur description
        arduino_port_index = None
        regen_port_index = None
        
        for i, (_, description) in enumerate(ports_info):
            # Cherche Arduino ou UNO dans les descriptions pour le port Arduino
            if "Arduino" in description or "UNO" in description:
                arduino_port_index = i
            # Cherche "USB Serial Port" dans les descriptions pour le port de régénération
            elif "USB Serial Port" in description:
                regen_port_index = i
        
        return ports_info, ports_display, arduino_port_index, regen_port_index
    
    def refresh_ports(self, show_message=True):
        """
        Actualiser la liste des ports COM disponibles
        
        Args:
            show_message: Afficher un message de confirmation après l'actualisation
        
        Returns:
            dict: Informations sur les ports détectés (pour usage externe)
        """
        # Sauvegarder les valeurs actuelles
        old_arduino_com = self.arduino_com_var.get()
        old_other_com = self.other_com_var.get()
        
        # Récupérer les ports et détecter les appareils
        ports_info, ports_display, arduino_port_index, regen_port_index = self.scan_ports()
        
        # Mettre à jour les menus déroulants
        # Pour Arduino
        self.arduino_com_dropdown['menu'].delete(0, 'end')
        
        if ports_display:
            for port in ports_display:
                self.arduino_com_dropdown['menu'].add_command(label=port, command=lambda p=port: self.arduino_com_var.set(p))
            
            # Essayer de conserver la sélection précédente
            if old_arduino_com in ports_display:
                self.arduino_com_var.set(old_arduino_com)
            elif arduino_port_index is not None:
                self.arduino_com_var.set(ports_display[arduino_port_index])
                # Préselectionner CO2/température/humidité si Arduino détecté
                self.measure_co2_var.set(1)
            else:
                self.arduino_com_var.set("")
                # Désactiver CO2/température/humidité si Arduino non détecté
                self.measure_co2_var.set(0)
        else:
            self.arduino_com_dropdown['menu'].add_command(label="Aucun port détecté", command=lambda: self.arduino_com_var.set("Aucun port détecté"))
            self.arduino_com_var.set("Aucun port détecté")
            self.measure_co2_var.set(0)
        
        # Pour la carte de régénération
        self.other_com_dropdown['menu'].delete(0, 'end')
        
        if ports_display:
            for port in ports_display:
                self.other_com_dropdown['menu'].add_command(label=port, command=lambda p=port: self.other_com_var.set(p))
            
            # Essayer de conserver la sélection précédente
            if old_other_com in ports_display:
                self.other_com_var.set(old_other_com)
            elif regen_port_index is not None:
                self.other_com_var.set(ports_display[regen_port_index])
                # Préselectionner régénération/température si carte régénération détectée
                self.measure_regen_var.set(1)
            else:
                self.other_com_var.set("")
                # Désactiver régénération/température si carte non détectée
                self.measure_regen_var.set(0)
        else:
            self.other_com_dropdown['menu'].add_command(label="Aucun port détecté", command=lambda: self.other_com_var.set("Aucun port détecté"))
            self.other_com_var.set("Aucun port détecté")
            self.measure_regen_var.set(0)
        
        # Afficher un message de confirmation si demandé
        if show_message:
            tk.messagebox.showinfo("Actualisation", "Liste des ports COM actualisée.")
        
        # Retourner les informations sur les ports pour usage externe
        return {
            'ports_info': ports_info,
            'ports_display': ports_display,
            'arduino_port_index': arduino_port_index,
            'regen_port_index': regen_port_index
        }
    
    def setup_ui(self):
        """Configurer les éléments de l'interface utilisateur"""
        # Initialiser avec le scan des ports
        ports_info, ports_display, arduino_port_index, regen_port_index = self.scan_ports()
        
        # Arduino port selection
        tk.Label(self.window, text="Port COM de l'Arduino:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        
        # Handle case when no ports are detected
        if ports_display:
            self.arduino_com_dropdown = tk.OptionMenu(self.window, self.arduino_com_var, *ports_display)
        else:
            # Create dummy option menu with empty list to avoid error
            self.arduino_com_var.set("Aucun port détecté")
            self.arduino_com_dropdown = tk.OptionMenu(self.window, self.arduino_com_var, "Aucun port détecté")
        self.arduino_com_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky='w')
        
        # Pré-sélectionner le port Arduino s'il a été détecté
        arduino_detected = arduino_port_index is not None
        if arduino_detected:
            self.arduino_com_var.set(ports_display[arduino_port_index])
            # Préselectionner CO2/température/humidité si Arduino détecté
            self.measure_co2_var.set(1)
        else:
            # Désactiver CO2/température/humidité si Arduino non détecté
            self.measure_co2_var.set(0)
        
        # Arduino baud rate
        tk.Label(self.window, text="Baudrate de l'Arduino:").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        arduino_baud_rate_entry = tk.Entry(self.window, textvariable=self.arduino_baud_rate_var)
        arduino_baud_rate_entry.grid(row=1, column=1, padx=10, pady=10, sticky='w')
        
        # Regeneration card port selection
        tk.Label(self.window, text="Port COM de la carte pour la régénération:").grid(row=2, column=0, padx=10, pady=10, sticky='w')
        # Handle case when no ports are detected
        if ports_display:
            self.other_com_dropdown = tk.OptionMenu(self.window, self.other_com_var, *ports_display)
        else:
            # Create dummy option menu with empty list to avoid error
            self.other_com_var.set("Aucun port détecté")
            self.other_com_dropdown = tk.OptionMenu(self.window, self.other_com_var, "Aucun port détecté")
        self.other_com_dropdown.grid(row=2, column=1, padx=10, pady=10, sticky='w')
        
        # Pré-sélectionner le port Serial s'il a été détecté
        regen_detected = regen_port_index is not None
        if regen_detected:
            self.other_com_var.set(ports_display[regen_port_index])
            # Préselectionner régénération/température si carte régénération détectée
            self.measure_regen_var.set(1)
        else:
            # Désactiver régénération/température si carte non détectée
            self.measure_regen_var.set(0)
        
        # Regeneration card baud rate
        tk.Label(self.window, text="Baudrate de la carte pour la régénération:").grid(row=3, column=0, padx=10, pady=10, sticky='w')
        other_baud_rate_entry = tk.Entry(self.window, textvariable=self.other_baud_rate_var)
        other_baud_rate_entry.grid(row=3, column=1, padx=10, pady=10, sticky='w')
        
        # Mode selection checkboxes
        manual_check = tk.Checkbutton(self.window, text="Mode Manuel", variable=self.mode_manual_var, command=self.set_manual_mode)
        manual_check.grid(row=4, column=0, padx=10, pady=10)
        
        auto_check = tk.Checkbutton(self.window, text="Mode Automatique", variable=self.mode_auto_var, command=self.set_auto_mode)
        auto_check.grid(row=4, column=1, padx=10, pady=10)
        
        # Measurement selection frame (only visible when manual mode is selected)
        self.measurement_frame = tk.LabelFrame(self.window, text="Sélection des mesures (Mode Manuel)")
        self.measurement_frame.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky='ew')
        self.measurement_frame.grid_remove()  # Initially hidden

        # Measurement options
        tk.Checkbutton(self.measurement_frame, text="Conductance", variable=self.measure_conductance_var).grid(row=0, column=0, sticky='w', padx=10, pady=5)
        tk.Checkbutton(self.measurement_frame, text="CO2 / Température / Humidité", variable=self.measure_co2_var).grid(row=1, column=0, sticky='w', padx=10, pady=5)
        tk.Checkbutton(self.measurement_frame, text="Régénération / Température", variable=self.measure_regen_var).grid(row=2, column=0, sticky='w', padx=10, pady=5)

        # Options frame pour les paramètres généraux
        options_frame = tk.LabelFrame(self.window, text="Options générales")
        options_frame.grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky='ew')

        # Options de sauvegarde
        autosave_check = tk.Checkbutton(options_frame, text="Activer les sauvegardes automatiques", variable=self.auto_save_var)
        autosave_check.grid(row=0, column=0, sticky='w', padx=10, pady=5)

        savedata_check = tk.Checkbutton(options_frame, text="Enregistrer les données des mesures", variable=self.save_data_var)
        savedata_check.grid(row=1, column=0, sticky='w', padx=10, pady=5)

        # Variable pour stocker le chemin de sauvegarde personnalisé
        self.save_location_path = tk.StringVar(value=EXCEL_BASE_DIR)

        # Fonction pour afficher/masquer le sélecteur d'emplacement
        def toggle_location_selector(*args):
            if self.custom_save_location_var.get():
                location_entry.grid(row=3, column=0, columnspan=1, sticky='ew', padx=10, pady=2)
                browse_button.grid(row=3, column=1, sticky='w', padx=0, pady=2)
            else:
                location_entry.grid_remove()
                browse_button.grid_remove()

        # Fonction pour ouvrir le sélecteur de dossier
        def browse_directory():
            directory = filedialog.askdirectory(initialdir=self.save_location_path.get())
            if directory:  # Si l'utilisateur a sélectionné un dossier
                self.save_location_path.set(directory)

        custom_location_check = tk.Checkbutton(options_frame, text="Choisir l'emplacement d'enregistrement",
                                              variable=self.custom_save_location_var, command=toggle_location_selector)
        custom_location_check.grid(row=2, column=0, sticky='w', padx=10, pady=5)

        # Champ de texte pour afficher le chemin d'enregistrement
        location_entry = tk.Entry(options_frame, textvariable=self.save_location_path, width=30)

        # Bouton pour parcourir les dossiers
        browse_button = tk.Button(options_frame, text="Parcourir...", command=browse_directory)

        # Initialiser l'état de visibilité du sélecteur en fonction de l'état de la case à cocher
        toggle_location_selector()
        
        # Button frame to hold refresh, launch and quit buttons
        button_frame = tk.Frame(self.window)
        button_frame.grid(row=7, column=0, columnspan=2, pady=20)

        # Refresh ports button
        refresh_button = tk.Button(button_frame, text="Actualiser les ports", command=self.refresh_ports)
        refresh_button.pack(side=tk.LEFT, padx=10)

        # Configuration button for changing protocol constants
        config_button = tk.Button(button_frame, text="Paramètres", command=self.open_config_window)
        config_button.pack(side=tk.LEFT, padx=10)

        # Launch button
        launch_button = tk.Button(button_frame, text="Lancer le programme", command=self.launch_program)
        launch_button.pack(side=tk.LEFT, padx=10)

        # Help button
        help_button = tk.Button(button_frame, text="Aide", command=self.open_documentation)
        help_button.pack(side=tk.LEFT, padx=10)

        # Quit button
        quit_button = tk.Button(button_frame, text="Quitter", command=self.quit_application)
        quit_button.pack(side=tk.LEFT, padx=10)
    
    def set_manual_mode(self):
        """Définir le mode manuel et décocher le mode automatique"""
        if self.mode_manual_var.get():
            self.mode_auto_var.set(0)
            self.measurement_frame.grid()  # Show measurement selection
        else:
            self.measurement_frame.grid_remove()  # Hide measurement selection
    
    def set_auto_mode(self):
        """Définir le mode automatique et décocher le mode manuel"""
        self.mode_manual_var.set(0)
        self.measurement_frame.grid_remove()  # Hide measurement selection
    
    def check_port_selections(self, arduino_port_str, other_port_str):
        """
        Vérifie que les ports sélectionnés correspondent aux bonnes cartes
        
        Args:
            arduino_port_str: chaîne du port Arduino sélectionné
            other_port_str: chaîne du port de régénération sélectionné
            
        Returns:
            bool: True si les sélections sont valides ou si l'utilisateur confirme
            str: "swap" si l'utilisateur choisit d'échanger les ports
        """
        # Détecter une possible inversion de ports
        arduino_appears_as_regen = arduino_port_str and "USB Serial Port" in arduino_port_str and ("Arduino" not in arduino_port_str and "UNO" not in arduino_port_str)
        regen_appears_as_arduino = other_port_str and ("Arduino" in other_port_str or "UNO" in other_port_str)
        
        # Si les deux ports semblent inversés
        if arduino_appears_as_regen and regen_appears_as_arduino:
            message = "Les ports semblent être inversés :\n\n"
            message += "- Le port Arduino contient 'USB Serial Port', qui correspond généralement à la carte de régénération\n"
            message += "- Le port de régénération contient 'Arduino' ou 'UNO', qui correspond généralement à l'Arduino\n\n"
            message += "Souhaitez-vous échanger les ports?"
            
            if tk.messagebox.askyesno("Ports inversés", message):
                # Échanger les ports
                self.arduino_com_var.set(other_port_str)
                self.other_com_var.set(arduino_port_str)
                return "swap"
            else:
                # L'utilisateur ne veut pas échanger, demander s'il veut continuer quand même
                if tk.messagebox.askyesno("Confirmation", "Voulez-vous continuer avec cette configuration de ports?"):
                    return True
                else:
                    return False
        
        # Si seulement un port semble mal configuré
        warnings = []
        
        # Vérifier si le port Arduino semble être un port de type USB Serial Port
        if arduino_appears_as_regen:
            warnings.append("Le port sélectionné pour l'Arduino semble être un port USB Serial Port, ce qui correspond généralement à la carte de régénération.")
            warnings.append("C'est probablement un mauvais choix de port pour l'Arduino.")
        
        # Vérifier si le port de régénération semble être un port Arduino
        if regen_appears_as_arduino:
            warnings.append("Le port sélectionné pour la carte de régénération semble être un port Arduino.")
            warnings.append("C'est probablement un mauvais choix de port pour la carte de régénération.")
        
        # Si des avertissements sont présents, demander confirmation à l'utilisateur
        if warnings:
            warning_message = "\n\n".join(warnings) + "\n\nVoulez-vous échanger les ports?"
            
            if tk.messagebox.askyesno("Avertissement - Mauvais ports", warning_message):
                # Échanger les ports
                temp = self.arduino_com_var.get()
                self.arduino_com_var.set(self.other_com_var.get())
                self.other_com_var.set(temp)
                return "swap"
            elif tk.messagebox.askyesno("Confirmation", "Voulez-vous continuer avec cette configuration de ports?"):
                return True
            else:
                return False
        
        return True
    
    def launch_program(self):
        """Lancer le mode de programme sélectionné"""
        if not self.mode_manual_var.get() and not self.mode_auto_var.get():
            return  # Do nothing if no mode is selected
        
        # Get measurement selections (only relevant for manual mode)
        measure_conductance = self.measure_conductance_var.get() if self.mode_manual_var.get() else 1
        measure_co2 = self.measure_co2_var.get() if self.mode_manual_var.get() else 1
        measure_regen = self.measure_regen_var.get() if self.mode_manual_var.get() else 1
        
        # Vérifier qu'au moins une mesure est sélectionnée en mode manuel
        if self.mode_manual_var.get() and not any([measure_conductance, measure_co2, measure_regen]):
            tk.messagebox.showerror("Error", "Veuillez sélectionner au moins un type de mesure à effectuer")
            return
        
        # Valeurs par défaut pour les ports
        arduino_port = "NONE"
        arduino_baud_rate = 9600
        other_port = "NONE"
        other_baud_rate = 9600
        
        arduino_port_str = self.arduino_com_var.get()
        other_port_str = self.other_com_var.get()
        
        # Vérification du port Arduino (nécessaire pour CO2 uniquement)
        # La conductance a besoin du Keithley, pas de l'Arduino
        if measure_co2 or self.mode_auto_var.get():
            try:
                if not arduino_port_str:
                    tk.messagebox.showerror("Error", "Veuillez sélectionner un port COM pour l'Arduino (nécessaire pour mesures de CO2)")
                    return
                arduino_port = arduino_port_str.split()[0]  # Extract only the COM port
                arduino_baud_rate = self.arduino_baud_rate_var.get()
            except (IndexError, AttributeError):
                tk.messagebox.showerror("Error", "Veuillez sélectionner un port COM valide pour l'Arduino")
                return
                
        # Vérification du port de régénération (nécessaire uniquement si mesure_regen ou mode auto)
        if measure_regen or self.mode_auto_var.get():
            try:
                if not other_port_str:
                    tk.messagebox.showerror("Error", "Veuillez sélectionner un port COM pour la carte de régénération")
                    return
                other_port = other_port_str.split()[0]  # Extract only the COM port
                other_baud_rate = self.other_baud_rate_var.get()
            except (IndexError, AttributeError):
                tk.messagebox.showerror("Error", "Veuillez sélectionner un port COM valide pour la carte de régénération")
                return
        
        # Vérifier que les ports sélectionnés semblent corrects
        if (measure_co2 or measure_regen or self.mode_auto_var.get()):
            check_result = self.check_port_selections(arduino_port_str, other_port_str)
            if check_result == "swap":
                # Si les ports ont été échangés, mettre à jour les variables
                arduino_port_str = self.arduino_com_var.get()
                other_port_str = self.other_com_var.get()
                
                # Mettre à jour les ports et baud rates
                try:
                    arduino_port = arduino_port_str.split()[0]  # Extract only the COM port
                    other_port = other_port_str.split()[0]  # Extract only the COM port
                except (IndexError, AttributeError):
                    tk.messagebox.showerror("Error", "Problème lors de l'échange des ports")
                    return
            elif not check_result:
                return
                
        # Vérifier si l'utilisateur a sélectionné des ports sans sélectionner les mesures correspondantes
        if self.mode_manual_var.get():
            warnings = []
            if not measure_co2 and arduino_port_str:
                warnings.append("Vous avez sélectionné un port Arduino mais aucune mesure de CO2")
            
            if not measure_regen and other_port_str:
                warnings.append("Vous avez sélectionné un port de régénération mais aucune mesure ne l'utilisant")
                
            if warnings:
                warning_message = "\n\n".join(warnings) + "\n\nVoulez-vous continuer quand même?"
                if not tk.messagebox.askyesno("Avertissement", warning_message):
                    return
        
        # Close the current window
        self.window.destroy()
        
        # Get options state
        auto_save = bool(self.auto_save_var.get())
        save_data = bool(self.save_data_var.get())
        custom_save_location = bool(self.custom_save_location_var.get())

        # Récupérer le chemin de sauvegarde personnalisé si activé
        save_location = self.save_location_path.get() if custom_save_location else EXCEL_BASE_DIR

        # Import and run directly instead of launching a new process
        if getattr(sys, 'frozen', False):
            # Running as executable
            if self.mode_auto_var.get():
                # Import auto app dynamically
                import auto_app
                auto_app.main(
                    arduino_port,
                    arduino_baud_rate,
                    other_port,
                    other_baud_rate,
                    auto_save=auto_save,
                    save_data=save_data,
                    custom_save_location=custom_save_location,
                    save_location=save_location
                )
            else:
                # Import manual app dynamically
                import manual_app
                manual_app.main(
                    arduino_port,
                    arduino_baud_rate,
                    other_port,
                    other_baud_rate,
                    measure_conductance=measure_conductance,
                    measure_co2=measure_co2,
                    measure_regen=measure_regen,
                    auto_save=auto_save,
                    save_data=save_data,
                    custom_save_location=custom_save_location,
                    save_location=save_location
                )
        else:
            # Running as script
            if self.mode_auto_var.get():
                # Auto mode
                script_name = "auto_app.py"
                script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), script_name)
                # Préparer les arguments de base
                command = [
                    sys.executable, script_path,
                    arduino_port, str(arduino_baud_rate),
                    other_port, str(other_baud_rate),
                    "--auto_save", str(int(auto_save)),
                    "--save_data", str(int(save_data)),
                    "--custom_save_location", str(int(custom_save_location))
                ]

                # Ajouter le chemin de sauvegarde seulement si demandé
                if custom_save_location and save_location:
                    command.extend(["--save_location", save_location])
                    print(f"Setting custom save location: {save_location}")
            else:
                # Manual mode with measurement selections
                script_name = "manual_app.py"
                script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), script_name)
                command = [
                    sys.executable, script_path,
                    arduino_port, str(arduino_baud_rate),
                    other_port, str(other_baud_rate),
                    "--measure_conductance", str(measure_conductance),
                    "--measure_co2", str(measure_co2),
                    "--measure_regen", str(measure_regen),
                    "--auto_save", str(int(auto_save)),
                    "--save_data", str(int(save_data)),
                    "--custom_save_location", str(int(custom_save_location))
                ]

                # Ajouter le chemin de sauvegarde seulement si demandé
                if custom_save_location and save_location:
                    command.extend(["--save_location", save_location])
                    print(f"Setting custom save location: {save_location}")
            
            # Utiliser execv pour remplacer le processus actuel (pas de sous-processus)
            os.execv(sys.executable, command)
    
    def open_documentation(self):
        """Lance mkdocs serve et ouvre la documentation dans un navigateur"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        mkdocs_path = os.path.join(base_dir, "mkdocs.yml")

        if not os.path.exists(mkdocs_path):
            tk.messagebox.showerror("Erreur", "Fichier mkdocs.yml non trouvé. Veuillez exécuter mkdocs_script.py d'abord.")
            return

        # Essayer de lancer mkdocs serve
        try:
            import threading
            import webbrowser
            import time

            # Variable pour communiquer entre les threads
            server_ready = threading.Event()

            # Fonction pour lancer mkdocs serve dans un thread séparé
            def run_mkdocs_server():
                os.chdir(base_dir)  # Changer le répertoire de travail
                try:
                    # Lancer mkdocs serve
                    process = subprocess.Popen(
                        ["mkdocs", "serve"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True,
                        shell=sys.platform.startswith('win')
                    )

                    print("Serveur MkDocs en cours de démarrage...")

                    # Lire la sortie pour les messages d'erreur ou le port
                    for line in process.stdout:
                        print(line.strip())
                        # Si la ligne contient "Documentation built" ou "Serving on", le serveur est prêt
                        if "Documentation built" in line or "Serving on" in line:
                            server_ready.set()
                            break
                except Exception as e:
                    print(f"Erreur lors du lancement de mkdocs serve: {e}")
                    server_ready.set()  # Signaler même en cas d'erreur pour ne pas bloquer le thread principal

            # Lancer le serveur dans un thread séparé
            server_thread = threading.Thread(target=run_mkdocs_server, daemon=True)
            server_thread.start()

            # Attendre jusqu'à 5 secondes maximum pour que le serveur soit prêt
            is_ready = server_ready.wait(timeout=1.0)
            if not is_ready:
                print("Avertissement: Serveur MkDocs n'a pas encore signalé sa disponibilité. Poursuite quand même...")

            # Ouvrir l'URL dans le navigateur
            def open_browser():
                url = "http://127.0.0.1:8000/"  # URL par défaut pour mkdocs serve
                webbrowser.open(url)
                print(f"Documentation ouverte dans le navigateur: {url}")

            # Exécuter l'action dans le thread principal
            self.window.after(100, open_browser)

            tk.messagebox.showinfo(
                "Documentation",
                "Le serveur MkDocs a été démarré sur le port 8000.\n"
                "La documentation a été ouverte dans votre navigateur.\n\n"
                "Note: Le serveur s'arrêtera automatiquement à la fermeture de l'application."
            )

        except Exception as e:
            # Si mkdocs ne fonctionne pas, essayer d'ouvrir le fichier directement
            print(f"Erreur avec mkdocs serve: {e}")
            doc_path = os.path.join(base_dir, "docs", "index.md")

            try:
                # Utiliser la commande appropriée selon le système d'exploitation
                if sys.platform.startswith('win'):
                    os.startfile(doc_path)
                elif sys.platform.startswith('darwin'):  # macOS
                    subprocess.call(['open', doc_path])
                else:  # linux
                    subprocess.call(['xdg-open', doc_path])

                # Plus besoin d'ouvrir Google dans un autre onglet

                tk.messagebox.showinfo(
                    "Documentation",
                    "La commande mkdocs serve a échoué.\nLes fichiers de documentation ont été ouverts directement.\n"
                    "Pour une meilleure expérience, installez MkDocs: pip install mkdocs mkdocs-material"
                )
            except Exception as e2:
                tk.messagebox.showerror(
                    "Erreur",
                    f"Impossible d'ouvrir la documentation: {str(e)}\n{str(e2)}\n\n"
                    f"Vous pouvez lancer manuellement: mkdocs serve\n"
                    f"Puis ouvrir http://127.0.0.1:8000/ dans votre navigateur."
                )

    def open_config_window(self):
        """Ouvre la fenêtre de configuration des constantes"""
        # Créer et afficher la fenêtre de configuration
        config_window = ConstantsConfigWindow(self)

        # Rendre la fenêtre modale (bloque l'interaction avec la fenêtre parent)
        self.window.wait_window(config_window.window)
    
    def quit_application(self):
        """Ferme l'application proprement et termine le processus"""
        self.window.destroy()
        import sys
        sys.exit(0)

    def run(self):
        """Exécuter la boucle principale de l'interface utilisateur"""
        self.window.mainloop()


class ConstantsConfigWindow:
    """Fenêtre de configuration des constantes pour les protocoles"""

    def __init__(self, parent):
        """
        Initialise la fenêtre de configuration des constantes

        Args:
            parent: Fenêtre parente (MenuUI) qui a créé cette fenêtre
        """
        self.parent = parent

        # Créer une nouvelle fenêtre
        self.window = tk.Toplevel(parent.window)
        self.window.title("Configuration des paramètres de protocole")
        self.window.geometry("600x700")
        self.window.resizable(True, True)
        self.window.transient(parent.window)  # Cette fenêtre dépend de la fenêtre parent
        self.window.grab_set()  # Bloque les interactions avec la fenêtre parent

        # Dictionnaire pour stocker les entrées utilisateur
        self.entries = {}

        # Initialiser l'interface
        self.setup_ui()

    def setup_ui(self):
        """Configurer l'interface utilisateur"""
        # Zone de défilement pour contenir tous les paramètres
        main_frame = tk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=1, padx=10, pady=10)

        # Créer un canvas pour permettre le défilement
        canvas = tk.Canvas(main_frame)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        # Ajouter une barre de défilement
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configurer le canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Créer un frame à l'intérieur du canvas
        content_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=content_frame, anchor="nw")

        # Section des constantes de conductance
        conductance_frame = ttk.LabelFrame(content_frame, text="Paramètres de détection de conductance")
        conductance_frame.pack(fill=tk.X, expand=1, padx=5, pady=5)

        conductance_params = [
            ("STABILITY_DURATION", "Durée de stabilité (s)", STABILITY_DURATION, "Durée requise en secondes pour considérer la conductance comme stable"),
            ("INCREASE_SLOPE_MIN", "Pente min. augmentation (µS/s)", INCREASE_SLOPE_MIN, "Seuil minimum pour la pente d'augmentation de conductance"),
            ("INCREASE_SLOPE_MAX", "Pente max. augmentation (µS/s)", INCREASE_SLOPE_MAX, "Seuil maximum pour la pente d'augmentation de conductance"),
            ("DECREASE_SLOPE_THRESHOLD", "Seuil pente décroissance (µS/s)", DECREASE_SLOPE_THRESHOLD, "Seuil négatif pour détecter une diminution de conductance"),
            ("SLIDING_WINDOW", "Durée de la pente glissante (s)", SLIDING_WINDOW, "Durée de l'intervalle pour le calcul de la pente glissante"),
            ("R0_THRESHOLD", "Seuil R0 (Ohms)", R0_THRESHOLD, "Seuil de résistance R0 en Ohms pour le calcul de conductance"),
            ("CONDUCTANCE_DECREASE_THRESHOLD", "Seuil décroissance (µS)", CONDUCTANCE_DECREASE_THRESHOLD, "Seuil de décroissance de conductance en µS"),
            ("KEITHLEY_POLARIZATION_VOLTAGE", "Tension de polarisation (V)", KEITHLEY_POLARIZATION_VOLTAGE, "Tension de polarisation en Volts pour les mesures de conductance")
        ]

        for i, (const_name, label_text, current_value, tooltip) in enumerate(conductance_params):
            row_frame = tk.Frame(conductance_frame)
            row_frame.pack(fill=tk.X, padx=5, pady=2)

            label = tk.Label(row_frame, text=label_text, width=25, anchor="w")
            label.pack(side=tk.LEFT, padx=5)

            entry = tk.Entry(row_frame, width=10)
            entry.insert(0, str(current_value))
            entry.pack(side=tk.LEFT, padx=5)

            info_label = tk.Label(row_frame, text=tooltip, fg="gray", anchor="w")
            info_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=1)

            self.entries[const_name] = entry

        # Section des constantes de températuree
        temp_frame = ttk.LabelFrame(content_frame, text="Paramètres de température")
        temp_frame.pack(fill=tk.X, expand=1, padx=5, pady=5)

        temp_params = [
            ("REGENERATION_TEMP", "Température de régénération (°C)", REGENERATION_TEMP, "Température en °C pour la régénération"),
            ("TCONS_LOW", "Point de consigne bas (°C)", TCONS_LOW, "Point de consigne basse température en °C"),
            ("VALVE_DELAY", "Délai vanne (s)", VALVE_DELAY, "Délai d'attente en secondes après opération d'ouverture/fermeture de vanne")
        ]

        for i, (const_name, label_text, current_value, tooltip) in enumerate(temp_params):
            row_frame = tk.Frame(temp_frame)
            row_frame.pack(fill=tk.X, padx=5, pady=2)

            label = tk.Label(row_frame, text=label_text, width=25, anchor="w")
            label.pack(side=tk.LEFT, padx=5)

            entry = tk.Entry(row_frame, width=10)
            entry.insert(0, str(current_value))
            entry.pack(side=tk.LEFT, padx=5)

            info_label = tk.Label(row_frame, text=tooltip, fg="gray", anchor="w")
            info_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=1)

            self.entries[const_name] = entry

        # Section des constantes CO2
        co2_frame = ttk.LabelFrame(content_frame, text="Paramètres du protocole CO2")
        co2_frame.pack(fill=tk.X, expand=1, padx=5, pady=5)

        co2_params = [
            ("CO2_STABILITY_THRESHOLD", "Seuil stabilité CO2 (ppm)", CO2_STABILITY_THRESHOLD, "Variation maximale en ppm pour considérer le CO2 comme stable"),
            ("CO2_STABILITY_DURATION", "Durée stabilité CO2 (s)", CO2_STABILITY_DURATION, "Durée en secondes pendant laquelle le CO2 doit être stable"),
            ("REGENERATION_DURATION", "Durée régénération (s)", REGENERATION_DURATION, "Durée en secondes du maintien à haute température pendant la régénération"),
            ("CELL_VOLUME", "Volume cellule (L)", CELL_VOLUME, "Volume de la cellule de mesure en litres pour le calcul de masse de carbone"),
            ("CO2_INCREASE_THRESHOLD", "Seuil augmentation CO2 (ppm)", CO2_INCREASE_THRESHOLD, "Seuil d'augmentation de CO2 en ppm pour déclencher la détection")
        ]

        for i, (const_name, label_text, current_value, tooltip) in enumerate(co2_params):
            row_frame = tk.Frame(co2_frame)
            row_frame.pack(fill=tk.X, padx=5, pady=2)

            label = tk.Label(row_frame, text=label_text, width=25, anchor="w")
            label.pack(side=tk.LEFT, padx=5)

            entry = tk.Entry(row_frame, width=10)
            entry.insert(0, str(current_value))
            entry.pack(side=tk.LEFT, padx=5)

            info_label = tk.Label(row_frame, text=tooltip, fg="gray", anchor="w")
            info_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=1)

            self.entries[const_name] = entry

        # Boutons de contrôle
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=10)

        # Bouton pour réinitialiser aux valeurs par défaut
        reset_button = tk.Button(button_frame, text="Réinitialiser aux valeurs par défaut", command=self.reset_values)
        reset_button.pack(side=tk.LEFT, padx=5)

        # Bouton pour sauvegarder
        save_button = tk.Button(button_frame, text="Appliquer", command=self.save_values)
        save_button.pack(side=tk.LEFT, padx=5)

        # Bouton pour annuler
        cancel_button = tk.Button(button_frame, text="Annuler", command=self.window.destroy)
        cancel_button.pack(side=tk.LEFT, padx=5)

    def reset_values(self):
        """Réinitialise les champs aux valeurs par défaut"""
        # Réinitialiser les valeurs de conductance
        self.entries["STABILITY_DURATION"].delete(0, tk.END)
        self.entries["STABILITY_DURATION"].insert(0, str(STABILITY_DURATION))

        self.entries["INCREASE_SLOPE_MIN"].delete(0, tk.END)
        self.entries["INCREASE_SLOPE_MIN"].insert(0, str(INCREASE_SLOPE_MIN))

        self.entries["INCREASE_SLOPE_MAX"].delete(0, tk.END)
        self.entries["INCREASE_SLOPE_MAX"].insert(0, str(INCREASE_SLOPE_MAX))

        self.entries["DECREASE_SLOPE_THRESHOLD"].delete(0, tk.END)
        self.entries["DECREASE_SLOPE_THRESHOLD"].insert(0, str(DECREASE_SLOPE_THRESHOLD))

        self.entries["SLIDING_WINDOW"].delete(0, tk.END)
        self.entries["SLIDING_WINDOW"].insert(0, str(SLIDING_WINDOW))

        self.entries["R0_THRESHOLD"].delete(0, tk.END)
        self.entries["R0_THRESHOLD"].insert(0, str(R0_THRESHOLD))

        self.entries["CONDUCTANCE_DECREASE_THRESHOLD"].delete(0, tk.END)
        self.entries["CONDUCTANCE_DECREASE_THRESHOLD"].insert(0, str(CONDUCTANCE_DECREASE_THRESHOLD))
        
        self.entries["KEITHLEY_POLARIZATION_VOLTAGE"].delete(0, tk.END)
        self.entries["KEITHLEY_POLARIZATION_VOLTAGE"].insert(0, str(KEITHLEY_POLARIZATION_VOLTAGE))

        # Réinitialiser les valeurs de température
        self.entries["REGENERATION_TEMP"].delete(0, tk.END)
        self.entries["REGENERATION_TEMP"].insert(0, str(REGENERATION_TEMP))

        self.entries["TCONS_LOW"].delete(0, tk.END)
        self.entries["TCONS_LOW"].insert(0, str(TCONS_LOW))

        self.entries["VALVE_DELAY"].delete(0, tk.END)
        self.entries["VALVE_DELAY"].insert(0, str(VALVE_DELAY))

        # Réinitialiser les valeurs CO2
        self.entries["CO2_STABILITY_THRESHOLD"].delete(0, tk.END)
        self.entries["CO2_STABILITY_THRESHOLD"].insert(0, str(CO2_STABILITY_THRESHOLD))

        self.entries["CO2_STABILITY_DURATION"].delete(0, tk.END)
        self.entries["CO2_STABILITY_DURATION"].insert(0, str(CO2_STABILITY_DURATION))

        self.entries["REGENERATION_DURATION"].delete(0, tk.END)
        self.entries["REGENERATION_DURATION"].insert(0, str(REGENERATION_DURATION))

        self.entries["CELL_VOLUME"].delete(0, tk.END)
        self.entries["CELL_VOLUME"].insert(0, str(CELL_VOLUME))

        self.entries["CO2_INCREASE_THRESHOLD"].delete(0, tk.END)
        self.entries["CO2_INCREASE_THRESHOLD"].insert(0, str(CO2_INCREASE_THRESHOLD))

    def save_values(self):
        """Sauvegarde les valeurs modifiées pour la session en cours et dans les fichiers appropriés"""
        try:
            # Créer un dictionnaire avec les nouvelles valeurs
            # Important: Convertir les valeurs dans le bon type (float, int)
            new_values = {}

            # Vérifier et récupérer les valeurs des constantes de conductance
            for key in ["STABILITY_DURATION", "SLIDING_WINDOW", "R0_THRESHOLD", "CONDUCTANCE_DECREASE_THRESHOLD", "KEITHLEY_POLARIZATION_VOLTAGE"]:
                try:
                    # Ces constantes sont des entiers ou des nombres à virgule
                    value = self.entries[key].get().strip()
                    if "*" in value:  # Gestion des expressions comme "2 * 60"
                        new_values[key] = eval(value)
                    else:
                        new_values[key] = float(value)
                        # Convertir en entier si c'est un nombre entier
                        if new_values[key].is_integer():
                            new_values[key] = int(new_values[key])
                except (ValueError, SyntaxError) as e:
                    messagebox.showerror("Erreur", f"Valeur invalide pour {key}: {e}")
                    return

            # Vérifier et récupérer les seuils de pente (qui sont des flottants)
            for key in ["INCREASE_SLOPE_MIN", "INCREASE_SLOPE_MAX", "DECREASE_SLOPE_THRESHOLD"]:
                try:
                    value = self.entries[key].get().strip()
                    new_values[key] = float(value)
                except ValueError:
                    messagebox.showerror("Erreur", f"Valeur invalide pour {key} (doit être un nombre décimal)")
                    return

            # Vérifier et récupérer les valeurs de température
            for key in ["REGENERATION_TEMP", "TCONS_LOW", "VALVE_DELAY"]:
                try:
                    value = self.entries[key].get().strip()
                    new_values[key] = float(value)
                    # Convertir en entier si c'est un nombre entier
                    if new_values[key].is_integer():
                        new_values[key] = int(new_values[key])
                except ValueError:
                    messagebox.showerror("Erreur", f"Valeur invalide pour {key}")
                    return

            # Vérifier et récupérer les valeurs CO2
            for key in ["CO2_STABILITY_THRESHOLD", "CO2_STABILITY_DURATION", "REGENERATION_DURATION", "CO2_INCREASE_THRESHOLD"]:
                try:
                    value = self.entries[key].get().strip()
                    if "*" in value:  # Gestion des expressions comme "2 * 60"
                        new_values[key] = eval(value)
                    else:
                        new_values[key] = float(value)
                        # Convertir en entier si c'est un nombre entier
                        if new_values[key].is_integer():
                            new_values[key] = int(new_values[key])
                except (ValueError, SyntaxError):
                    messagebox.showerror("Erreur", f"Valeur invalide pour {key}")
                    return

            # CELL_VOLUME est toujours un flottant
            try:
                new_values["CELL_VOLUME"] = float(self.entries["CELL_VOLUME"].get().strip())
            except ValueError:
                messagebox.showerror("Erreur", "Valeur invalide pour CELL_VOLUME (doit être un nombre décimal)")
                return

            # Appliquer les nouvelles valeurs aux constantes globales
            for key, value in new_values.items():
                globals()[key] = value

            # Modifier les constantes dans le module
            import core.constants
            for key, value in new_values.items():
                setattr(core.constants, key, value)
            
            # Vérifier si nous sommes en mode exécutable
            from utils.config_manager import is_running_as_executable, save_config
            
            success_message = "Les paramètres ont été appliqués pour cette session"
            if is_running_as_executable():
                # En mode exécutable, sauvegarder dans fichier JSON
                if save_config(new_values):
                    success_message += " et sauvegardés dans le fichier de configuration"
                else:
                    messagebox.showwarning("Avertissement",
                       "Les paramètres ont été appliqués pour cette session mais n'ont pas pu être sauvegardés dans le fichier de configuration")
            else:
                # En mode script, sauvegarder dans le fichier constants.py
                try:
                    # Chemin du module constants.py
                    import os
                    import inspect
                    constants_file_path = inspect.getfile(core.constants)
                    
                    # Lire le contenu actuel du fichier
                    with open(constants_file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                    
                    # Mettre à jour chaque constante dans le fichier
                    for key, value in new_values.items():
                        # Créer un pattern de recherche pour la constante
                        import re
                        if isinstance(value, int) or isinstance(value, float):
                            # Remplacer la valeur numérique
                            pattern = rf"^{key}\s*=\s*[0-9*\.\s]+.*$"
                            # Conserver les commentaires éventuels après la valeur
                            comment_match = re.search(rf"^{key}\s*=\s*[0-9*\.\s]+(.*)$", file_content, re.MULTILINE)
                            comment = comment_match.group(1) if comment_match else ""
                            replacement = f"{key} = {value}{comment}"
                            file_content = re.sub(pattern, replacement, file_content, flags=re.MULTILINE)
                    
                    # Écrire le contenu mis à jour dans le fichier
                    with open(constants_file_path, 'w', encoding='utf-8') as f:
                        f.write(file_content)
                        
                    success_message += " et sauvegardés dans le fichier constants.py"
                    
                except Exception as file_error:
                    # En cas d'erreur lors de l'écriture du fichier, informer l'utilisateur mais continuer
                    messagebox.showwarning("Avertissement", 
                        f"Les paramètres ont été appliqués pour cette session mais n'ont pas pu être sauvegardés de façon permanente:\n{str(file_error)}")
            
            # Afficher un message de succès
            messagebox.showinfo("Succès", success_message)
            
            # Fermer la fenêtre
            self.window.destroy()

        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue: {str(e)}")