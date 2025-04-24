"""
Constantes utilisées dans toute l'application
"""

# Constantes de mesure
STABILITY_DURATION = 2 * 60  # 3 minutes en secondes
INCREASE_SLOPE_MIN = 0.1  # Seuil minimum pour la pente en µS/s
INCREASE_SLOPE_MAX = 0.7  # Seuil maximum pour la pente en µS/s
DECREASE_SLOPE_THRESHOLD = -0.05  # Seuil pour détecter une diminution de conductance
SLIDING_WINDOW = 2.5 * 60  # Fenêtre de 2,5 minutes pour le calcul de la pente
R0_THRESHOLD = 12  # Seuil pour R0
REGENERATION_TEMP = 700  # Température pour la régénération et point de consigne haute température
TCONS_LOW = 0  # Point de consigne basse température
VALVE_DELAY = 4  # Délai en secondes après opération de vanne

# Paramètres de stabilité CO2 pour le protocole de régénération
CO2_STABILITY_THRESHOLD = 5  # Seuil de stabilité CO2 en ppm
CO2_STABILITY_DURATION = 60  # 60 secondes pour la stabilité CO2
REGENERATION_DURATION = 2*60  # 120 secondes de régénération à haute température
CELL_VOLUME = 0.965  # Volume de la cellule en litres

# Configuration Keithley 6517
KEITHLEY_GPIB_ADDRESS = "GPIB0::27::INSTR"
KEITHLEY_COMMANDS = {
    "ZERO_CHECK_OFF": ":SYST:ZCH OFF",
    "MODE_RESISTANCE": ":SENS:FUNC 'RES'",
    "AUTO_RANGE_LOW_LIMIT": ":SENS:RES:RANG:AUTO:LLIM 100",
    "AUTO_RANGE_HIGH_LIMIT": ":SENS:RES:RANG:AUTO:ULIM 100000",
    "VOLTAGE_RANGE": ":SOUR:VOLT:RANG 10",
    "VOLTAGE_LEVEL": ":SOUR:VOLT:LEV 10",
    "OUTPUT_ON": ":OUTP ON",
    "OUTPUT_OFF": ":OUTP OFF",
    "READ_FRESH": ":SENSe:DATA:FRESH?"
}

# Opérations de fichier
EXCEL_BASE_DIR = "donnees_excel"