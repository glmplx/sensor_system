"""
Interface utilisateur du menu pour le système de capteurs
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import serial.tools.list_ports
import os
import sys
from core.constants import EXCEL_BASE_DIR

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
        self.other_baud_rate_var = tk.IntVar(value=115200)
        self.mode_manual_var = tk.IntVar()
        self.mode_auto_var = tk.IntVar()
        
        # Measurement selection variables (for manual mode)
        self.measure_conductance_var = tk.IntVar(value=0)  # Conductance désactivée par défaut
        self.measure_co2_var = tk.IntVar(value=1)
        self.measure_regen_var = tk.IntVar(value=1)
        
        # Set up UI elements
        self.setup_ui()
    
    def setup_ui(self):
        """Configurer les éléments de l'interface utilisateur"""
        # Detect available COM ports
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
        
        # Arduino port selection
        tk.Label(self.window, text="Port COM de l'Arduino:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        arduino_com_dropdown = tk.OptionMenu(self.window, self.arduino_com_var, *ports_display)
        arduino_com_dropdown.grid(row=0, column=1, padx=10, pady=10)
        
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
        arduino_baud_rate_entry.grid(row=1, column=1, padx=10, pady=10)
        
        # Regeneration card port selection
        tk.Label(self.window, text="Port COM de la carte pour la régénération:").grid(row=2, column=0, padx=10, pady=10, sticky='w')
        other_com_dropdown = tk.OptionMenu(self.window, self.other_com_var, *ports_display)
        other_com_dropdown.grid(row=2, column=1, padx=10, pady=10)
        
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
        other_baud_rate_entry.grid(row=3, column=1, padx=10, pady=10)
        
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
        
        # Button frame to hold both launch and quit buttons
        button_frame = tk.Frame(self.window)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        # Launch button
        launch_button = tk.Button(button_frame, text="Lancer le programme", command=self.launch_program)
        launch_button.pack(side=tk.LEFT, padx=10)
        
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
        
        # Import and run directly instead of launching a new process
        if getattr(sys, 'frozen', False):
            # Running as executable
            if self.mode_auto_var.get():
                # Import auto app dynamically
                import auto_app
                auto_app.main(arduino_port, arduino_baud_rate, other_port, other_baud_rate)
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
                    measure_regen=measure_regen
                )
        else:
            # Running as script
            if self.mode_auto_var.get():
                # Auto mode
                script_name = "auto_app.py"
                script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), script_name)
                command = [sys.executable, script_path, arduino_port, str(arduino_baud_rate), other_port, str(other_baud_rate)]
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
                    "--measure_regen", str(measure_regen)
                ]
            
            # Utiliser execv pour remplacer le processus actuel (pas de sous-processus)
            os.execv(sys.executable, command)
    
    def quit_application(self):
        """Ferme l'application proprement et termine le processus"""
        self.window.destroy()
        import sys
        sys.exit(0)

    def run(self):
        """Exécuter la boucle principale de l'interface utilisateur"""
        self.window.mainloop()