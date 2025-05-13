# Documentation des fonctions

Générée automatiquement le 2025-05-07 16:05:32


## Fichier: auto_app.py

### Fonction: `main(arduino_port=None, arduino_baud_rate=None, other_port=None, other_baud_rate=None)`

**Description:**

Point d'entrée principal pour l'application en mode automatique
    
    Cette fonction initialise les appareils, configure l'interface graphique et exécute
    la boucle principale qui gère la détection de conductance et la régénération automatiques.
    
    Args:
        arduino_port: Port COM de l'Arduino (CO2, température, humidité)
        arduino_baud_rate: Débit en bauds pour la communication avec l'Arduino
        other_port: Port COM de la carte de régénération
        other_baud_rate: Débit en bauds pour la communication avec la carte de régénération

---

### Fonction: `handle_window_close(event=None)`

**Description:**

Gère l'événement de fermeture de la fenêtre par le bouton X
        
        Args:
            event: Événement de fermeture de la fenêtre

---

### Fonction: `toggle_auto(event)`

**Description:**

Active ou désactive les mesures automatiques
        
        Cette fonction gère l'activation/désactivation des mesures automatiques,
        incluant l'initialisation des fichiers, l'activation du Keithley et la 
        gestion des temps de pause pour maintenir des timestamps cohérents.
        
        Args:
            event: Événement déclencheur (clic sur le bouton)

---

### Fonction: `raz_auto(event)`

**Description:**

Réinitialise les données de mesure en mode automatique
        
        Cette fonction sauvegarde d'abord les données actuelles dans les fichiers Excel,
        puis réinitialise les données de mesure et les graphiques. Elle conserve l'historique
        des données déjà enregistrées.
        
        Args:
            event: Événement déclencheur (clic sur le bouton)

---

### Fonction: `start_regeneration(event)`

**Description:**

Gère le clic sur le bouton de régénération
        
        Cette fonction démarre le protocole de régénération du capteur qui implique
        le chauffage du capteur pour éliminer les molécules adsorbées.
        
        Args:
            event: Événement déclencheur (clic sur le bouton)

---

### Fonction: `cancel_regeneration(event)`

**Description:**

Gère le clic sur le bouton d'annulation de régénération
        
        Cette fonction annule le protocole de régénération en cours et
        ramène le système à son état normal.
        
        Args:
            event: Événement déclencheur (clic sur le bouton)

---

### Fonction: `quit_program(event)`

**Description:**

Gère la fermeture propre du programme
        
        Cette fonction sauvegarde les données, propose de renommer le dossier de données,
        réinitialise la température consigne, ferme les connexions avec les appareils et
        nettoie les ressources graphiques avant de quitter le programme.
        
        Args:
            event: Événement déclencheur (clic sur le bouton ou fermeture de fenêtre)

---

### Fonction: `process_pin_states(line)`

**Description:**

Traite les informations d'état des pins et met à jour l'interface
                
                Cette fonction analyse les états des pins (capteurs de position) depuis
                une ligne de données Arduino et met à jour les indicateurs visuels correspondants.
                
                Args:
                    line: Ligne de texte contenant les informations d'état des pins
                    
                Returns:
                    bool: True si des états de pins ont été traités, False sinon

---


## Fichier: create_executable.py

### Fonction: `create_executable()`

**Description:**

Create an executable for the sensor system application

---


## Fichier: create_installer.py

### Fonction: `create_installer()`

**Description:**

Create an installer for the sensor system application

---


## Fichier: doc_maker.py

### Fonction: `find_python_files(directory='.')`

**Description:**

Trouve tous les fichiers Python dans le répertoire et ses sous-répertoires.

---

### Fonction: `extract_functions(filepath)`

**Description:**

Extrait les informations sur les fonctions d'un fichier Python.

---

### Fonction: `generate_markdown_documentation(functions_data, output_file='DOCUMENTATION.md')`

**Description:**

Génère un fichier Markdown avec la documentation des fonctions.

---

### Fonction: `main()`

**Description:**

Permet de lancer le programme

---


## Fichier: main.py

### Fonction: `main()`

**Description:**

Point d'entrée principal pour l'application.
    Initialise l'interface utilisateur et gère les exceptions globales.

---


## Fichier: manual_app.py

