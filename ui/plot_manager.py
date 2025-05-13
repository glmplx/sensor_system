"""
Gestionnaire de graphiques pour l'interface utilisateur du système de capteurs
"""

import sys
import time
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, TextBox, RadioButtons

class PlotManager:
    """Gère les graphiques matplotlib et les éléments d'interface utilisateur"""
    
    def __init__(self, mode="manual"):
        """
        Initialise le gestionnaire de graphiques
        
        Args:
            mode: Mode "manual" ou "auto"
        """
        # Désactiver la barre d'outils de navigation avant de créer les figures
        plt.rcParams['toolbar'] = 'None'
        
        self.mode = mode
        self.fig = None
        self.axes = {
            'conductance': None,
            'co2': None,
            'co2_right': None,
            'res_temp': None
        }
        self.buttons = {}
        self.indicators = {}
        self.textboxes = {}
        self.radiobuttons = {}
        
        # Variable pour suivre les préférences d'affichage des unités de temps (par défaut : secondes)
        self.display_minutes = False
        
        # Référence pour le temps de restabilisation du CO2
        self.reference_restabilization_time = None
        
        # Statut des appareils disponibles
        self.available_devices = {
            'arduino': False,
            'regen': False,
            'keithley': False
        }
        
        # Boutons d'ajout d'appareils
        self.add_device_buttons = {}
        
        # Configuration de la figure et des graphiques
        self.setup_plots()
    
    def setup_plots(self):
        """Configure la figure et les axes pour les graphiques"""
        # Créer une figure sans barre d'outils en utilisant le paramètre 'toolbar=None'
        self.fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 18))
        
        
        # Définition de la taille/position de la fenêtre en fonction du mode d'exécution
        try:
            manager = plt.get_current_fig_manager()
            
            # Vérifier si exécuté sous forme d'exécutable
            if getattr(sys, 'frozen', False):
                # Pour l'exécutable, utiliser une taille plus conservative et essayer de centrer la fenêtre
                width, height = 1400, 800  # Taille plus conservative
                
                # Essayer différentes méthodes pour ajuster la fenêtre
                try:
                    # Essayer de centrer la fenêtre - pour Tkinter
                    if hasattr(manager, 'canvas') and hasattr(manager.canvas, 'manager') and hasattr(manager.canvas.manager, 'window'):
                        root = manager.canvas.manager.window
                        # D'abord configurer la taille de la fenêtre
                        root.geometry(f"{width}x{height}")
                        
                        # Ensuite la centrer après un court délai
                        def center_window():
                            """Centre la fenêtre sur l'écran"""
                            screen_width = root.winfo_screenwidth()
                            screen_height = root.winfo_screenheight()
                            pos_x = (screen_width // 2) - (width // 2)
                            pos_y = (screen_height // 2) - (height // 2)
                            root.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
                        
                        # Programmer le centrage pour après la création de la fenêtre
                        root.after(100, center_window)
                    
                    # For Qt backends
                    elif hasattr(manager, 'window') and hasattr(manager.window, 'setGeometry'):
                        import tkinter as tk
                        # Create a temporary root to get screen dimensions
                        temp_root = tk.Tk()
                        screen_width = temp_root.winfo_screenwidth()
                        screen_height = temp_root.winfo_screenheight()
                        temp_root.destroy()
                        
                        # Calculate centered position
                        pos_x = (screen_width // 2) - (width // 2)
                        pos_y = (screen_height // 2) - (height // 2)
                        manager.window.setGeometry(pos_x, pos_y, width, height)
                    
                    # Generic approach
                    else:
                        # Just use reasonable defaults that should work on most screens
                        self.fig.set_size_inches(14, 9)
                        if hasattr(manager, 'window') and hasattr(manager.window, 'wm_geometry'):
                            manager.window.wm_geometry(f"{width}x{height}+10+10")
                
                except Exception as e:
                    print(f"Failed to center window: {e}")
                    # Fallback to a very simple approach
                    self.fig.set_size_inches(12, 8)
            
            else:
                # Running as script - maximize window
                if hasattr(manager, 'window') and hasattr(manager.window, 'showMaximized'):
                    manager.window.showMaximized()
                elif hasattr(manager, 'full_screen_toggle'):
                    manager.full_screen_toggle()
                elif hasattr(manager, 'frame'):
                    manager.frame.Maximize(True)
                elif hasattr(manager, 'resize'):
                    manager.resize(*manager.window.maxsize())
                
        except Exception as e:
            print(f"Note: Could not set window size: {e}")
        
        # Adjust margins
        plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.15)
        
        # Enable interactive mode
        plt.ion()
        
        # Conductance plot
        ax1.set_xlabel('Temps (s)')
        ax1.set_ylabel('Conductance (µS)')
        self.axes['conductance'] = ax1
        
        # CO2, temperature and humidity plot
        ax2.set_xlabel('Temps (s)')
        ax2.set_ylabel('CO2 (ppm)', color='tab:blue')
        self.axes['co2'] = ax2
        
        # Create secondary axis for temperature and humidity
        ax2_right = ax2.twinx()
        ax2_right.set_ylabel('Température (°C) et Humidité (%)', color='black')
        self.axes['co2_right'] = ax2_right
        
        # Temperature and Tcons plot
        ax3.set_xlabel('Temps (s)')
        ax3.set_ylabel('Température °C')
        self.axes['res_temp'] = ax3
        
        # Set visibility to be configured later via configure_measurement_panels
        # Default to visible until explicitly hidden
        ax1.set_visible(True)
        ax2.set_visible(True)
        ax2_right.set_visible(True)
        ax3.set_visible(True)
        
        # Add buttons based on the mode
        if self.mode == "manual":
            self.setup_manual_buttons()
        else:
            self.setup_auto_buttons()
        
        # Add common elements
        self.setup_common_elements()
    
    def setup_manual_buttons(self):
        """Configure les boutons pour le mode manuel"""
        button_width = 0.1
        button_height = 0.04
        
        # Start/Stop buttons for each measurement
        ax_button_conductance = plt.axes([0.02, 0.01, button_width, button_height])
        self.buttons['conductance'] = Button(ax_button_conductance, 'Start/Stop Conduct.')
        self.buttons['conductance'].active = True  # Définir active=True par défaut
        
        ax_button_co2_temp_humidity = plt.axes([0.14, 0.01, button_width, button_height])
        self.buttons['co2_temp_humidity'] = Button(ax_button_co2_temp_humidity, 'Start/Stop CO2/T/H')
        self.buttons['co2_temp_humidity'].active = True  # Définir active=True par défaut
        
        ax_button_res_temp = plt.axes([0.26, 0.01, button_width, button_height])
        self.buttons['res_temp'] = Button(ax_button_res_temp, 'Start/Stop Res/Temp')
        self.buttons['res_temp'].active = True  # Définir active=True par défaut
        
        # Reset buttons for each measurement
        ax_button_raz_conductance = plt.axes([0.02, 0.06, button_width, button_height])
        self.buttons['raz_conductance'] = Button(ax_button_raz_conductance, 'RAZ Conduct.')
        
        ax_button_raz_co2_temp_humidity = plt.axes([0.14, 0.06, button_width, button_height])
        self.buttons['raz_co2_temp_humidity'] = Button(ax_button_raz_co2_temp_humidity, 'RAZ CO2/T/H')
        
        ax_button_raz_res_temp = plt.axes([0.26, 0.06, button_width, button_height])
        self.buttons['raz_res_temp'] = Button(ax_button_raz_res_temp, 'RAZ Res/Temp')
        
        # Protocole buttons à droite de Start/Stop Res/Temp
        protocol_button_width = button_width * 0.85  # Légèrement plus large pour mieux afficher le texte
        protocol_y = 0.01  # Même hauteur que les boutons Start/Stop
        spacing = 0.04  # Définir spacing ici avant utilisation
        
        # Position X juste après le bouton Start/Stop Res/Temp (0.26 + button_width)
        protocol_x = 0.38
        
        # Créer une barre de progression pour les protocoles
        protocol_progress_y = protocol_y + button_height + 0.01  # Juste au-dessus des boutons
        protocol_progress_width = protocol_button_width * 2.25 + 0.03  # Largeur pour couvrir les deux boutons
        ax_protocol_progress = plt.axes([protocol_x, protocol_progress_y, protocol_progress_width, 0.015])  # Épaisseur augmentée de 0.01 à 0.015
        ax_protocol_progress.set_xticks([])
        ax_protocol_progress.set_yticks([])
        ax_protocol_progress.set_frame_on(True)  # Afficher le cadre
        ax_protocol_progress.patch.set_alpha(0.2)  # Rendre semi-transparent pour voir le cadre
        ax_protocol_progress.set_xlabel('')
        ax_protocol_progress.set_title('Progression', fontsize=8, pad=2)
        ax_protocol_progress.text(0.5, 0.5, '0%', ha='center', va='center', transform=ax_protocol_progress.transAxes, fontsize=7)
        ax_protocol_progress.set_visible(False)  # Initialement invisible
        self.indicators['protocol_progress'] = ax_protocol_progress
        
        # Bouton Protocole CO2
        ax_button_regeneration = plt.axes([protocol_x, protocol_y, protocol_button_width, button_height])
        regeneration_button = Button(ax_button_regeneration, 'Protocole CO2', color='firebrick')
        regeneration_button.ax.set_facecolor('firebrick')
        regeneration_button.color = 'firebrick'
        regeneration_button.label.set_color('white')
        self.buttons['regeneration'] = regeneration_button
        
        # Bouton pour le protocole de conductance avec résistance/température
        protocol_x2 = protocol_x + protocol_button_width + 0.03  # Légèrement plus espacé
        protocol_button_width2 = protocol_button_width * 1.4  # Encore plus large pour le texte plus long
        ax_button_cond_regen = plt.axes([protocol_x2, protocol_y, protocol_button_width2, button_height])
        cond_regen_button = Button(ax_button_cond_regen, 'Protocole Conductance', color='darkblue')
        # Activé dès le départ
        cond_regen_button.ax.set_facecolor('darkblue')
        cond_regen_button.color = 'darkblue'
        cond_regen_button.label.set_color('white')
        cond_regen_button.active = True  # Activé par défaut
        self.buttons['conductance_regen'] = cond_regen_button
        
        # Bouton pour le protocole complet (conductance, co2, température)
        protocol_x3 = protocol_x2 + protocol_button_width2 + 0.03  # À droite du bouton protocole conductance
        protocol_button_width3 = protocol_button_width2  # Même largeur que le bouton protocole conductance
        ax_button_complet = plt.axes([protocol_x3, protocol_y, protocol_button_width3, button_height])
        complet_button = Button(ax_button_complet, 'Protocole Complet', color='darkgreen')
        # Initialement désactivé comme les autres boutons protocole
        complet_button.ax.set_facecolor('lightgray')
        complet_button.color = 'lightgray'
        complet_button.label.set_color('darkgray')
        complet_button.active = False  # Désactivé par défaut
        self.buttons['protocole_complet'] = complet_button
        
        # Bouton d'annulation de régénération (initialement caché) - au-dessus du bouton Protocole Complet
        cancel_x = protocol_x3 + (protocol_button_width3 / 2) - (button_width * 0.35)  # Centré au-dessus du Protocole Complet
        cancel_y = protocol_y + button_height + 0.03  # Au-dessus des boutons protocole
        ax_button_cancel_regen = plt.axes([cancel_x, cancel_y, button_width * 0.7, button_height])
        cancel_regen_button = Button(ax_button_cancel_regen, 'Cancel', color='orange')
        cancel_regen_button.ax.set_facecolor('orange')
        cancel_regen_button.color = 'orange'
        cancel_regen_button.label.set_color('black')
        cancel_regen_button.ax.set_visible(False)  # Initialement caché
        self.buttons['cancel_regeneration'] = cancel_regen_button
        
        # Tcons input and button - déplacés vers la droite en vertical et encore plus bas
        spacing = 0.04  # Espacement vertical
        right_column_x = 0.92  # Position X de la colonne droite
        # Définir right_column_y_start ici car il est utilisé dans setup_common_elements mais pas défini ici
        right_column_y_start = 0.7  # Position Y de départ
        tcons_y_start = 0.18  # Position encore plus basse pour mieux espacer de R0
        compact_button_width = button_width/1.8
        
        # Tcons textbox - collé au bouton Set Tcons
        ax_button_Tcons = plt.axes([right_column_x, tcons_y_start - button_height - spacing/2, compact_button_width, button_height])
        self.buttons['set_Tcons'] = Button(ax_button_Tcons, 'Set Tcons')
        
        # Tcons textbox juste au-dessus du bouton
        ax_textbox_Tcons = plt.axes([right_column_x, tcons_y_start - button_height/2, compact_button_width, button_height])
        self.textboxes['Tcons'] = TextBox(ax_textbox_Tcons, '', initial='')
        self.buttons['set_Tcons'].active = True  # Définir active=True par défaut
    
    def setup_auto_buttons(self):
        """Configure les boutons pour le mode automatique"""
        button_width = 0.1
        button_height = 0.04
        
        # Auto start/stop button
        ax_button_auto = plt.axes([0.02, 0.01, button_width, button_height])
        self.buttons['auto'] = Button(ax_button_auto, 'Start/Stop Auto.')
        
        # Reset button for auto mode
        ax_button_raz_auto = plt.axes([0.14, 0.01, button_width, button_height])
        self.buttons['raz_auto'] = Button(ax_button_raz_auto, 'RAZ Auto.')
        
        # Protocole buttons à droite de Start/Stop Res/Temp
        protocol_button_width = button_width * 0.85  # Légèrement plus large pour mieux afficher le texte
        protocol_y = 0.01  # Même hauteur que les boutons Start/Stop
        spacing = 0.04  # Définir spacing ici avant utilisation
        
        # Position X juste après le bouton Start/Stop Res/Temp (0.26 + button_width)
        protocol_x = 0.38
        
        # Bouton Protocole CO2
        ax_button_regeneration = plt.axes([protocol_x, protocol_y, protocol_button_width, button_height])
        regeneration_button = Button(ax_button_regeneration, 'Protocole CO2', color='firebrick')
        regeneration_button.ax.set_facecolor('firebrick')
        regeneration_button.color = 'firebrick'
        regeneration_button.label.set_color('white')
        self.buttons['regeneration'] = regeneration_button
        
        # Bouton pour le protocole de conductance avec résistance/température
        protocol_x2 = protocol_x + protocol_button_width + 0.03  # Légèrement plus espacé
        protocol_button_width2 = protocol_button_width * 1.4  # Encore plus large pour le texte plus long
        ax_button_cond_regen = plt.axes([protocol_x2, protocol_y, protocol_button_width2, button_height])
        cond_regen_button = Button(ax_button_cond_regen, 'Protocole Conductance', color='darkblue')
        # Activé dès le départ
        cond_regen_button.ax.set_facecolor('darkblue')
        cond_regen_button.color = 'darkblue'
        cond_regen_button.label.set_color('white')
        cond_regen_button.active = True  # Activé par défaut
        self.buttons['conductance_regen'] = cond_regen_button
        
        # Bouton pour le protocole complet (conductance, co2, température)
        protocol_x3 = protocol_x2 + protocol_button_width2 + 0.03  # À droite du bouton protocole conductance
        protocol_button_width3 = protocol_button_width2  # Même largeur que le bouton protocole conductance
        ax_button_complet = plt.axes([protocol_x3, protocol_y, protocol_button_width3, button_height])
        complet_button = Button(ax_button_complet, 'Protocole Complet', color='darkgreen')
        # Initialement désactivé comme les autres boutons protocole
        complet_button.ax.set_facecolor('lightgray')
        complet_button.color = 'lightgray'
        complet_button.label.set_color('darkgray')
        complet_button.active = False  # Désactivé par défaut
        self.buttons['protocole_complet'] = complet_button
        
        # Bouton d'annulation de régénération (initialement caché) - au-dessus du bouton Protocole Complet
        cancel_x = protocol_x3 + (protocol_button_width3 / 2) - (button_width * 0.35)  # Centré au-dessus du Protocole Complet
        cancel_y = protocol_y + button_height + 0.03  # Au-dessus des boutons protocole
        ax_button_cancel_regen = plt.axes([cancel_x, cancel_y, button_width * 0.7, button_height])
        cancel_regen_button = Button(ax_button_cancel_regen, 'Cancel', color='orange')
        cancel_regen_button.ax.set_facecolor('orange')
        cancel_regen_button.color = 'orange'
        cancel_regen_button.label.set_color('black')
        cancel_regen_button.ax.set_visible(False)  # Initialement caché
        self.buttons['cancel_regeneration'] = cancel_regen_button
    
    def setup_common_elements(self):
        """Configure les éléments communs aux deux modes"""
        button_width = 0.1
        button_height = 0.04
        
        # Add device buttons - en haut à gauche, empilés en colonne
        self.setup_add_device_buttons()
        
        # Time unit selection radio buttons (right side of trappe indicators)
        ax_radio_time_unit = plt.axes([0.50, 0.91, 0.12, 0.05])
        self.radiobuttons['time_unit'] = RadioButtons(ax_radio_time_unit, ('Secondes', 'Minutes'), active=0)
        ax_radio_time_unit.set_title('Unités de temps', fontsize=9)
        
        # R0 textbox et boutons au-dessus du bouton Init mais plus à droite et plus haut
        init_x = 0.89  # Position X du bouton Init
        init_y = 0.06  # Position Y du bouton Init
        spacing = 0.04  # Espacement vertical - définir spacing AVANT utilisation
        r0_x = 0.92  # Aligné avec Tcons (même position X que right_column_x)
        r0_y_start = init_y + spacing*9  # Position encore plus haute pour plus d'espace
        compact_button_width = button_width/1.8
        
        # Premier élément: R0 display (sans label)
        ax_r0_display = plt.axes([r0_x, r0_y_start - button_height/2, compact_button_width, button_height])
        self.indicators['R0_display'] = ax_r0_display
        
        # Deuxième élément: Update R0 button
        ax_button_update_R0 = plt.axes([r0_x, r0_y_start - spacing - button_height/2, compact_button_width, button_height])
        self.buttons['update_R0'] = Button(ax_button_update_R0, 'Update')
        
        # Troisième élément: R0 textbox (sans label)
        ax_textbox_R0 = plt.axes([r0_x, r0_y_start - spacing*3 - button_height/2, compact_button_width, button_height])
        self.textboxes['R0'] = TextBox(ax_textbox_R0, '', initial='')
        
        # Quatrième élément: Set R0 button - directement collé au textbox
        ax_button_R0 = plt.axes([r0_x, r0_y_start - spacing*3 - button_height*1.5, compact_button_width, button_height])
        self.buttons['set_R0'] = Button(ax_button_R0, 'Set R0')
        
        # Push/Open and Retract/Close buttons (grayed out initially)
        ax_button_PushOpen = plt.axes([0.78, 0.01, button_width, button_height])
        push_open_button = Button(ax_button_PushOpen, 'Push/Open', color='lightgray')
        push_open_button.ax.set_facecolor('lightgray')
        push_open_button.color = 'lightgray'
        push_open_button.active = False  # Custom flag to track if button is usable
        self.buttons['push_open'] = push_open_button
        
        ax_button_RetractClose = plt.axes([0.78, 0.06, button_width, button_height])
        retract_close_button = Button(ax_button_RetractClose, 'Retract/Close', color='lightgray')
        retract_close_button.ax.set_facecolor('lightgray')
        retract_close_button.color = 'lightgray'
        retract_close_button.active = False  # Custom flag to track if button is usable
        self.buttons['retract_close'] = retract_close_button
        
        # Quit button
        ax_button_quit = plt.axes([0.89, 0.01, button_width, button_height])
        self.buttons['quit'] = Button(ax_button_quit, 'Quitter')
        
        # Start all measurements button (green)
        ax_button_start_all = plt.axes([0.14, 0.11, button_width, button_height])
        start_all_button = Button(ax_button_start_all, 'Start/Stop All', color='lightgreen')
        start_all_button.ax.set_facecolor('lightgreen')
        start_all_button.color = 'lightgreen'
        self.buttons['start_all'] = start_all_button
        
        # Status indicators
        self.setup_indicators()
        
        # R0 display - supprimé car déplacé à droite
        
        # Delta C display - position décalée plus à droite
        ax_delta_c = plt.axes([0.68, 0.92, button_width/2.2, button_height])
        ax_delta_c.text(0.5, 0.5, "Delta C: 0 ppm", ha="center", va="center", transform=ax_delta_c.transAxes)
        ax_delta_c.axis('off')
        self.indicators['delta_c_display'] = ax_delta_c
        
        # Carbon mass display - position décalée plus à droite
        ax_carbon_mass = plt.axes([0.78, 0.92, button_width/2.2, button_height])
        ax_carbon_mass.text(0.5, 0.5, "Masse C: 0 µg", ha="center", va="center", transform=ax_carbon_mass.transAxes)
        ax_carbon_mass.axis('off')
        self.indicators['carbon_mass_display'] = ax_carbon_mass
        
        # Percolation time display - position décalée plus à droite
        ax_percolation_time = plt.axes([0.88, 0.92, button_width/2.2, button_height])
        ax_percolation_time.text(0.5, 0.5, "T perco: 0 s", ha="center", va="center", transform=ax_percolation_time.transAxes)
        ax_percolation_time.axis('off')
        self.indicators['percolation_time_display'] = ax_percolation_time
        
        # Indicateur de sauvegarde de secours - en dessous de la masse de carbone
        ax_backup_indicator = plt.axes([0.86, 0.89, button_width/1.5, button_height * 0.8])
        ax_backup_indicator.text(0.5, 0.5, "Dernière sauvegarde: --:--:--", fontsize=7, 
                                 ha="center", va="center", transform=ax_backup_indicator.transAxes)
        ax_backup_indicator.axis('off')
        self.indicators['backup_status'] = ax_backup_indicator
        
        # Init button (blue)
        ax_button_init = plt.axes([0.89, 0.06, button_width, button_height])
        init_button = Button(ax_button_init, 'Init', color='lightblue')
        # Assurer que la couleur est bien appliquée
        init_button.ax.set_facecolor('lightblue')
        init_button.color = 'lightblue'
        self.buttons['init'] = init_button
        
    def setup_add_device_buttons(self):
        """Configure les boutons pour ajouter des appareils pendant l'exécution"""
        button_width = 0.1
        button_height = 0.03
        
        # Position initiale des éléments
        title_x = 0.01
        title_width = 0.12
        title_y = 0.97
        button_x = title_x + title_width/2 - button_width/2  # Centré sous le titre
        
        # Créer un titre pour le groupe de boutons
        ax_title = plt.axes([title_x, title_y, title_width, 0.02])
        ax_title.text(0.5, 0.5, "Ajouter appareils", ha="center", va="center", transform=ax_title.transAxes, fontweight='bold', fontsize=8)
        ax_title.axis('off')
        
        # Stockage des informations de position pour le décalage dynamique
        self.add_device_button_info = {
            'arduino': {'index': 0, 'visible_index': 0, 'color': 'lightskyblue', 'label': 'Arduino'},
            'regen': {'index': 1, 'visible_index': 1, 'color': 'lightcoral', 'label': 'Régénération'},
            'keithley': {'index': 2, 'visible_index': 2, 'color': 'lightgreen', 'label': 'Keithley'}
        }
        
        # Créer les boutons mais ne pas les positionner encore
        # Les positions seront ajustées dynamiquement dans update_add_device_buttons
        for device_type, info in self.add_device_button_info.items():
            # Position initiale (sera ajustée plus tard)
            y_pos = title_y - 0.03 - info['index'] * (button_height + 0.01)
            ax_button = plt.axes([button_x, y_pos, button_width, button_height])
            
            button = Button(ax_button, info['label'], color=info['color'])
            button.ax.set_facecolor(info['color'])
            button.color = info['color']
            button.active = True
            button.label.set_fontsize(8)  # Réduire la taille du texte
            self.add_device_buttons[device_type] = button
            
            # Par défaut, tous les boutons sont cachés
            button.ax.set_visible(False)
    
    def setup_indicators(self):
        """Configure les indicateurs d'état"""
        # Les indicateurs d'augmentation et de stabilisation sont maintenant des lignes verticales
        # sur le graphique et non plus des voyants LED
        
        # Créer des indicateurs vides pour maintenir la compatibilité avec le code existant
        self.indicators['increase_led'] = None
        self.indicators['stabilization_led'] = None
        
        # Vérin rentré indicator
        ax_sensor_in_led = plt.axes([0.17, 0.95, 0.02, 0.02])
        sensor_in_led = plt.Rectangle((0,0), 1, 1, color='gray')
        ax_sensor_in_led.add_patch(sensor_in_led)
        ax_sensor_in_led.text(1.2, 0.5, 'Vérin Rentré', va='center', ha='left', transform=ax_sensor_in_led.transAxes)
        ax_sensor_in_led.axis('off')
        self.indicators['sensor_in_led'] = sensor_in_led
        
        # Vérin sorti indicator
        ax_sensor_out_led = plt.axes([0.17, 0.92, 0.02, 0.02])
        sensor_out_led = plt.Rectangle((0,0), 1, 1, color='gray')
        ax_sensor_out_led.add_patch(sensor_out_led)
        ax_sensor_out_led.text(1.2, 0.5, 'Vérin Sorti', va='center', ha='left', transform=ax_sensor_out_led.transAxes)
        ax_sensor_out_led.axis('off')
        self.indicators['sensor_out_led'] = sensor_out_led
        
        # Trappe fermée indicator
        ax_trappe_fermee_led = plt.axes([0.35, 0.95, 0.02, 0.02])
        trappe_fermee_led = plt.Rectangle((0,0), 1, 1, color='gray')
        ax_trappe_fermee_led.add_patch(trappe_fermee_led)
        ax_trappe_fermee_led.text(1.2, 0.5, 'Trappe Fermée', va='center', ha='left', transform=ax_trappe_fermee_led.transAxes)
        ax_trappe_fermee_led.axis('off')
        self.indicators['trappe_fermee_led'] = trappe_fermee_led
        
        # Trappe ouverte indicator
        ax_trappe_ouverte_led = plt.axes([0.35, 0.92, 0.02, 0.02])
        trappe_ouverte_led = plt.Rectangle((0,0), 1, 1, color='gray')
        ax_trappe_ouverte_led.add_patch(trappe_ouverte_led)
        ax_trappe_ouverte_led.text(1.2, 0.5, 'Trappe Ouverte', va='center', ha='left', transform=ax_trappe_ouverte_led.transAxes)
        ax_trappe_ouverte_led.axis('off')
        self.indicators['trappe_ouverte_led'] = trappe_ouverte_led
    
    def connect_button(self, button_name, callback):
        """
        Connecte un bouton à une fonction de rappel

        Args:
            button_name: Nom du bouton à connecter
            callback: Fonction à appeler lorsque le bouton est cliqué
        """
        if button_name in self.buttons:
            # Pour les boutons qui peuvent être désactivés (push_open, retract_close, co2_temp_humidity, res_temp, protocole_complet, etc.)
            if button_name in ['push_open', 'retract_close', 'co2_temp_humidity', 'res_temp', 'set_Tcons', 'protocole_complet', 'regeneration', 'conductance_regen']:

                def wrapped_disabled_callback(event):
                    """ Fonction de rappel qui gère les boutons désactivés """
                    # Ne rien faire si le bouton est désactivé
                    if hasattr(self.buttons[button_name], 'active') and not self.buttons[button_name].active:
                        return

                    # Sinon, appeler le callback normal avec l'event
                    callback(event)

                self.buttons[button_name].on_clicked(wrapped_disabled_callback)

                # S'assurer que le bouton a l'attribut 'active'
                if not hasattr(self.buttons[button_name], 'active'):
                    self.buttons[button_name].active = True

            # Cas spécial pour le bouton init qui active les autres boutons
            elif button_name == 'init':
                original_color = self.buttons[button_name].ax.get_facecolor()

                def wrapped_init_callback(event):
                    """ Fonction de rappel qui gère le bouton init """
                    # Appeler le callback original
                    callback(event)

                    # Restaurer la couleur originale après le clic
                    self.buttons[button_name].ax.set_facecolor('lightblue')

                    # Activer les boutons push_open et retract_close
                    for btn_name in ['push_open', 'retract_close']:
                        if btn_name in self.buttons:
                            button = self.buttons[btn_name]
                            button.active = True
                            button.ax.set_facecolor('white')
                            button.color = 'white'

                    # Mettre à jour l'état des boutons de protocole en fonction des mesures actuellement actives
                    self.update_protocol_button_states(
                        measure_co2_temp_humidity_active=hasattr(self, 'measure_co2_temp_humidity_active') and self.measure_co2_temp_humidity_active,
                        measure_conductance_active=hasattr(self, 'measure_conductance_active') and self.measure_conductance_active,
                        measure_res_temp_active=hasattr(self, 'measure_res_temp_active') and self.measure_res_temp_active
                    )

                    # Forcer la mise à jour du canvas
                    self.buttons[button_name].ax.figure.canvas.draw_idle()

                self.buttons[button_name].on_clicked(wrapped_init_callback)
            else:
                self.buttons[button_name].on_clicked(callback)
    
    def connect_textbox(self, textbox_name, callback):
        """
        Connecte un champ de texte à une fonction de rappel
        
        Args:
            textbox_name: Nom du champ de texte à connecter
            callback: Fonction à appeler lorsque le champ de texte est soumis
        """
        if textbox_name in self.textboxes:
            self.textboxes[textbox_name].on_submit(callback)
            
    def connect_radiobutton(self, radiobutton_name, callback):
        """
        Connecte un bouton radio à une fonction de rappel
        
        Args:
            radiobutton_name: Nom du bouton radio à connecter
            callback: Fonction à appeler lorsque la sélection du bouton radio change
        """
        if radiobutton_name in self.radiobuttons:
            self.radiobuttons[radiobutton_name].on_clicked(callback)
    
    def update_indicator(self, indicator_name, state):
        """
        Met à jour l'état d'un indicateur
        
        Args:
            indicator_name: Nom de l'indicateur à mettre à jour
            state: Nouvel état pour l'indicateur (True = actif, False = inactif)
        """
        if indicator_name in self.indicators:
            indicator = self.indicators[indicator_name]
            if indicator is None:
                # Ignore les indicateurs None (comme increase_led et stabilization_led qui sont maintenant des lignes verticales)
                return
            
            if state:
                indicator.set_color('green')
            else:
                indicator.set_color('gray')
            indicator.figure.canvas.draw()
    
    def update_sensor_indicators(self, pin_states=None):
        """
        Met à jour les indicateurs de capteurs en fonction des états individuels des broches
        
        Args:
            pin_states: Dictionnaire avec les états des broches VR, VS, TO, TF
                       {'vr': bool, 'vs': bool, 'to': bool, 'tf': bool}
        """
        if pin_states is None:
            # État inconnu - tous les indicateurs éteints
            self.update_indicator('sensor_in_led', False)  # Vérin Rentré
            self.update_indicator('sensor_out_led', False) # Vérin Sorti
            self.update_indicator('trappe_fermee_led', False)  # Trappe Fermée
            self.update_indicator('trappe_ouverte_led', False) # Trappe Ouverte
            return
            
        # Update each indicator based on its corresponding pin state
        try:
            # Récupération des états avec valeurs par défaut à False si la clé n'existe pas
            vr_state = pin_states.get('vr', False)
            vs_state = pin_states.get('vs', False)
            tf_state = pin_states.get('tf', False)
            to_state = pin_states.get('to', False)
            
            # Mise à jour des voyants
            self.update_indicator('sensor_in_led', vr_state)       # Vérin Rentré
            self.update_indicator('sensor_out_led', vs_state)      # Vérin Sorti
            self.update_indicator('trappe_fermee_led', tf_state)   # Trappe Fermée
            self.update_indicator('trappe_ouverte_led', to_state)  # Trappe Ouverte
        except Exception as e:
            print(f"Error updating sensor indicators: {e}")
            # En cas d'erreur, on éteint tous les voyants
            self.update_indicator('sensor_in_led', False)
            self.update_indicator('sensor_out_led', False)
            self.update_indicator('trappe_fermee_led', False)
            self.update_indicator('trappe_ouverte_led', False)
    
    def update_detection_indicators(self, increase_detected, stabilized):
        """
        Met à jour les indicateurs de détection - utilise maintenant des lignes verticales pointillées 
        dans le graphique de conductance au lieu des indicateurs LED
        
        Args:
            increase_detected: Si une augmentation de conductance a été détectée
            stabilized: Si la conductance s'est stabilisée
        """
        # Les changements de détection sont maintenant gérés par les lignes verticales
        # dans update_conductance_plot à travers le dictionnaire events
        # Cette méthode est conservée pour la compatibilité avec le code existant
        pass
        
    def reset_reference_restabilization(self):
        """
        Réinitialise le temps de référence de restabilisation pour utiliser la prochaine restabilisation détectée
        """
        self.reference_restabilization_time = None
    
    def update_R0_display(self, value):
        """
        Met à jour l'affichage de R0
        
        Args:
            value: Valeur à afficher
        """
        ax_label = self.indicators['R0_display']
        ax_label.clear()
        ax_label.text(0.5, 0.5, f"{value}", ha="center", va="center", transform=ax_label.transAxes)
        ax_label.figure.canvas.draw()
        
    def update_regeneration_status(self, status, results=None):
        """
        Met à jour l'état du bouton de régénération en fonction de la progression de la régénération

        Args:
            status: Dictionnaire contenant l'état du protocole de régénération
                'active': bool - True si la régénération est en cours
                'step': int - Étape actuelle (0-3)
                'message': str - Message d'état
                'progress': float - Pourcentage de progression (0-100)
            results: Dictionnaire optionnel contenant les résultats de la régénération
                'delta_c': float - Delta C entre la stabilisation initiale et finale
                'carbon_mass': float - Masse de carbone calculée en µg
        """
        if 'regeneration' not in self.buttons:
            return

        regeneration_button = self.buttons['regeneration']
        cancel_button = self.buttons.get('cancel_regeneration')

        # Créer/mettre à jour l'attribut regeneration_active
        self.regeneration_active = status['active']

        if status['active']:
            # Regeneration in progress, display status
            regeneration_button.label.set_text(f"Regenerating... {status['progress']:.0f}%")
            regeneration_button.ax.set_facecolor('lightgray')
            regeneration_button.color = 'lightgray'
            regeneration_button.label.set_color('black')
            regeneration_button.active = False

            # Show cancel button
            if cancel_button:
                cancel_button.ax.set_visible(True)
                cancel_button.active = True

            # Désactiver les boutons CO2/T/H et Res/Temp pendant la régénération
            self.set_regeneration_buttons_state(False)
        else:
            # Regeneration not active, reset button
            regeneration_button.label.set_text("Protocole CO2")  # Nom corrigé
            regeneration_button.ax.set_facecolor('firebrick')
            regeneration_button.color = 'firebrick'
            regeneration_button.label.set_color('white')
            regeneration_button.active = True

            # Hide cancel button if no other protocol is running
            # Vérification si d'autres protocoles sont actifs avant de cacher le bouton cancel
            other_protocols_active = False
            for attr in ['conductance_regen_active', 'protocole_complet_active']:
                if hasattr(self, attr) and getattr(self, attr, False):
                    other_protocols_active = True
                    break

            if not other_protocols_active and cancel_button:
                cancel_button.ax.set_visible(False)
                cancel_button.active = False

            # Réactiver les boutons CO2/T/H et Res/Temp après la régénération
            # seulement si aucun autre protocole n'est actif
            if not other_protocols_active:
                self.set_regeneration_buttons_state(True)

            # Mettre à jour les afficheurs de résultats si disponibles
            if results is not None:
                delta_c = results.get('delta_c', 0)
                carbon_mass = results.get('carbon_mass', 0)
                percolation_time = results.get('percolation_time', 0)

                # Mise à jour de l'afficheur Delta C
                if 'delta_c_display' in self.indicators:
                    ax_delta_c = self.indicators['delta_c_display']
                    ax_delta_c.clear()
                    ax_delta_c.text(0.5, 0.5, f"Delta C: {delta_c:.2f} ppm",
                                   ha="center", va="center", transform=ax_delta_c.transAxes)
                    ax_delta_c.axis('off')

                # Mise à jour de l'afficheur de masse de carbone
                if 'carbon_mass_display' in self.indicators:
                    ax_carbon_mass = self.indicators['carbon_mass_display']
                    ax_carbon_mass.clear()
                    ax_carbon_mass.text(0.5, 0.5, f"Masse C: {carbon_mass:.2f} µg",
                                      ha="center", va="center", transform=ax_carbon_mass.transAxes)
                    ax_carbon_mass.axis('off')

                # Mise à jour de l'afficheur du temps de percolation
                if 'percolation_time_display' in self.indicators:
                    ax_percolation_time = self.indicators['percolation_time_display']
                    ax_percolation_time.clear()
                    # Toujours afficher en secondes, quelle que soit la durée
                    ax_percolation_time.text(0.5, 0.5, f"T perco: {percolation_time:.1f} s",
                                          ha="center", va="center", transform=ax_percolation_time.transAxes)
                    ax_percolation_time.axis('off')

        regeneration_button.ax.figure.canvas.draw_idle()

        # Redraw cancel button if it exists
        if cancel_button:
            cancel_button.ax.figure.canvas.draw_idle()
    
    def update_conductance_plot(self, timeList, conductanceList, events=None):
        """
        Met à jour le graphique de conductance
        
        Args:
            timeList: Liste des valeurs de temps
            conductanceList: Liste des valeurs de conductance
            events: Dictionnaire des événements à marquer sur le graphique
        """
        ax = self.axes['conductance']
        ax.clear()
        
        # Convert time to minutes if display_minutes is True
        if self.display_minutes and timeList:
            plot_time = [t / 60.0 for t in timeList]
            time_unit = 'min'
        else:
            plot_time = timeList
            time_unit = 's'
            
        ax.plot(plot_time, conductanceList, color='blue', linewidth=2)
        ax.set_xlabel(f'Temps ({time_unit})')
        ax.set_ylabel('Conductance (µS)')
        
        # Add event markers if provided
        has_markers = False
        if events:
            if 'increase_time' in events and events['increase_time']:
                event_time = events['increase_time'] / 60.0 if self.display_minutes else events['increase_time']
                ax.axvline(x=event_time, color='g', linestyle=':', linewidth=1.5, label='Début augmentation')
                has_markers = True
            
            if 'stabilization_time' in events and events['stabilization_time']:
                event_time = events['stabilization_time'] / 60.0 if self.display_minutes else events['stabilization_time']
                ax.axvline(x=event_time, color='r', linestyle=':', linewidth=1.5, label='Stabilisation')
                has_markers = True
            
            if 'max_slope_time' in events and events['max_slope_time']:
                event_time = events['max_slope_time'] / 60.0 if self.display_minutes else events['max_slope_time']
                ax.axvline(x=event_time, color='orange', linestyle=':', linewidth=1.5, label='Pente maximale')
                has_markers = True
                
            # Nouveaux marqueurs pour les étapes post-régénération
            if 'conductance_decrease_time' in events and events['conductance_decrease_time']:
                event_time = events['conductance_decrease_time'] / 60.0 if self.display_minutes else events['conductance_decrease_time']
                ax.axvline(x=event_time, color='purple', linestyle=':', linewidth=1.5, label='Décroissance < 5 µS')
                has_markers = True

            if 'post_regen_stability_time' in events and events['post_regen_stability_time']:
                event_time = events['post_regen_stability_time'] / 60.0 if self.display_minutes else events['post_regen_stability_time']
                ax.axvline(x=event_time, color='cyan', linestyle=':', linewidth=1.5, label='Restabilisation post-régén')
                has_markers = True

            # Marqueur pour la première stabilité du protocole complet
            if 'first_stability_time' in events and events['first_stability_time']:
                event_time = events['first_stability_time'] / 60.0 if self.display_minutes else events['first_stability_time']
                ax.axvline(x=event_time, color='magenta', linestyle=':', linewidth=1.5, label='Première stabilité')
                has_markers = True
            
            # Afficher la légende seulement s'il y a des marqueurs
            if has_markers:
                ax.legend()
        
        self.fig.canvas.draw()
    
    def update_co2_temp_humidity_plot(self, timestamps_co2, values_co2, timestamps_temp, values_temp, 
                                    timestamps_humidity, values_humidity, regeneration_timestamps=None):
        """
        Met à jour le graphique de CO2, température et humidité
        
        Args:
            timestamps_co2: Liste des horodatages CO2
            values_co2: Liste des valeurs de CO2
            timestamps_temp: Liste des horodatages de température
            values_temp: Liste des valeurs de température
            timestamps_humidity: Liste des horodatages d'humidité
            values_humidity: Liste des valeurs d'humidité
            regeneration_timestamps: Dictionnaire des horodatages pour les événements clés du protocole de régénération
        """
        ax = self.axes['co2']
        ax_right = self.axes['co2_right']
        
        # Convert time to minutes if display_minutes is True
        if self.display_minutes:
            plot_timestamps_co2 = [t / 60.0 for t in timestamps_co2] if timestamps_co2 else []
            plot_timestamps_temp = [t / 60.0 for t in timestamps_temp] if timestamps_temp else []
            plot_timestamps_humidity = [t / 60.0 for t in timestamps_humidity] if timestamps_humidity else []
            time_unit = 'min'
        else:
            plot_timestamps_co2 = timestamps_co2
            plot_timestamps_temp = timestamps_temp
            plot_timestamps_humidity = timestamps_humidity
            time_unit = 's'
        
        ax.clear()
        ax.plot(plot_timestamps_co2, values_co2, label='CO2 (ppm)', color='tab:blue')
        ax.set_xlabel(f'Temps ({time_unit})')
        ax.set_ylabel('CO2 (ppm)', color='tab:blue')
        ax.tick_params(axis='y', labelcolor='tab:blue')
        
        ax_right.clear()
        temperature_plot, = ax_right.plot(plot_timestamps_temp, values_temp, label='Température (°C)', color='tab:red')
        humidity_plot, = ax_right.plot(plot_timestamps_humidity, values_humidity, label='Humidité (%)', color='tab:green')
        ax_right.set_ylabel('')
        ax_right.tick_params(axis='y', labelcolor='black')
        ax_right.legend(loc='center right', handles=[temperature_plot, humidity_plot])
        
        # Ajouter des pointillés verticaux pour les événements clés de régénération
        if regeneration_timestamps:
            # Afficher une ligne verticale lorsque R0 a été actualisé
            if regeneration_timestamps.get('r0_actualized') is not None:
                r0_time = regeneration_timestamps['r0_actualized'] / 60.0 if self.display_minutes else regeneration_timestamps['r0_actualized']
                ax.axvline(x=r0_time, color='purple', linestyle='--', linewidth=1.5, label='R0 actualisé')
            
            # Afficher une ligne verticale pour le début de la vérification de la stabilité CO2
            if regeneration_timestamps.get('co2_stability_started') is not None:
                start_time = regeneration_timestamps['co2_stability_started'] / 60.0 if self.display_minutes else regeneration_timestamps['co2_stability_started']
                ax.axvline(x=start_time, color='green', linestyle='--', linewidth=1.5, label='Début stabilité CO2')
            
            # Afficher une ligne verticale pour la confirmation de stabilité CO2
            if regeneration_timestamps.get('co2_stability_achieved') is not None:
                end_time = regeneration_timestamps['co2_stability_achieved'] / 60.0 if self.display_minutes else regeneration_timestamps['co2_stability_achieved']
                ax.axvline(x=end_time, color='orange', linestyle='--', linewidth=1.5, label='Stabilité CO2 atteinte')
            
            # Afficher une ligne verticale pour l'augmentation de CO2 après Tcons=700
            if regeneration_timestamps.get('co2_increase_detected') is not None:
                increase_time = regeneration_timestamps['co2_increase_detected'] / 60.0 if self.display_minutes else regeneration_timestamps['co2_increase_detected']
                ax.axvline(x=increase_time, color='magenta', linestyle='--', linewidth=1.5, label='Augmentation CO2 détectée')
            
            # Afficher une ligne verticale pour le pic de CO2 (fin de montée)
            if regeneration_timestamps.get('co2_peak_reached') is not None:
                peak_time = regeneration_timestamps['co2_peak_reached'] / 60.0 if self.display_minutes else regeneration_timestamps['co2_peak_reached']
                ax.axvline(x=peak_time, color='red', linestyle='--', linewidth=1.5, label='Pic de CO2 atteint')
                
            # Afficher une ligne verticale pour la restabilisation du CO2
            if regeneration_timestamps.get('co2_restabilized') is not None:
                restab_time = regeneration_timestamps['co2_restabilized'] / 60.0 if self.display_minutes else regeneration_timestamps['co2_restabilized']
                ax.axvline(x=restab_time, color='blue', linestyle='--', linewidth=1.5, label='CO2 restabilisé')
                
                # Si nous avons une nouvelle restabilisation, mettre à jour la référence
                if self.reference_restabilization_time is None:
                    self.reference_restabilization_time = regeneration_timestamps['co2_restabilized']
            
            # Ajouter la ligne de référence de la recherche de restabilisation si disponible
            if regeneration_timestamps.get('co2_restabilization_start_time') is not None:
                restab_start_time = regeneration_timestamps['co2_restabilization_start_time'] / 60.0 if self.display_minutes else regeneration_timestamps['co2_restabilization_start_time']
                ax.axvline(x=restab_start_time, color='purple', linestyle='--', linewidth=1.5, label='Début recherche restabilisation')
            
            # Ajouter une légende si des événements sont présents
            if any(v is not None for v in regeneration_timestamps.values()):
                ax.legend(loc='upper left')
        
        self.fig.canvas.draw()
    
    def update_res_temp_plot(self, timestamps, temperatures, tcons_values, regeneration_timestamps=None):
        """
        Met à jour le graphique de température de résistance
        
        Args:
            timestamps: Liste des horodatages
            temperatures: Liste des valeurs de température
            tcons_values: Liste des valeurs de Tcons
            regeneration_timestamps: Dictionnaire des horodatages pour les événements clés du protocole de régénération
        """
        ax = self.axes['res_temp']
        ax.clear()
        
        # Convert time to minutes if display_minutes is True
        if self.display_minutes and timestamps:
            plot_timestamps = [t / 60.0 for t in timestamps]
            time_unit = 'min'
        else:
            plot_timestamps = timestamps
            time_unit = 's'
            
        ax.plot(plot_timestamps, temperatures, label='Température mesurée', color='tab:red')
        ax.plot(plot_timestamps, tcons_values, label='Tcons', color='tab:blue')
        ax.legend()
        ax.set_xlabel(f'Temps ({time_unit})')
        ax.set_ylabel('Température °C')
        
        # Ajouter des pointillés verticaux pour les événements clés de régénération
        if regeneration_timestamps:
            # Afficher une ligne verticale lorsque R0 a été actualisé
            if regeneration_timestamps.get('r0_actualized') is not None:
                r0_time = regeneration_timestamps['r0_actualized'] / 60.0 if self.display_minutes else regeneration_timestamps['r0_actualized']
                ax.axvline(x=r0_time, color='purple', linestyle='--', linewidth=1.5, label='R0 actualisé')
            
            # Afficher une ligne verticale pour le début de la vérification de la stabilité CO2
            if regeneration_timestamps.get('co2_stability_started') is not None:
                start_time = regeneration_timestamps['co2_stability_started'] / 60.0 if self.display_minutes else regeneration_timestamps['co2_stability_started']
                ax.axvline(x=start_time, color='green', linestyle='--', linewidth=1.5, label='Début stabilité CO2')
            
            # Afficher une ligne verticale pour la confirmation de stabilité CO2
            if regeneration_timestamps.get('co2_stability_achieved') is not None:
                end_time = regeneration_timestamps['co2_stability_achieved'] / 60.0 if self.display_minutes else regeneration_timestamps['co2_stability_achieved']
                ax.axvline(x=end_time, color='orange', linestyle='--', linewidth=1.5, label='Stabilité CO2 atteinte')
            
        self.fig.canvas.draw()
    
    def update_raz_buttons_visibility(self, measurement_states):
        """
        Met à jour la visibilité des boutons de réinitialisation en fonction des états de mesure

        Args:
            measurement_states: Dictionnaire avec les états de mesure
        """
        if self.mode == "manual":
            # S'assurer que tous les états sont mis à jour, pas seulement ceux fournis
            updated_states = {}

            # Conserver les états précédents pour les mesures non spécifiées
            for measurement in ['conductance', 'co2_temp_humidity', 'res_temp']:
                button_name = f"raz_{measurement}"
                if button_name in self.buttons:
                    # État par défaut: bouton visible (mesure inactive)
                    current_state = not self.buttons[button_name].ax.get_visible() if self.buttons[button_name].ax.get_visible() is not None else False
                    # Mettre à jour uniquement si l'état est fourni
                    updated_states[measurement] = measurement_states.get(measurement, current_state)

            # Appliquer les mises à jour
            for measurement, state in updated_states.items():
                button_name = f"raz_{measurement}"
                if button_name in self.buttons:
                    self.buttons[button_name].ax.set_visible(not state)
        else:
            self.buttons['raz_auto'].ax.set_visible(not measurement_states.get('auto', False))

        self.fig.canvas.draw()
    
    def deactivate_movement_buttons(self):
        """Désactive les boutons push/open et retract/close"""
        for btn_name in ['push_open', 'retract_close']:
            if btn_name in self.buttons:
                button = self.buttons[btn_name]
                button.active = False
                button.ax.set_facecolor('lightgray')
                button.color = 'lightgray'
                button.ax.figure.canvas.draw_idle()
    
    def set_regeneration_buttons_state(self, active):
        """
        Active ou désactive les boutons qui doivent être indisponibles pendant la régénération
        
        Args:
            active: True pour activer les boutons, False pour les désactiver
        """
        # Liste des boutons à désactiver pendant la régénération
        buttons_to_control = ['co2_temp_humidity', 'res_temp', 'set_Tcons']
        
        for btn_name in buttons_to_control:
            if btn_name in self.buttons:
                button = self.buttons[btn_name]
                
                # S'assurer que le bouton a l'attribut 'active'
                if not hasattr(button, 'active'):
                    button.active = True
                
                # Définir l'état actif/inactif
                button.active = active
                
                # Mettre à jour l'apparence du bouton
                if active:
                    button.ax.set_facecolor('white')
                    button.color = 'white'
                else:
                    button.ax.set_facecolor('lightgray')
                    button.color = 'lightgray'
                
                # Redessiner le bouton
                button.ax.figure.canvas.draw_idle()
    
    def configure_measurement_panels(self, measure_conductance=True, measure_co2=True, measure_regen=True):
        """
        Configure les panneaux de mesure visibles et réorganise la mise en page
        
        Args:
            measure_conductance: Si le panneau de conductance doit être affiché
            measure_co2: Si le panneau CO2/temp/humidité doit être affiché
            measure_regen: Si le panneau de température de régénération doit être affiché
        """
        # Approche plus simple: ajuster la position relative des panneaux
        # sans recréer la figure complète
        
        # Récupérer tous les axes de la figure
        active_axes = []
        if measure_conductance and 'conductance' in self.axes:
            self.axes['conductance'].set_visible(True)
            active_axes.append(self.axes['conductance'])
        else:
            if 'conductance' in self.axes:
                self.axes['conductance'].set_visible(False)
        
        if measure_co2 and 'co2' in self.axes and 'co2_right' in self.axes:
            self.axes['co2'].set_visible(True)
            self.axes['co2_right'].set_visible(True)
            active_axes.append(self.axes['co2'])
        else:
            if 'co2' in self.axes:
                self.axes['co2'].set_visible(False)
            if 'co2_right' in self.axes:
                self.axes['co2_right'].set_visible(False)
        
        if measure_regen and 'res_temp' in self.axes:
            self.axes['res_temp'].set_visible(True)
            active_axes.append(self.axes['res_temp'])
        else:
            if 'res_temp' in self.axes:
                self.axes['res_temp'].set_visible(False)
        
        # Ajuster la taille des axes visibles
        if active_axes:
            # Calculer la hauteur de chaque panneau (en tenant compte des marges)
            n_active = len(active_axes)
            
            # Recalculer les positions de chaque axe visible (pour tout nombre de panneaux)
            height_per_panel = 0.75 / n_active
            bottom_margin = 0.15  # Marge inférieure
            
            for i, ax in enumerate(active_axes):
                # Position y (de bas en haut)
                bottom = bottom_margin + (n_active - i - 1) * height_per_panel
                # Définir la nouvelle position [left, bottom, width, height]
                ax.set_position([0.1, bottom, 0.8, height_per_panel * 0.95])
                
                # Si c'est un axe CO2, ajuster aussi l'axe droit
                if ax == self.axes.get('co2') and 'co2_right' in self.axes:
                    self.axes['co2_right'].set_position([0.1, bottom, 0.8, height_per_panel * 0.95])
        
        # Cacher les boutons pour les panneaux masqués et les fonctionnalités non disponibles
        for button_name, button in self.buttons.items():
            # Boutons liés aux mesures de conductance
            if button_name in ['conductance', 'raz_conductance']:
                button.ax.set_visible(measure_conductance)
            
            # Boutons liés aux mesures de CO2
            elif button_name in ['co2_temp_humidity', 'raz_co2_temp_humidity']:
                button.ax.set_visible(measure_co2)
            
            # Boutons liés aux mesures de température/résistance
            elif button_name in ['res_temp', 'raz_res_temp']:
                button.ax.set_visible(measure_regen)
            
            # Boutons liés à R0 et Tcons (dépendent de la régénération)
            elif button_name in ['set_R0', 'update_R0', 'set_Tcons']:
                button.ax.set_visible(measure_regen)
                
            # Le bouton "Start/Stop Tout" est toujours visible si au moins une mesure est disponible
            elif button_name == 'start_all':
                button.ax.set_visible(measure_conductance or measure_co2 or measure_regen)
        
        # Masquer également les textboxes et zones d'affichage liées à la régénération
        if not measure_regen:
            for textbox_name in ['R0', 'Tcons']:
                if textbox_name in self.textboxes:
                    # Pour les zones de texte, les désactiver mais ne pas les cacher complètement
                    textbox = self.textboxes[textbox_name]
                    textbox.set_val("")  # Effacer le contenu
                    textbox.color = 'lightgray'  # Griser le fond
                    textbox.eventson = False  # Désactiver les événements
            
            # Masquer l'affichage R0
            if 'R0_display' in self.indicators:
                # Effacer le texte de l'affichage R0
                ax_label = self.indicators['R0_display']
                ax_label.clear()
                ax_label.text(0.5, 0.5, "N/A", ha="center", va="center", transform=ax_label.transAxes, color='gray')
        else:
            # Réactiver les zones de texte si la régénération est active
            for textbox_name in ['R0', 'Tcons']:
                if textbox_name in self.textboxes:
                    textbox = self.textboxes[textbox_name]
                    textbox.color = 'white'  # Remettre en blanc
                    textbox.eventson = True  # Réactiver les événements
        
        # Redraw
        self.fig.canvas.draw()
    
    def on_time_unit_change(self, label):
        """
        Gère le changement d'affichage des unités de temps (secondes/minutes)
        
        Args:
            label: Étiquette du bouton radio sélectionné
        """
        if label == 'Minutes':
            self.display_minutes = True
        else:  # 'Secondes'
            self.display_minutes = False
            
        # Force redraw of all plots with the new time unit
        # This is normally done by the parent application during the next update cycle
            
    def update_backup_status(self, status_info):
        """
        Met à jour l'indicateur de sauvegarde de secours
        
        Args:
            status_info: Dictionnaire contenant les informations sur la dernière sauvegarde
                'time': float - Timestamp de la dernière sauvegarde
                'success': bool - True si la sauvegarde a réussi
                'reason': str - Raison de la sauvegarde
        """
        if 'backup_status' not in self.indicators:
            return
            
        ax = self.indicators['backup_status']
        ax.clear()
        
        if not status_info or status_info.get('time') is None:
            ax.text(0.5, 0.5, "Dernière sauvegarde: --:--:--", 
                   fontsize=7, ha="center", va="center", transform=ax.transAxes)
            ax.axis('off')
            return
        
        # Formatage de l'heure
        timestamp = status_info.get('time')
        time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
        
        # Couleur en fonction du succès
        color = 'green' if status_info.get('success', False) else 'red'
        
        # Texte de statut
        ax.text(0.5, 0.5, f"Dernière sauvegarde: {time_str}", 
               fontsize=7, ha="center", va="center", color=color, transform=ax.transAxes)
        ax.axis('off')
        
        # Forcer le rafraîchissement
        self.fig.canvas.draw_idle()
    
    def close(self):
        """Ferme la fenêtre du graphique"""
        plt.close(self.fig)
    
    def show(self):
        """Affiche la fenêtre du graphique"""
        plt.show()
        
    def update_add_device_buttons(self, available_devices=None):
        """
        Met à jour l'état des boutons d'ajout d'appareils en fonction des appareils déjà connectés
        
        Args:
            available_devices: Dictionnaire indiquant les appareils déjà connectés
                {'arduino': bool, 'regen': bool, 'keithley': bool}
        """
        if available_devices:
            self.available_devices.update(available_devices)
        
        # Paramètres pour le positionnement
        button_width = 0.1
        button_height = 0.03
        spacing = 0.01  # Espacement vertical entre les boutons
        title_x = 0.01
        title_width = 0.12
        title_y = 0.97
        button_x = title_x + title_width/2 - button_width/2  # Centré sous le titre
        
        # Calculer quels boutons doivent être visibles
        visible_buttons = {}
        for device_type in self.add_device_button_info:
            # Le bouton est visible si l'appareil n'est pas connecté
            is_visible = not self.available_devices.get(device_type, False)
            visible_buttons[device_type] = is_visible
        
        # Recalculer les indices pour les boutons visibles
        visible_count = 0
        for device_type, info in self.add_device_button_info.items():
            if visible_buttons[device_type]:
                # Mettre à jour l'index visible
                info['visible_index'] = visible_count
                visible_count += 1
        
        # Mettre à jour la position et la visibilité des boutons
        for device_type, button in self.add_device_buttons.items():
            is_visible = visible_buttons[device_type]
            button.ax.set_visible(is_visible)
            
            if is_visible:
                # Calculer la nouvelle position Y basée sur l'index visible
                visible_index = self.add_device_button_info[device_type]['visible_index']
                new_y_pos = title_y - 0.03 - visible_index * (button_height + spacing)
                
                # Appliquer la nouvelle position
                button.ax.set_position([button_x, new_y_pos, button_width, button_height])
        
        # Forcer le redessinage
        if self.fig:
            self.fig.canvas.draw_idle()
    
    def connect_add_device_button(self, device_type, callback):
        """
        Connecte un callback au bouton d'ajout d'appareil
        
        Args:
            device_type: Type d'appareil ('arduino', 'regen' ou 'keithley')
            callback: Fonction à appeler lorsque le bouton est cliqué
        """
        if device_type in self.add_device_buttons:
            # Désactiver le bouton après clic pour éviter les clics multiples
            def wrapped_callback(event):
                # Désactiver le bouton immédiatement
                button = self.add_device_buttons[device_type]
                button.active = False
                button.ax.set_facecolor('lightgray')
                button.color = 'lightgray'
                self.fig.canvas.draw_idle()
                
                # Appeler le callback
                callback(event)
            
            self.add_device_buttons[device_type].on_clicked(wrapped_callback)
            
    def update_protocol_button_states(self, measure_co2_temp_humidity_active, measure_conductance_active, measure_res_temp_active):
        """
        Met à jour l'état des boutons de protocole en fonction des mesures actives
        - Le bouton de protocole CO2 doit être cliquable si CO2 et Tcons/Tmes sont actifs
        - Le bouton de protocole de conductance doit être cliquable si Conductance et Tcons/Tmes sont actifs
        - Le bouton de protocole complet doit être cliquable si les trois mesures sont actives ET que l'init a été effectué

        Args:
            measure_co2_temp_humidity_active: Si la mesure de CO2/température/humidité est active
            measure_conductance_active: Si la mesure de conductance est active
            measure_res_temp_active: Si la mesure de résistance/température est active
        """
        # Mémoriser les états des mesures pour pouvoir y accéder plus tard
        self.measure_co2_temp_humidity_active = measure_co2_temp_humidity_active
        self.measure_conductance_active = measure_conductance_active
        self.measure_res_temp_active = measure_res_temp_active

        # Vérifier si l'initialisation a été effectuée (boutons push_open et retract_close actifs)
        init_done = (
            'push_open' in self.buttons and
            hasattr(self.buttons['push_open'], 'active') and
            self.buttons['push_open'].active
        )

         # Protocole CO2 - nécessite CO2 et température
        co2_protocol_ready = measure_co2_temp_humidity_active and measure_res_temp_active
        self._update_button_state('regeneration', co2_protocol_ready, 'firebrick')

        # Protocole Conductance - nécessite conductance et température
        cond_protocol_ready = measure_conductance_active and measure_res_temp_active
        self._update_button_state('conductance_regen', cond_protocol_ready, 'darkblue')

        # Protocole Complet - nécessite les 3 mesures ET init
        full_protocol_ready = (measure_co2_temp_humidity_active and
                            measure_conductance_active and
                            measure_res_temp_active and
                            init_done)
        self._update_button_state('protocole_complet', full_protocol_ready, 'darkgreen')

        # Toujours montrer le bouton Cancel si un protocole est actif
        self._update_cancel_button_visibility()

    def _update_button_state(self, button_name, is_active, active_color):
        """Met à jour l'état d'un bouton de protocole"""
        if button_name in self.buttons:
            button = self.buttons[button_name]
            button.active = is_active
            if is_active:
                button.ax.set_facecolor(active_color)
                button.color = active_color
                button.label.set_color('white')
            else:
                button.ax.set_facecolor('lightgray')
                button.color = 'lightgray'
                button.label.set_color('darkgray')
            button.ax.figure.canvas.draw_idle()

    def _update_cancel_button_visibility(self):
        """Met à jour la visibilité du bouton Cancel"""
        if 'cancel_regeneration' in self.buttons:
            cancel_button = self.buttons['cancel_regeneration']
            # Montrer le bouton si un protocole est actif
            # Vérifier d'abord si les attributs existent dans la classe
            protocol_active = False

            # Vérifier si protocole_complet_active est à True
            if hasattr(self, 'protocole_complet_active') and self.protocole_complet_active:
                protocol_active = True
                # Repositionner le bouton cancel au-dessus du bouton protocole_complet
                if 'protocole_complet' in self.buttons:
                    protocole_complet_button = self.buttons['protocole_complet']
                    if hasattr(protocole_complet_button, 'ax') and hasattr(protocole_complet_button.ax, 'get_position'):
                        button_position = protocole_complet_button.ax.get_position()
                        cancel_position = cancel_button.ax.get_position()
                        # Centrer le bouton cancel au-dessus du protocole complet
                        new_x = button_position.x0 + button_position.width/2 - cancel_position.width/2
                        new_cancel_position = [new_x, cancel_position.y0, cancel_position.width, cancel_position.height]
                        cancel_button.ax.set_position(new_cancel_position)

                        # Assurer que le bouton cancel est au-dessus des autres éléments (z-order)
                        # Plus la valeur est élevée, plus l'élément est au-dessus
                        cancel_button.ax.set_zorder(10000)  # Valeur très élevée pour être au-dessus de tous les autres éléments

                        # Déplacer légèrement le bouton pour qu'il soit plus visible (décalage vers le haut)
                        new_cancel_position[1] += 0.02  # Augmenter la position Y pour l'éloigner du bouton protocole
                        cancel_button.ax.set_position(new_cancel_position)

                        # Changer la couleur pour qu'il soit plus visible
                        cancel_button.ax.set_facecolor('orangered')  # Couleur plus vive
                        cancel_button.color = 'orangered'
                        cancel_button.label.set_color('white')  # Texte blanc pour meilleur contraste

            # Vérifier les autres protocoles
            if not protocol_active:
                for protocol_name in ['regeneration_active', 'conductance_regen_active']:
                    if hasattr(self, protocol_name) and getattr(self, protocol_name, False):
                        protocol_active = True
                        break

            # Vérifier également si le protocole est actif dans la barre de progression
            if not protocol_active and 'protocol_progress' in self.indicators and self.indicators['protocol_progress'].get_visible():
                protocol_active = True

            cancel_button.ax.set_visible(protocol_active)
            cancel_button.active = protocol_active
            cancel_button.ax.figure.canvas.draw_idle()
        
    def update_regeneration_status(self, status_info, regeneration_results=None):
        """
        Met à jour l'affichage du statut de régénération/protocole

        Args:
            status_info: Dictionnaire contenant les informations de statut
                'active': Bool - Si le protocole est actif
                'step': Int - Étape courante du protocole
                'message': Str - Message à afficher
                'progress': Float - Progression (0-100)
            regeneration_results: Résultats de régénération (non utilisé dans cette fonction)
        """
        # Mettre à jour l'état de la barre de progression commune
        if 'protocol_progress' in self.indicators:
            ax_progress = self.indicators['protocol_progress']
            progress = status_info.get('progress', 0)
            message = status_info.get('message', '')

            if status_info.get('active', False):
                # Afficher la barre de progression
                ax_progress.set_visible(True)

                # Mettre à jour la barre de progrès
                ax_progress.clear()
                ax_progress.barh(0, progress, color='green', height=0.8)
                ax_progress.set_xlim(0, 100)
                ax_progress.set_ylim(-0.5, 0.5)
                ax_progress.text(50, 0, f"{progress:.0f}%", ha='center', va='center', fontsize=9, color='black', fontweight='bold')

                # Ajouter un titre qui indique le type de protocole en cours
                protocol_type_info = status_info.get('protocol_type', '')

                if protocol_type_info == 'full':
                    protocol_type = "Complet"
                else:
                    protocol_type = "CO2" if "regeneration" in message.lower() else "Conductance"

                ax_progress.set_title(f"Protocole {protocol_type} : {message}", fontsize=8, pad=2)

                # Rendre le bouton cancel visible pour tous les protocoles
                if 'cancel_regeneration' in self.buttons:
                    cancel_button = self.buttons['cancel_regeneration']
                    cancel_button.ax.set_visible(True)
                    cancel_button.active = True

                
                    # Forcer le redessinage du bouton cancel
                    cancel_button.ax.figure.canvas.draw_idle()

                # Enlever les axes
                ax_progress.set_xticks([])
                ax_progress.set_yticks([])
                ax_progress.set_frame_on(True)
            else:
                # Cacher la barre de progression si le protocole est désactivé
                ax_progress.set_visible(False)

                # Cacher le bouton cancel seulement si aucun protocole n'est actif
                if 'cancel_regeneration' in self.buttons:
                    # Vérifier si un autre protocole est encore actif
                    other_protocol_active = False
                    for attr in ['regeneration_active', 'conductance_regen_active', 'protocole_complet_active']:
                        if hasattr(self, attr) and getattr(self, attr, False):
                            other_protocol_active = True
                            break

                    if not other_protocol_active:
                        self.buttons['cancel_regeneration'].ax.set_visible(False)
                        self.buttons['cancel_regeneration'].active = False
                        self.buttons['cancel_regeneration'].ax.figure.canvas.draw_idle()

            # Actualiser la barre de progression
            ax_progress.figure.canvas.draw_idle()

    def set_close_callback(self, callback):
        """
        Configure un callback pour quand la fenêtre est fermée via le bouton X

        Args:
            callback: Fonction à appeler quand la fenêtre est fermée
        """
        # Obtient le gestionnaire de fenêtre pour se connecter à son événement de fermeture
        try:
            if self.fig and self.fig.canvas and self.fig.canvas.manager:
                manager = self.fig.canvas.manager
                
                # Determine the backend and connect appropriately
                backend = plt.get_backend().lower()
                
                if 'qt' in backend:
                    # For Qt backends
                    window = manager.window
                    if hasattr(window, 'closeEvent'):
                        # Store original closeEvent
                        original_close_event = window.closeEvent
                        
                        def new_close_event(event):
                            """
                            La fonction def new_close_event(event): sert à intercepter l'événement de fermeture de la fenêtre
                            """
                            # Run our callback first
                            if callback:
                                callback(event)
                            # Then call the original handler
                            original_close_event(event)
                            
                        window.closeEvent = new_close_event
                        
                elif 'tk' in backend:
                    # For Tkinter backend
                    if hasattr(manager, 'window'):
                        window = manager.window
                        window.protocol("WM_DELETE_WINDOW", callback)
                        
                elif 'wx' in backend:
                    # For wxPython backend
                    if hasattr(manager, 'frame'):
                        import wx
                        frame = manager.frame
                        
                        # Bind to EVT_CLOSE
                        def on_close(event):
                            """
                            Fonction de gestion d’événement utilisée uniquement pour le backend wxPython
                            """
                            callback(event)
                            event.Skip()
                            
                        frame.Bind(wx.EVT_CLOSE, on_close)
                
                # Add fallback for other backends if needed
                # Suppression du message de configuration du backend
                
        except Exception as e:
            print(f"Could not set close callback: {e}")