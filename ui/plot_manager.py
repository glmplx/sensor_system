"""
Plot manager for the sensor system UI
"""

import sys
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, TextBox, RadioButtons

class PlotManager:
    """Manages matplotlib plots and UI elements"""
    
    def __init__(self, mode="manual"):
        """
        Initialize the plot manager
        
        Args:
            mode: "manual" or "auto" mode
        """
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
        
        # Variable to track time unit display preference (default: seconds)
        self.display_minutes = False
        
        # Reference for CO2 restabilization time
        self.reference_restabilization_time = None
        
        # Setup figure and plots
        self.setup_plots()
    
    def setup_plots(self):
        """Set up the figure and axes for plots"""
        self.fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 18))
        
        # Set window size/position based on how we're running
        try:
            manager = plt.get_current_fig_manager()
            
            # Check if running as executable
            if getattr(sys, 'frozen', False):
                # For executable, use a more conservative size and try to center it
                width, height = 1400, 800  # More conservative size
                
                # Try different methods to adjust the window
                try:
                    # Try to center the window - for Tkinter
                    if hasattr(manager, 'canvas') and hasattr(manager.canvas, 'manager') and hasattr(manager.canvas.manager, 'window'):
                        root = manager.canvas.manager.window
                        # First configure the window size
                        root.geometry(f"{width}x{height}")
                        
                        # Then center it after a short delay
                        def center_window():
                            screen_width = root.winfo_screenwidth()
                            screen_height = root.winfo_screenheight()
                            pos_x = (screen_width // 2) - (width // 2)
                            pos_y = (screen_height // 2) - (height // 2)
                            root.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
                        
                        # Schedule the centering for after the window is created
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
        """Set up buttons for manual mode"""
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
        
        # Regeneration buttons (above set Tcons, left of retract/close)
        # Décalage du bouton de régénération vers la droite et réduction de largeur
        ax_button_regeneration = plt.axes([0.53, 0.06, button_width * 0.9, button_height])
        regeneration_button = Button(ax_button_regeneration, 'Start Regeneration', color='firebrick')
        regeneration_button.ax.set_facecolor('firebrick')
        regeneration_button.color = 'firebrick'
        regeneration_button.label.set_color('white')
        self.buttons['regeneration'] = regeneration_button
        
        # Bouton d'annulation de régénération (initialement caché)
        ax_button_cancel_regen = plt.axes([0.63, 0.06, button_width * 0.7, button_height])
        cancel_regen_button = Button(ax_button_cancel_regen, 'Cancel', color='orange')
        cancel_regen_button.ax.set_facecolor('orange')
        cancel_regen_button.color = 'orange'
        cancel_regen_button.label.set_color('black')
        cancel_regen_button.ax.set_visible(False)  # Initialement caché
        self.buttons['cancel_regeneration'] = cancel_regen_button
        
        # Tcons input and button
        ax_textbox_Tcons = plt.axes([0.60, 0.01, button_width/2, button_height])
        self.textboxes['Tcons'] = TextBox(ax_textbox_Tcons, 'Tcons', initial='')
        
        ax_button_Tcons = plt.axes([0.67, 0.01, button_width/2, button_height])
        self.buttons['set_Tcons'] = Button(ax_button_Tcons, 'Set Tcons')
        self.buttons['set_Tcons'].active = True  # Définir active=True par défaut
    
    def setup_auto_buttons(self):
        """Set up buttons for auto mode"""
        button_width = 0.1
        button_height = 0.04
        
        # Auto start/stop button
        ax_button_auto = plt.axes([0.02, 0.01, button_width, button_height])
        self.buttons['auto'] = Button(ax_button_auto, 'Start/Stop Auto.')
        
        # Reset button for auto mode
        ax_button_raz_auto = plt.axes([0.14, 0.01, button_width, button_height])
        self.buttons['raz_auto'] = Button(ax_button_raz_auto, 'RAZ Auto.')
        
        # Regeneration buttons (ajouté pour le mode auto aussi)
        # Décalage du bouton de régénération vers la droite et réduction de largeur
        ax_button_regeneration = plt.axes([0.53, 0.06, button_width * 0.9, button_height])
        regeneration_button = Button(ax_button_regeneration, 'Start Regeneration', color='firebrick')
        regeneration_button.ax.set_facecolor('firebrick')
        regeneration_button.color = 'firebrick'
        regeneration_button.label.set_color('white')
        self.buttons['regeneration'] = regeneration_button
        
        # Bouton d'annulation de régénération (initialement caché)
        ax_button_cancel_regen = plt.axes([0.63, 0.06, button_width * 0.7, button_height])
        cancel_regen_button = Button(ax_button_cancel_regen, 'Cancel', color='orange')
        cancel_regen_button.ax.set_facecolor('orange')
        cancel_regen_button.color = 'orange'
        cancel_regen_button.label.set_color('black')
        cancel_regen_button.ax.set_visible(False)  # Initialement caché
        self.buttons['cancel_regeneration'] = cancel_regen_button
    
    def setup_common_elements(self):
        """Set up elements common to both modes"""
        button_width = 0.1
        button_height = 0.04
        
        # Time unit selection radio buttons (right side of trappe indicators)
        ax_radio_time_unit = plt.axes([0.50, 0.91, 0.12, 0.05])
        self.radiobuttons['time_unit'] = RadioButtons(ax_radio_time_unit, ('Secondes', 'Minutes'), active=0)
        ax_radio_time_unit.set_title('Unités de temps', fontsize=9)
        
        # R0 textbox and buttons
        ax_textbox_R0 = plt.axes([0.45, 0.01, button_width/2, button_height])
        self.textboxes['R0'] = TextBox(ax_textbox_R0, 'R0', initial='')
        
        ax_button_update_R0 = plt.axes([0.38, 0.06, button_width/2, button_height])
        self.buttons['update_R0'] = Button(ax_button_update_R0, 'Update')
        
        ax_button_R0 = plt.axes([0.52, 0.01, button_width/2, button_height])
        self.buttons['set_R0'] = Button(ax_button_R0, 'Set R0')
        
        # Push/Open and Retract/Close buttons (grayed out initially)
        ax_button_PushOpen = plt.axes([0.75, 0.01, button_width, button_height])
        push_open_button = Button(ax_button_PushOpen, 'Push/Open', color='lightgray')
        push_open_button.ax.set_facecolor('lightgray')
        push_open_button.color = 'lightgray'
        push_open_button.active = False  # Custom flag to track if button is usable
        self.buttons['push_open'] = push_open_button
        
        ax_button_RetractClose = plt.axes([0.75, 0.06, button_width, button_height])
        retract_close_button = Button(ax_button_RetractClose, 'Retract/Close', color='lightgray')
        retract_close_button.ax.set_facecolor('lightgray')
        retract_close_button.color = 'lightgray'
        retract_close_button.active = False  # Custom flag to track if button is usable
        self.buttons['retract_close'] = retract_close_button
        
        # Quit button
        ax_button_quit = plt.axes([0.89, 0.01, button_width, button_height])
        self.buttons['quit'] = Button(ax_button_quit, 'Quitter')
        
        # Status indicators
        self.setup_indicators()
        
        # R0 display
        ax_label = plt.axes([0.38, 0.01, button_width/2, button_height])
        self.indicators['R0_display'] = ax_label
        
        # Delta C display - à droite du sélecteur d'unités de temps
        ax_delta_c = plt.axes([0.65, 0.92, button_width/1.5, button_height])
        ax_delta_c.text(0.5, 0.5, "Delta C: 0 ppm", ha="center", va="center", transform=ax_delta_c.transAxes)
        ax_delta_c.axis('off')
        self.indicators['delta_c_display'] = ax_delta_c
        
        # Carbon mass display - à droite du sélecteur d'unités de temps
        ax_carbon_mass = plt.axes([0.80, 0.92, button_width/1.5, button_height])
        ax_carbon_mass.text(0.5, 0.5, "Masse C: 0 µg", ha="center", va="center", transform=ax_carbon_mass.transAxes)
        ax_carbon_mass.axis('off')
        self.indicators['carbon_mass_display'] = ax_carbon_mass
        
        # Init button (blue)
        ax_button_init = plt.axes([0.89, 0.06, button_width, button_height])
        init_button = Button(ax_button_init, 'Init', color='lightblue')
        # Assurer que la couleur est bien appliquée
        init_button.ax.set_facecolor('lightblue')
        init_button.color = 'lightblue'
        self.buttons['init'] = init_button
    
    def setup_indicators(self):
        """Set up status indicators"""
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
        Connect a button to a callback function
        
        Args:
            button_name: Name of the button to connect
            callback: Function to call when the button is clicked
        """
        if button_name in self.buttons:
            # Pour les boutons qui peuvent être désactivés (push_open, retract_close, co2_temp_humidity, res_temp, etc.)
            if button_name in ['push_open', 'retract_close', 'co2_temp_humidity', 'res_temp', 'set_Tcons']:
                
                def wrapped_disabled_callback(event):
                    # Ne rien faire si le bouton est désactivé
                    if hasattr(self.buttons[button_name], 'active') and not self.buttons[button_name].active:
                        return
                    
                    # Sinon, appeler le callback normal
                    callback(event)
                
                self.buttons[button_name].on_clicked(wrapped_disabled_callback)
                
                # S'assurer que le bouton a l'attribut 'active'
                if not hasattr(self.buttons[button_name], 'active'):
                    self.buttons[button_name].active = True
                
            # Cas spécial pour le bouton init qui active les autres boutons
            elif button_name == 'init':
                original_color = self.buttons[button_name].ax.get_facecolor()
                
                def wrapped_init_callback(event):
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
                    
                    # Forcer la mise à jour du canvas
                    self.buttons[button_name].ax.figure.canvas.draw_idle()
                
                self.buttons[button_name].on_clicked(wrapped_init_callback)
            else:
                self.buttons[button_name].on_clicked(callback)
    
    def connect_textbox(self, textbox_name, callback):
        """
        Connect a textbox to a callback function
        
        Args:
            textbox_name: Name of the textbox to connect
            callback: Function to call when the textbox is submitted
        """
        if textbox_name in self.textboxes:
            self.textboxes[textbox_name].on_submit(callback)
            
    def connect_radiobutton(self, radiobutton_name, callback):
        """
        Connect a radio button to a callback function
        
        Args:
            radiobutton_name: Name of the radio button to connect
            callback: Function to call when the radio button selection changes
        """
        if radiobutton_name in self.radiobuttons:
            self.radiobuttons[radiobutton_name].on_clicked(callback)
    
    def update_indicator(self, indicator_name, state):
        """
        Update an indicator's state
        
        Args:
            indicator_name: Name of the indicator to update
            state: New state for the indicator (True = active, False = inactive)
        """
        if indicator_name in self.indicators:
            indicator = self.indicators[indicator_name]
            if indicator is None:
                # Skip None indicators (like increase_led and stabilization_led which are now vertical lines)
                return
            
            if state:
                indicator.set_color('green')
            else:
                indicator.set_color('gray')
            indicator.figure.canvas.draw()
    
    def update_sensor_indicators(self, pin_states=None):
        """
        Update sensor indicators based on individual pin states
        
        Args:
            pin_states: Dictionary with states of VR, VS, TO, TF pins
                       {'vr': bool, 'vs': bool, 'to': bool, 'tf': bool}
        """
        if pin_states is None:
            # Unknown state - all indicators off
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
        Update detection indicators - now using vertical dotted lines in the conductance plot
        instead of LED indicators
        
        Args:
            increase_detected: Whether an increase in conductance has been detected
            stabilized: Whether the conductance has stabilized
        """
        # Les changements de détection sont maintenant gérés par les lignes verticales
        # dans update_conductance_plot à travers le dictionnaire events
        # Cette méthode est conservée pour la compatibilité avec le code existant
        pass
        
    def reset_reference_restabilization(self):
        """
        Reset the reference restabilization time to use the next detected restabilization
        """
        self.reference_restabilization_time = None
    
    def update_R0_display(self, value):
        """
        Update the R0 display
        
        Args:
            value: Value to display
        """
        ax_label = self.indicators['R0_display']
        ax_label.clear()
        ax_label.text(0.5, 0.5, f"{value}", ha="center", va="center", transform=ax_label.transAxes)
        ax_label.figure.canvas.draw()
        
    def update_regeneration_status(self, status, results=None):
        """
        Update the regeneration button status based on regeneration progress
        
        Args:
            status: Dictionary containing status of regeneration protocol
                'active': bool - True if regeneration is in progress
                'step': int - Current step (0-3)
                'message': str - Status message
                'progress': float - Progress percentage (0-100)
            results: Optional dictionary containing regeneration results
                'delta_c': float - Delta C between initial and final stabilization
                'carbon_mass': float - Calculated carbon mass in µg
        """
        if 'regeneration' not in self.buttons:
            return
            
        regeneration_button = self.buttons['regeneration']
        cancel_button = self.buttons.get('cancel_regeneration')
        
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
            regeneration_button.label.set_text("Start Regeneration")
            regeneration_button.ax.set_facecolor('firebrick')
            regeneration_button.color = 'firebrick'
            regeneration_button.label.set_color('white')
            regeneration_button.active = True
            
            # Hide cancel button
            if cancel_button:
                cancel_button.ax.set_visible(False)
                cancel_button.active = False
                
            # Réactiver les boutons CO2/T/H et Res/Temp après la régénération
            self.set_regeneration_buttons_state(True)
            
            # Mettre à jour les afficheurs de résultats si disponibles
            if results is not None:
                delta_c = results.get('delta_c', 0)
                carbon_mass = results.get('carbon_mass', 0)
                
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
            
        regeneration_button.ax.figure.canvas.draw_idle()
        
        # Redraw cancel button if it exists
        if cancel_button:
            cancel_button.ax.figure.canvas.draw_idle()
    
    def update_conductance_plot(self, timeList, conductanceList, events=None):
        """
        Update the conductance plot
        
        Args:
            timeList: List of time values
            conductanceList: List of conductance values
            events: Dictionary of events to mark on the plot
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
            
            # Afficher la légende seulement s'il y a des marqueurs
            if has_markers:
                ax.legend()
        
        self.fig.canvas.draw()
    
    def update_co2_temp_humidity_plot(self, timestamps_co2, values_co2, timestamps_temp, values_temp, 
                                    timestamps_humidity, values_humidity, regeneration_timestamps=None):
        """
        Update the CO2, temperature and humidity plot
        
        Args:
            timestamps_co2: List of CO2 timestamps
            values_co2: List of CO2 values
            timestamps_temp: List of temperature timestamps
            values_temp: List of temperature values
            timestamps_humidity: List of humidity timestamps
            values_humidity: List of humidity values
            regeneration_timestamps: Dictionary of timestamps for key events in the regeneration protocol
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
        Update the resistance temperature plot
        
        Args:
            timestamps: List of timestamps
            temperatures: List of temperature values
            tcons_values: List of Tcons values
            regeneration_timestamps: Dictionary of timestamps for key events in the regeneration protocol
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
        Update visibility of reset buttons based on measurement states
        
        Args:
            measurement_states: Dictionary with measurement states
        """
        if self.mode == "manual":
            for measurement, state in measurement_states.items():
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
        Configure which measurement panels are visible and reorganize the layout
        
        Args:
            measure_conductance: Whether to show conductance panel
            measure_co2: Whether to show CO2/temp/humidity panel
            measure_regen: Whether to show regeneration temperature panel
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
            if n_active < 3:
                # Recalculer les positions de chaque axe visible
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
        Handle change in time unit display (seconds/minutes)
        
        Args:
            label: Selected radio button label
        """
        if label == 'Minutes':
            self.display_minutes = True
        else:  # 'Secondes'
            self.display_minutes = False
            
        # Force redraw of all plots with the new time unit
        # This is normally done by the parent application during the next update cycle
            
    def close(self):
        """Close the plot window"""
        plt.close(self.fig)
    
    def show(self):
        """Show the plot window"""
        plt.show()