### Fonction: `main(arduino_port=None, arduino_baud_rate=None, other_port=None, other_baud_rate=None,
         measure_conductance=1, measure_co2=1, measure_regen=1)`

**Description:**

Point d'entrée principal pour l'application en mode manuel
    
    Args:
        arduino_port: Port COM pour l'Arduino
        arduino_baud_rate: Débit en bauds pour l'Arduino
        other_port: Port COM pour l'appareil de régénération
        other_baud_rate: Débit en bauds pour l'appareil de régénération
        measure_conductance: Activer les mesures de conductance (1=activé, 0=désactivé)
        measure_co2: Activer les mesures de CO2/température/humidité (1=activé, 0=désactivé)
        measure_regen: Activer les mesures de régénération/température (1=activé, 0=désactivé)

---

### Fonction: `update_regeneration_button_state()`

**Description:**

Met à jour l'état des boutons de protocole en fonction des mesures actives

---

### Fonction: `perform_emergency_backup(reason="sauvegarde automatique")`

**Description:**

Effectue une sauvegarde d'urgence des données en cas de problème avec un appareil
        ou périodiquement pour éviter la perte de données
        
        Args:
            reason: Raison de la sauvegarde (pour le journal et les notifications)
            
        Returns:
            bool: True si des données ont été sauvegardées, False sinon

---

### Fonction: `show_backup_notification(reason)`

**Description:**

Affiche une notification à l'utilisateur concernant la sauvegarde d'urgence
        
        Args:
            reason: Raison de la sauvegarde

---

### Fonction: `check_device_errors()`

**Description:**

Vérifie les erreurs des appareils pour détecter des problèmes de connexion
        
        Returns:
            dict: Informations sur les erreurs détectées

---

### Fonction: `add_arduino_device(event)`

**Description:**

Fonction pour ajouter un Arduino en cours d'exécution

---

### Fonction: `add_keithley_device(event=None)`

**Description:**

Fonction pour ajouter un Keithley en cours d'exécution

---

### Fonction: `add_regen_device(event)`

**Description:**

Fonction pour ajouter une carte de régénération en cours d'exécution

---

### Fonction: `start_conductance_regen(event)`

**Description:**

Handle conductance regeneration button click

---

### Fonction: `cancel_conductance_regen(event)`

**Description:**

Handle conductance regeneration cancel button click - redirects to unified cancel function

---

### Fonction: `add_keithley_device(event)`

**Description:**

Fonction pour ajouter un Keithley en cours d'exécution

---


## Fichier: measurement_manager.py

### Fonction: `__init__(self, keithley_device, arduino_device, regen_device)`

**Description:**

Initialise le gestionnaire de mesures
        
        Args:
            keithley_device: Appareil pour les mesures de résistance
            arduino_device: Appareil pour les mesures de CO2, température, humidité
            regen_device: Appareil pour le contrôle de température de résistance

---

### Fonction: `reset_data(self, data_type=None)`

**Description:**

Reset stored data with proper handling for ExcelHandler
        
        Args:
            data_type: Type of data to reset, or None for all data

---

### Fonction: `read_conductance(self)`

**Description:**

Lit les données de conductance depuis l'appareil Keithley

---

### Fonction: `read_arduino_status_only(self)`

**Description:**

Read pin states from Arduino without storing CO2/temperature/humidity data
        Returns: True if pin states were updated, False otherwise

---

### Fonction: `read_arduino_data(self)`

**Description:**

Read CO2, temperature, humidity data from Arduino and store it
        Only called when measurements are active

---

### Fonction: `read_arduino(self)`

**Description:**

Méthode pour compatibilité - redirige vers read_arduino_data

---

### Fonction: `read_res_temp(self)`

**Description:**

Read resistance temperature data

---

### Fonction: `push_open_sensor(self)`

**Description:**

Push/open the sensor

---

### Fonction: `retract_close_sensor(self)`

**Description:**

Retract/close the sensor

---

### Fonction: `init_system(self)`

**Description:**

Initialize the system

---

### Fonction: `set_R0(self, value)`

**Description:**

Set R0 value

---

### Fonction: `set_Tcons(self, value)`

**Description:**

Set Tcons value

---

### Fonction: `read_R0(self)`

**Description:**

Read R0 value

---

### Fonction: `detect_increase(self)`

**Description:**

Detect increase in conductance
        Returns: True if increase detected, False otherwise

---

### Fonction: `detect_stabilization(self)`

**Description:**

Detect stabilization in conductance
        Returns: True if stabilization detected, False otherwise

---

### Fonction: `detect_co2_peak(self)`

**Description:**

Detect CO2 peak after an increase was detected
        
        Returns:
            None: Updates self.co2_peak_detected flag if a peak is detected

---

### Fonction: `check_reset_detection_indicators(self)`

**Description:**

Vérifie si la conductance est descendue sous 5 µS après stabilisation
        et réinitialise les indicateurs de détection (mais pas le temps de percolation)
        
        Returns: True si les indicateurs ont été réinitialisés, False sinon

---

### Fonction: `check_conductance_increase_after_decrease(self)`

**Description:**

Vérifie si la conductance remonte après être descendue sous 5 µS.
        Si oui, actualise l'indicateur de début d'augmentation (T perco).
        
        Returns: True si une remontée est détectée et l'indicateur actualisé, False sinon

---

### Fonction: `detect_post_regen_stability(self)`

**Description:**

Détecte la restabilisation après une chute de conductance post-régénération
        Returns: True si restabilisation détectée, False sinon

---

### Fonction: `automatic_mode_handler(self)`

**Description:**

Handle automatic mode logic
        Returns: True if action was taken, False otherwise

---

### Fonction: `get_last_timestamps(self)`

**Description:**

Get the latest timestamps for all data types

---

### Fonction: `start_regeneration_protocol(self)`

**Description:**

Start the regeneration protocol:
        1. Check for CO2 stability (±2 ppm for 2 minutes)
        2. When stable, increase temperature to 700°C for 3 minutes
        3. Return to normal operation
        
        Returns:
            bool: True if regeneration protocol was started, False if already in progress

---

### Fonction: `cancel_regeneration_protocol(self)`

**Description:**

Cancel the regeneration protocol and return to normal temperature
        
        Returns:
            bool: True if regeneration was cancelled, False if not in progress

---

### Fonction: `check_co2_stability(self)`

**Description:**

Check if CO2 readings are stable (±2 ppm for 2 minutes)
        
        Returns:
            bool: True if CO2 is stable for the required duration, False otherwise

---

### Fonction: `check_co2_restabilization(self)`

**Description:**

Check if CO2 readings have restabilized after the peak
        
        Returns:
            bool: True if CO2 is stable for the required duration, False otherwise

---

### Fonction: `regeneration_complete(self)`

**Description:**

Complete the regeneration process and reset variables

---

### Fonction: `start_conductance_regen_protocol(self)`

**Description:**

Démarre le protocole de conductance avec résistance/température:
        1. Lance la régénération à 700°C
        2. Surveille la résistance jusqu'à ce qu'elle dépasse 1 MΩ
        3. Arrête la régénération quand la résistance > 1 MΩ est atteinte
        
        Returns:
            bool: True si le protocole a été démarré, False si déjà en cours

---

### Fonction: `cancel_conductance_regen_protocol(self)`

**Description:**

Annuler le protocole de conductance résistance/température
        
        Returns:
            bool: True si le protocole a été annulé, False sinon

---

### Fonction: `manage_conductance_regen_protocol(self)`

**Description:**

Gère le protocole de conductance avec résistance/température:
        Surveille la résistance et arrête la régénération quand elle dépasse 1 MΩ
        
        Returns:
            dict: État actuel du protocole

---

### Fonction: `start_full_protocol(self)`

**Description:**

Démarre le protocole complet, qui combine plusieurs opérations en séquence:
        1. Rétracte le vérin (ferme)
        2. Vérifie la stabilité du CO2
        3. Augmente Tcons à 700°C
        4. Attend que la conductance descende sous 5µS
        5. Remet Tcons à 0°C
        6. Attend la restabilisation du CO2
        7. Calcule delta C et masse de carbone
        
        Ce protocole est particulièrement destiné à être utilisé sur BANCO après un feu.
        
        Returns:
            bool: True si le protocole a démarré, False si déjà en cours

---

### Fonction: `manage_full_protocol(self)`

**Description:**

Gère les différentes étapes du protocole complet.
        
        Returns:
            dict: État actuel du protocole complet
                'active': bool - True si le protocole est en cours
                'step': int - Étape actuelle (1-7)
                'message': str - Message d'état
                'progress': float - Progression (0-100)

---

### Fonction: `manage_regeneration_protocol(self)`

**Description:**

Gère le protocole de régénération avec les nouvelles règles :
        1. La détection de restabilisation peut commencer dès le pic détecté
        2. La température reste à 700°C jusqu'à la fin de REGENERATION_DURATION
        3. La restabilisation peut se terminer avant ou après le retour à 0°C

---


## Fichier: excel_handler.py

### Fonction: `__init__(self, mode="manual")`

**Description:**

Initialiser le gestionnaire Excel
        
        Args:
            mode: Mode de fonctionnement, soit "manual" soit "auto"

---

### Fonction: `initialize_folder(self)`

**Description:**

Initialise le dossier de test basé sur la date et l'heure actuelles
        
        Returns:
            str: Chemin vers le dossier de test créé

---

### Fonction: `initialize_file(self, file_type)`

**Description:**

Initialise un fichier Excel pour un type de données spécifique
        
        Args:
            file_type: Type de fichier de données à initialiser ('conductance', 'co2_temp_humidity', 'temp_res')
            
        Returns:
            str: Chemin vers le fichier initialisé

---

### Fonction: `_create_workbook_with_info(self, file_path, file_type)`

**Description:**

Crée un classeur Excel sans feuille initiale
        
        Args:
            file_path: Chemin du fichier à créer
            file_type: Type de fichier (non utilisé)
            
        Returns:
            str: Chemin du fichier créé

---

### Fonction: `add_sheet_to_excel(self, file_path, sheet_name, data)`

**Description:**

Ajoute une feuille au fichier excel de sauvegarde

---

### Fonction: `_update_cumulative_sheet(self, file_path)`

**Description:**

Met à jour ou crée la feuille 'Essais cumulés' de manière plus robuste

---

### Fonction: `raz_co2_temp_humidity_data(self, co2_timestamps, co2_values, temp_timestamps, temp_values, humidity_timestamps, humidity_values)`

**Description:**

Prépare les données CO2/temp/humidity pour un nouvel essai

---

### Fonction: `raz_temp_res_data(self, timestamps, temperatures, tcons_values)`

**Description:**

Prépare les données temp/resistance pour un nouvel essai

---

### Fonction: `raz_conductance_data(self, timeList, conductanceList, resistanceList)`

**Description:**

Prépare les données pour un nouvel essai sans sauvegarder immédiatement

---

### Fonction: `save_conductance_data(self, timeList, conductanceList, resistanceList, sheet_name=None)`

**Description:**

Sauvegarde les données de conductance dans le fichier Excel
        
        Args:
            timeList: Liste des timestamps (en secondes)
            conductanceList: Liste des valeurs de conductance (en µS)
            resistanceList: Liste des valeurs de résistance (en Ohms)
            sheet_name: Nom de la feuille à utiliser (ou None pour créer un nom basé sur l'horodatage)
            
        Returns:
            bool: True si la sauvegarde a réussi, False sinon

---

### Fonction: `save_co2_temp_humidity_data(self, co2_timestamps, co2_values, temp_timestamps, temp_values, humidity_timestamps, humidity_values, delta_c=None, carbon_mass=None, sheet_name=None)`

**Description:**

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

---

### Fonction: `save_temp_res_data(self, timestamps, temperatures, tcons_values, sheet_name=None)`

**Description:**

Sauvegarde les données temp/resistance
        
        Args:
            timestamps: Liste des timestamps
            temperatures: Liste des valeurs de température
            tcons_values: Liste des valeurs de consigne de température
            sheet_name: Nom de la feuille à utiliser (ou None pour créer un nom basé sur l'horodatage)

---

### Fonction: `save_all_data(self, measurement_manager)`

**Description:**

Save all data to Excel files
        
        Args:
            measurement_manager: MeasurementManager instance with data
            
        Returns:
            bool: True if all data was saved successfully, False otherwise

---

### Fonction: `rename_test_folder(self, new_name)`

**Description:**

Rename the test folder with a custom name
        
        Args:
            new_name: New name for the test folder
            
        Returns:
            bool: True if the folder was renamed successfully, False otherwise

---

### Fonction: `add_charts_to_excel(self, file_path)`

**Description:**

Ajoute des graphiques aux feuilles Excel en fonction du type de données
        
        Args:
            file_path: Chemin du fichier Excel
            
        Returns:
            bool: True si les graphiques ont été ajoutés avec succès, False sinon

---

### Fonction: `_add_conductance_charts(self, workbook)`

**Description:**

Ajoute les graphiques pour les données de conductance
        
        Args:
            workbook: Classeur Excel ouvert

---

### Fonction: `_add_co2_temp_humidity_charts(self, workbook)`

**Description:**

Ajoute les graphiques pour les données CO2/température/humidité
        
        Args:
            workbook: Classeur Excel ouvert

---

### Fonction: `_add_temp_res_charts(self, workbook)`

**Description:**

Ajoute les graphiques pour les données température/résistance
        
        Args:
            workbook: Classeur Excel ouvert

---

### Fonction: `_should_create_cumulative_sheet(self, file_path)`

**Description:**

Détermine si une feuille 'Essais cumulés' doit être créée

---


## Fichier: arduino_device.py

### Fonction: `__init__(self, port=None, baud_rate=115200, timeout=2)`

**Description:**

Initialise l'appareil Arduino
        
        Args:
            port: Port série à connecter
            baud_rate: Vitesse en bauds pour la connexion série
            timeout: Délai d'expiration pour les opérations série en secondes

---

### Fonction: `connect(self)`

**Description:**

Établit la connexion à l'appareil Arduino via le port série
        
        Returns:
            bool: True si la connexion a réussi, False sinon

---

### Fonction: `read_line(self)`

**Description:**

Lire une ligne depuis l'Arduino
        
        Returns:
            str: La ligne lue, ou None en cas d'erreur

---

### Fonction: `send_command(self, command)`

**Description:**

Envoyer une commande à l'Arduino
        
        Args:
            command: La commande à envoyer
            
        Returns:
            bool: True si la commande a été envoyée avec succès, False sinon

---

### Fonction: `close(self)`

**Description:**

Ferme proprement la connexion à l'Arduino
        
        Returns:
            bool: True si la fermeture a réussi ou si l'appareil était déjà fermé, False en cas d'erreur

---


## Fichier: keithley_device.py

### Fonction: `__init__(self, gpib_address=KEITHLEY_GPIB_ADDRESS)`

**Description:**

Initialise l'appareil Keithley
        
        Args:
            gpib_address: Adresse GPIB de l'appareil

---

### Fonction: `connect(self)`

**Description:**

Établit la connexion à l'appareil Keithley via GPIB
        
        Returns:
            bool: True si la connexion a réussi, False sinon

---

### Fonction: `configure(self)`

**Description:**

Configure l'appareil Keithley avec les paramètres nécessaires pour les mesures de résistance
        
        Returns:
            bool: True si la configuration a réussi, False sinon

---

### Fonction: `read_resistance(self)`

**Description:**

Lire la résistance depuis le Keithley
        
        Returns:
            float: Valeur de résistance en ohms, ou None en cas d'erreur

---

### Fonction: `_async_delay(self, seconds)`

**Description:**

Délai asynchrone pour ne pas bloquer l'exécution

---

### Fonction: `turn_output_on(self)`

**Description:**

Activer la sortie du Keithley

---

### Fonction: `turn_output_off(self)`

**Description:**

Désactiver la sortie du Keithley

---

### Fonction: `close(self)`

**Description:**

Fermer la connexion au Keithley

---

### Fonction: `__del__(self)`

**Description:**

Destructeur - assure que la connexion est fermée lors de la suppression de l'objet

---


## Fichier: regen_device.py

### Fonction: `__init__(self, port=None, baud_rate=115200, timeout=2)`

**Description:**

Initialise l'appareil de régénération
        
        Args:
            port: Port série à connecter
            baud_rate: Vitesse en bauds pour la connexion série
            timeout: Délai d'expiration pour les opérations série en secondes

---

### Fonction: `connect(self)`

**Description:**

Établit la connexion à l'appareil de régénération
        
        Returns:
            bool: True si la connexion a réussi, False sinon

---

### Fonction: `read_variable(self, command, address)`

**Description:**

Lire une variable depuis l'appareil de régénération
        
        Args:
            command: Caractère de commande (par exemple, 'L')
            address: Caractère d'adresse (par exemple, 'a', 'b', 'c', 'd')
            
        Returns:
            str: La valeur lue, ou "0.0" en cas d'erreur (jamais None)

---

### Fonction: `write_parameter(self, command, address, value)`

**Description:**

Écrire un paramètre dans l'appareil de régénération
        
        Args:
            command: Caractère de commande (par exemple, 'e')
            address: Caractère d'adresse (par exemple, 'a', 'b')
            value: Valeur à écrire
            
        Returns:
            bool: True si le paramètre a été écrit avec succès, False sinon

---

### Fonction: `close(self)`

**Description:**

Ferme proprement la connexion à l'appareil de régénération
        
        Returns:
            bool: True si la fermeture a réussi ou si l'appareil était déjà fermé, False en cas d'erreur

---


## Fichier: menu.py

### Fonction: `__init__(self)`

**Description:**

Initialiser l'interface utilisateur du menu

---

### Fonction: `scan_ports(self)`

**Description:**

Analyse les ports COM disponibles et identifie les types d'appareils
        
        Returns:
            tuple: (ports_info, ports_display, arduino_port_index, regen_port_index)
                - ports_info: Liste de tuples (port.device, port.description)
                - ports_display: Liste des ports formatés pour l'affichage
                - arduino_port_index: Index du port Arduino détecté ou None
                - regen_port_index: Index du port de régénération détecté ou None

---

### Fonction: `refresh_ports(self, show_message=True)`

**Description:**

Actualiser la liste des ports COM disponibles
        
        Args:
            show_message: Afficher un message de confirmation après l'actualisation
        
        Returns:
            dict: Informations sur les ports détectés (pour usage externe)

---

### Fonction: `setup_ui(self)`

**Description:**

Configurer les éléments de l'interface utilisateur

---

### Fonction: `set_manual_mode(self)`

**Description:**

Définir le mode manuel et décocher le mode automatique

---

### Fonction: `set_auto_mode(self)`

**Description:**

Définir le mode automatique et décocher le mode manuel

---

### Fonction: `check_port_selections(self, arduino_port_str, other_port_str)`

**Description:**

Vérifie que les ports sélectionnés correspondent aux bonnes cartes
        
        Args:
            arduino_port_str: chaîne du port Arduino sélectionné
            other_port_str: chaîne du port de régénération sélectionné
            
        Returns:
            bool: True si les sélections sont valides ou si l'utilisateur confirme
            str: "swap" si l'utilisateur choisit d'échanger les ports

---

### Fonction: `launch_program(self)`

**Description:**

Lancer le mode de programme sélectionné

---

### Fonction: `open_documentation(self)`

**Description:**

Ouvre le fichier de documentation

---

### Fonction: `quit_application(self)`

**Description:**

Ferme l'application proprement et termine le processus

---

### Fonction: `run(self)`

**Description:**

Exécuter la boucle principale de l'interface utilisateur

---


## Fichier: plot_manager.py

### Fonction: `__init__(self, mode="manual")`

**Description:**

Initialise le gestionnaire de graphiques
        
        Args:
            mode: Mode "manual" ou "auto"

---

### Fonction: `setup_plots(self)`

**Description:**

Configure la figure et les axes pour les graphiques

---

### Fonction: `center_window()`

**Description:**

Centre la fenêtre

---

### Fonction: `setup_manual_buttons(self)`

**Description:**

Configure les boutons pour le mode manuel

---

### Fonction: `setup_auto_buttons(self)`

**Description:**

Configure les boutons pour le mode automatique

---

### Fonction: `setup_common_elements(self)`

**Description:**

Configure les éléments communs aux deux modes

---

### Fonction: `setup_add_device_buttons(self)`

**Description:**

Configure les boutons pour ajouter des appareils pendant l'exécution

---

### Fonction: `setup_indicators(self)`

**Description:**

Configure les indicateurs d'état

---

### Fonction: `connect_button(self, button_name, callback)`

**Description:**

Connecte un bouton à une fonction de rappel
        
        Args:
            button_name: Nom du bouton à connecter
            callback: Fonction à appeler lorsque le bouton est cliqué

---

### Fonction: `connect_textbox(self, textbox_name, callback)`

**Description:**

Connecte un champ de texte à une fonction de rappel
        
        Args:
            textbox_name: Nom du champ de texte à connecter
            callback: Fonction à appeler lorsque le champ de texte est soumis

---

### Fonction: `connect_radiobutton(self, radiobutton_name, callback)`

**Description:**

Connecte un bouton radio à une fonction de rappel
        
        Args:
            radiobutton_name: Nom du bouton radio à connecter
            callback: Fonction à appeler lorsque la sélection du bouton radio change

---

### Fonction: `update_indicator(self, indicator_name, state)`

**Description:**

Met à jour l'état d'un indicateur
        
        Args:
            indicator_name: Nom de l'indicateur à mettre à jour
            state: Nouvel état pour l'indicateur (True = actif, False = inactif)

---

### Fonction: `update_sensor_indicators(self, pin_states=None)`

**Description:**

Met à jour les indicateurs de capteurs en fonction des états individuels des broches
        
        Args:
            pin_states: Dictionnaire avec les états des broches VR, VS, TO, TF
                       {'vr': bool, 'vs': bool, 'to': bool, 'tf': bool}

---

### Fonction: `update_detection_indicators(self, increase_detected, stabilized)`

**Description:**

Met à jour les indicateurs de détection - utilise maintenant des lignes verticales pointillées 
        dans le graphique de conductance au lieu des indicateurs LED
        
        Args:
            increase_detected: Si une augmentation de conductance a été détectée
            stabilized: Si la conductance s'est stabilisée

---

### Fonction: `reset_reference_restabilization(self)`

**Description:**

Réinitialise le temps de référence de restabilisation pour utiliser la prochaine restabilisation détectée

---

### Fonction: `update_R0_display(self, value)`

**Description:**

Met à jour l'affichage de R0
        
        Args:
            value: Valeur à afficher

---

### Fonction: `update_regeneration_status(self, status, results=None)`

**Description:**

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

---

### Fonction: `update_conductance_plot(self, timeList, conductanceList, events=None)`

**Description:**

Met à jour le graphique de conductance
        
        Args:
            timeList: Liste des valeurs de temps
            conductanceList: Liste des valeurs de conductance
            events: Dictionnaire des événements à marquer sur le graphique

---

### Fonction: `update_co2_temp_humidity_plot(self, timestamps_co2, values_co2, timestamps_temp, values_temp, 
                                    timestamps_humidity, values_humidity, regeneration_timestamps=None)`

**Description:**

Met à jour le graphique de CO2, température et humidité
        
        Args:
            timestamps_co2: Liste des horodatages CO2
            values_co2: Liste des valeurs de CO2
            timestamps_temp: Liste des horodatages de température
            values_temp: Liste des valeurs de température
            timestamps_humidity: Liste des horodatages d'humidité
            values_humidity: Liste des valeurs d'humidité
            regeneration_timestamps: Dictionnaire des horodatages pour les événements clés du protocole de régénération

---

### Fonction: `update_res_temp_plot(self, timestamps, temperatures, tcons_values, regeneration_timestamps=None)`

**Description:**

Met à jour le graphique de température de résistance
        
        Args:
            timestamps: Liste des horodatages
            temperatures: Liste des valeurs de température
            tcons_values: Liste des valeurs de Tcons
            regeneration_timestamps: Dictionnaire des horodatages pour les événements clés du protocole de régénération

---

### Fonction: `update_raz_buttons_visibility(self, measurement_states)`

**Description:**

Met à jour la visibilité des boutons de réinitialisation en fonction des états de mesure
        
        Args:
            measurement_states: Dictionnaire avec les états de mesure

---

### Fonction: `deactivate_movement_buttons(self)`

**Description:**

Désactive les boutons push/open et retract/close

---

### Fonction: `set_regeneration_buttons_state(self, active)`

**Description:**

Active ou désactive les boutons qui doivent être indisponibles pendant la régénération
        
        Args:
            active: True pour activer les boutons, False pour les désactiver

---

### Fonction: `configure_measurement_panels(self, measure_conductance=True, measure_co2=True, measure_regen=True)`

**Description:**

Configure les panneaux de mesure visibles et réorganise la mise en page
        
        Args:
            measure_conductance: Si le panneau de conductance doit être affiché
            measure_co2: Si le panneau CO2/temp/humidité doit être affiché
            measure_regen: Si le panneau de température de régénération doit être affiché

---

### Fonction: `on_time_unit_change(self, label)`

**Description:**

Gère le changement d'affichage des unités de temps (secondes/minutes)
        
        Args:
            label: Étiquette du bouton radio sélectionné

---

### Fonction: `update_backup_status(self, status_info)`

**Description:**

Met à jour l'indicateur de sauvegarde de secours
        
        Args:
            status_info: Dictionnaire contenant les informations sur la dernière sauvegarde
                'time': float - Timestamp de la dernière sauvegarde
                'success': bool - True si la sauvegarde a réussi
                'reason': str - Raison de la sauvegarde

---

### Fonction: `close(self)`

**Description:**

Ferme la fenêtre du graphique

---

### Fonction: `show(self)`

**Description:**

Affiche la fenêtre du graphique

---

### Fonction: `update_add_device_buttons(self, available_devices=None)`

**Description:**

Met à jour l'état des boutons d'ajout d'appareils en fonction des appareils déjà connectés
        
        Args:
            available_devices: Dictionnaire indiquant les appareils déjà connectés
                {'arduino': bool, 'regen': bool, 'keithley': bool}

---

### Fonction: `connect_add_device_button(self, device_type, callback)`

**Description:**

Connecte un callback au bouton d'ajout d'appareil
        
        Args:
            device_type: Type d'appareil ('arduino', 'regen' ou 'keithley')
            callback: Fonction à appeler lorsque le bouton est cliqué

---

### Fonction: `update_protocol_button_states(self, measure_co2_temp_humidity_active, measure_conductance_active, measure_res_temp_active)`

**Description:**

Met à jour l'état des boutons de protocole en fonction des mesures actives
        - Le bouton de protocole CO2 doit être cliquable si CO2 et Tcons/Tmes sont actifs
        - Le bouton de protocole de conductance doit être cliquable si Conductance et Tcons/Tmes sont actifs
        - Le bouton de protocole complet doit être cliquable si les trois mesures sont actives
        
        Args:
            measure_co2_temp_humidity_active: Si la mesure de CO2/température/humidité est active
            measure_conductance_active: Si la mesure de conductance est active
            measure_res_temp_active: Si la mesure de résistance/température est active

---

### Fonction: `update_regeneration_status(self, status_info, regeneration_results=None)`

**Description:**

Met à jour l'affichage du statut de régénération/protocole
        
        Args:
            status_info: Dictionnaire contenant les informations de statut
                'active': Bool - Si le protocole est actif
                'step': Int - Étape courante du protocole
                'message': Str - Message à afficher
                'progress': Float - Progression (0-100)
            regeneration_results: Résultats de régénération (non utilisé dans cette fonction)

---

### Fonction: `set_close_callback(self, callback)`

**Description:**

Configure un callback pour quand la fenêtre est fermée via le bouton X
        
        Args:
            callback: Fonction à appeler quand la fenêtre est fermée

---


## Fichier: helpers.py

### Fonction: `calculate_slope(x_values, y_values, window_size=10)`

**Description:**

Calcule la pente d'une ligne ajustée aux valeurs données en utilisant la régression linéaire
    
    Cette fonction utilise numpy.polyfit pour calculer la pente (coefficient de premier degré)
    d'une droite ajustée aux données. Elle est utile pour déterminer le taux de variation
    d'un signal, par exemple pour détecter l'augmentation de conductance.
    
    Args:
        x_values: Liste des valeurs x (généralement le temps)
        y_values: Liste des valeurs y (généralement la conductance)
        window_size: Nombre de points à inclure dans le calcul de la pente
    
    Returns:
        float: Pente de la ligne (taux de variation)

---

### Fonction: `find_indices_for_sliding_window(time_values, current_time, half_window_size)`

**Description:**

Trouve les indices pour une fenêtre glissante centrée autour d'un temps donné
    
    Cette fonction détermine les indices de début et de fin dans une liste de temps
    pour créer une fenêtre autour d'un temps spécifique. Elle est utile pour
    isoler des segments temporels dans les données de mesure, par exemple pour
    analyser une période spécifique avant et après un événement.
    
    Args:
        time_values: Liste des valeurs temporelles (timestamps)
        current_time: Temps central pour la fenêtre
        half_window_size: Demi-taille de la fenêtre en unités de temps
    
    Returns:
        tuple: (indice_début, indice_fin) définissant les bornes de la fenêtre

---

### Fonction: `parse_co2_data(line)`

**Description:**

Analyse les données de CO2, température et humidité à partir d'une ligne Arduino
    
    Cette fonction extrait les valeurs de CO2 (ppm), température (°C) et humidité (%)
    à partir d'une ligne de texte envoyée par l'Arduino. Le format attendu est:
    "@[valeur_CO2] [valeur_température] [valeur_humidité]"
    
    Args:
        line: Ligne lue depuis le port série de l'Arduino
    
    Returns:
        tuple: (co2, température, humidité) ou None si l'analyse a échoué

---

### Fonction: `parse_pin_states(line)`

**Description:**

Analyse les états des pins à partir d'une ligne de données Arduino
    
    Cette fonction extrait l'état des capteurs de position du système à partir
    d'une ligne de texte envoyée par l'Arduino. Le format attendu est:
    "VR:[HIGH/LOW] VS:[HIGH/LOW] TO:[HIGH/LOW] TF:[HIGH/LOW]"
    où:
    - VR: Vérin Rentré
    - VS: Vérin Sorti
    - TO: Trappe Ouverte
    - TF: Trappe Fermée
    
    Args:
        line: Ligne lue depuis le port série contenant les états des pins
        
    Returns:
        dict: Dictionnaire des états des pins {'vr': bool, 'vs': bool, 'to': bool, 'tf': bool}
              ou None si l'analyse a échoué

---

