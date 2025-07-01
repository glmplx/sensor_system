"""
Module de configuration pour le système de capteurs.
Charge les paramètres depuis le fichier sensor_config.json.
"""
import json
import os
from typing import Any, Dict

class Config:
    """Gestionnaire de configuration singleton pour charger les paramètres depuis JSON."""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._load_config()
        return cls._instance
    
    @classmethod
    def _load_config(cls):
        """Charge la configuration depuis le fichier JSON."""
        config_path = os.path.join(os.path.dirname(__file__), 'sensor_config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cls._config = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Fichier de configuration non trouvé : {config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Erreur de format JSON dans le fichier de configuration : {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Récupère une valeur de configuration."""
        return self._config.get(key, default)
    
    def __getattr__(self, name: str) -> Any:
        """Permet l'accès aux paramètres via config.PARAM_NAME."""
        if self._config and name in self._config:
            return self._config[name]
        raise AttributeError(f"Configuration '{name}' non trouvée")

# Instance globale
config = Config()

# Constantes additionnelles non présentes dans le JSON
EXCEL_BASE_DIR = "donnees_excel"
KEITHLEY_GPIB_ADDRESS = "GPIB0::27::INSTR"
KEITHLEY_READ_TIMEOUT = 5000
KEITHLEY_OPERATION_TIMEOUT = 3000
KEITHLEY_VISA_ERROR_CLOSING_FAILED = "-1073807338"
KEITHLEY_COMMANDS = {
    "ZERO_CHECK_OFF": ":SYST:ZCH OFF",
    "MODE_RESISTANCE": ":SENS:FUNC 'RES'",
    "AUTO_RANGE_LOW_LIMIT": ":SENS:RES:RANG:AUTO:LLIM 100",
    "AUTO_RANGE_HIGH_LIMIT": ":SENS:RES:RANG:AUTO:ULIM 100000",
    "VOLTAGE_RANGE": ":SOUR:VOLT:RANG 10",
    "VOLTAGE_LEVEL": ":SOUR:VOLT:LEV {}",
    "OUTPUT_ON": ":OUTP ON",
    "OUTPUT_OFF": ":OUTP OFF",
    "READ_FRESH": ":SENSe:DATA:FRESH?"
}
ARDUINO_DEFAULT_BAUD_RATE = 115200
ARDUINO_DEFAULT_TIMEOUT = 2
REGEN_DEFAULT_BAUD_RATE = 115200
REGEN_DEFAULT_TIMEOUT = 2
REGEN_COMMAND_DELAY = 0.2
REGEN_DATA_CHECK_INTERVAL = 0.1
REGEN_MAX_DATA_CHECK_ATTEMPTS = 5
REGEN_WRITE_DELAY = 0.1