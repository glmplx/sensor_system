"""
Constantes utilisées dans toute l'application de système de capteurs.
Définit les seuils, paramètres et configurations pour les différents dispositifs et protocoles.
"""

# Constantes de mesure pour la détection de conductance
STABILITY_DURATION = 120# Durée requise en secondes pour considérer la conductance comme stable
INCREASE_SLOPE_MIN = 0.1# Seuil minimum pour la pente d'augmentation de conductance en µS/s
INCREASE_SLOPE_MAX = 0.7# Seuil maximum pour la pente d'augmentation de conductance en µS/s
DECREASE_SLOPE_THRESHOLD = -0.6000000000000001-0.6000000000000001-0.2-0.2-0.1-0.05-0.05  # Seuil négatif pour détecter une diminution de conductance en µS/s
SLIDING_WINDOW = 150# Taille de la fenêtre glissante en secondes pour le calcul de la pente
R0_THRESHOLD = 15# Seuil de résistance R0 en Ohms pour le calcul de conductance
REGENERATION_TEMP = 700# Température en °C pour la régénération et point de consigne haute température
TCONS_LOW = 0# Point de consigne basse température en °C
VALVE_DELAY = 4# Délai d'attente en secondes après opération d'ouverture/fermeture de vanne
CONDUCTANCE_DECREASE_THRESHOLD = 5# Seuil de décroissance de conductance en µS

# Paramètres pour le protocole de régénération CO2
CO2_STABILITY_THRESHOLD = 15# Variation maximale en ppm pour considérer le CO2 comme stable
CO2_STABILITY_DURATION = 120# Durée en secondes pendant laquelle le CO2 doit être stable
REGENERATION_DURATION = 120# Durée en secondes du maintien à haute température pendant la régénération
CELL_VOLUME = 0.965# Volume de la cellule de mesure en litres pour le calcul de masse de carbone
CO2_INCREASE_THRESHOLD = 15# Seuil d'augmentation de CO2 en ppm pour déclencher la détection

# Configuration du multimètre Keithley 6517
KEITHLEY_GPIB_ADDRESS = "GPIB0::27::INSTR"  # Adresse GPIB de l'appareil Keithley
KEITHLEY_READ_TIMEOUT = 5000  # Timeout en ms pour les opérations de lecture (5 secondes)
KEITHLEY_OPERATION_TIMEOUT = 3000  # Timeout en ms pour les opérations standards (3 secondes)
KEITHLEY_VISA_ERROR_CLOSING_FAILED = "-1073807338"  # Code d'erreur VISA pour échec de fermeture de connexion
KEITHLEY_POLARIZATION_VOLTAGE = 10# Tension de polarisation en Volts pour les mesures de conductance
KEITHLEY_COMMANDS = {
    "ZERO_CHECK_OFF": ":SYST:ZCH OFF",  # Désactive la vérification du zéro
    "MODE_RESISTANCE": ":SENS:FUNC 'RES'",  # Configure l'appareil en mode mesure de résistance
    "AUTO_RANGE_LOW_LIMIT": ":SENS:RES:RANG:AUTO:LLIM 100",  # Limite inférieure de l'auto-range en Ohms
    "AUTO_RANGE_HIGH_LIMIT": ":SENS:RES:RANG:AUTO:ULIM 100000",  # Limite supérieure de l'auto-range en Ohms
    "VOLTAGE_RANGE": ":SOUR:VOLT:RANG 10",  # Configure la plage de tension à 10V
    "VOLTAGE_LEVEL": ":SOUR:VOLT:LEV {}",  # Configure le niveau de tension (à formater avec la valeur)
    "OUTPUT_ON": ":OUTP ON",  # Active la sortie
    "OUTPUT_OFF": ":OUTP OFF",  # Désactive la sortie
    "READ_FRESH": ":SENSe:DATA:FRESH?"  # Commande pour lire une nouvelle mesure
}

# Configuration des périphériques série
ARDUINO_DEFAULT_BAUD_RATE = 115200  # Vitesse de communication par défaut pour l'Arduino
ARDUINO_DEFAULT_TIMEOUT = 2  # Timeout par défaut pour les opérations Arduino en secondes
REGEN_DEFAULT_BAUD_RATE = 115200  # Vitesse de communication par défaut pour la carte de régénération
REGEN_DEFAULT_TIMEOUT = 2  # Timeout par défaut pour les opérations de régénération en secondes
REGEN_COMMAND_DELAY = 0.2  # Délai après envoi d'une commande à la carte de régénération en secondes
REGEN_DATA_CHECK_INTERVAL = 0.1  # Intervalle entre vérifications de données disponibles en secondes
REGEN_MAX_DATA_CHECK_ATTEMPTS = 5  # Nombre maximum de tentatives de vérification de données
REGEN_WRITE_DELAY = 0.1  # Délai après écriture d'un paramètre en secondes

# Configuration de stockage des données
EXCEL_BASE_DIR = "donnees_excel"  # Répertoire de base pour le stockage des fichiers Excel générés