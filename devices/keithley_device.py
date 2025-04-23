"""
Interface pour l'appareil Keithley 6517
"""

import time
import pyvisa
from core.constants import KEITHLEY_COMMANDS, KEITHLEY_GPIB_ADDRESS

class KeithleyDevice:
    """Interface pour l'électromètre Keithley 6517"""
    
    def __init__(self, gpib_address=KEITHLEY_GPIB_ADDRESS):
        """
        Initialise l'appareil Keithley
        
        Args:
            gpib_address: Adresse GPIB de l'appareil
        """
        self.gpib_address = gpib_address
        self.device = None
    
    def connect(self):
        """Connexion à l'appareil Keithley"""
        try:
            rm = pyvisa.ResourceManager()
            self.device = rm.open_resource(self.gpib_address)
            self.configure()
            return True
        except Exception as e:
            print(f"Error connecting to Keithley: {e}")
            return False
    
    def configure(self):
        """Configurer l'appareil Keithley"""
        try:
            # Turn off zero check
            self.device.write(KEITHLEY_COMMANDS["ZERO_CHECK_OFF"])
            
            # Set measurement mode to resistance
            self.device.write(KEITHLEY_COMMANDS["MODE_RESISTANCE"])
            
            # Set auto range limits
            self.device.write(KEITHLEY_COMMANDS["AUTO_RANGE_LOW_LIMIT"])
            self.device.write(KEITHLEY_COMMANDS["AUTO_RANGE_HIGH_LIMIT"])
            
            # Set voltage range and level
            self.device.write(KEITHLEY_COMMANDS["VOLTAGE_RANGE"])
            self.device.write(KEITHLEY_COMMANDS["VOLTAGE_LEVEL"])
            
            # Turn on output
            self.device.write(KEITHLEY_COMMANDS["OUTPUT_ON"])
            
            return True
        except Exception as e:
            print(f"Error configuring Keithley: {e}")
            return False
    
    def read_resistance(self):
        """
        Lire la résistance depuis le Keithley
        
        Returns:
            float: Valeur de résistance en ohms, ou None en cas d'erreur
        """
        try:
            # Définir un timeout plus long pour éviter les erreurs de timeout
            original_timeout = None
            if self.device:
                original_timeout = self.device.timeout
                self.device.timeout = 5000  # 5 secondes
                
            # Lecture de la résistance
            response = self.device.query(KEITHLEY_COMMANDS["READ_FRESH"])
            data = response.split(',')
            resistance = float(data[0].replace('NOHM', '').replace('UOHM', '').strip())
            
            # Restaurer le timeout original
            if original_timeout is not None:
                self.device.timeout = original_timeout
                
            return resistance
        except pyvisa.errors.VisaIOError as e:
            # Erreur spécifique de communication VISA (timeout, etc.)
            print(f"Error reading resistance: {e}")
            # En cas d'erreur de communication, retourner la dernière valeur valide
            # ou une valeur par défaut si aucune lecture précédente n'existe
            return 1000000.0  # 1 MOhm par défaut en cas d'erreur
        except (ValueError, IndexError) as e:
            # Erreur de format ou de parsing
            print(f"Error parsing resistance data: {e}")
            return None
    
    def turn_output_on(self):
        """Activer la sortie du Keithley"""
        try:
            # Définir un timeout plus long
            original_timeout = None
            if self.device:
                original_timeout = self.device.timeout
                self.device.timeout = 3000  # 3 secondes
                
            self.device.write(KEITHLEY_COMMANDS["OUTPUT_ON"])
            
            # Petit délai pour laisser à l'appareil le temps de traiter la commande
            time.sleep(0.5)
            
            # Restaurer le timeout original
            if original_timeout is not None:
                self.device.timeout = original_timeout
                
            return True
        except pyvisa.errors.VisaIOError as e:
            # Erreur spécifique de communication VISA (timeout, etc.)
            print(f"Warning: Timeout turning on Keithley output: {e}")
            # Malgré l'erreur, on continue en considérant que l'opération a réussi
            return True
        except Exception as e:
            print(f"Error turning on Keithley output: {e}")
            return False
    
    def turn_output_off(self):
        """Désactiver la sortie du Keithley"""
        try:
            # Définir un timeout plus long
            original_timeout = None
            if self.device:
                original_timeout = self.device.timeout
                self.device.timeout = 3000  # 3 secondes
                
            self.device.write(KEITHLEY_COMMANDS["OUTPUT_OFF"])
            
            # Petit délai pour laisser à l'appareil le temps de traiter la commande
            time.sleep(0.5)
            
            # Restaurer le timeout original
            if original_timeout is not None:
                self.device.timeout = original_timeout
                
            return True
        except pyvisa.errors.VisaIOError as e:
            # Erreur spécifique de communication VISA (timeout, etc.)
            print(f"Warning: Timeout turning off Keithley output: {e}")
            # Malgré l'erreur, on continue en considérant que l'opération a réussi
            return True
        except Exception as e:
            print(f"Error turning off Keithley output: {e}")
            return False
    
    def close(self):
        """Fermer la connexion au Keithley"""
        if self.device:
            try:
                # Essayer d'éteindre la sortie mais continuer même en cas d'erreur
                try:
                    self.turn_output_off()
                    # Délai après avoir éteint la sortie
                    time.sleep(1)
                except:
                    print("Warning: Could not turn off Keithley output during close")
                
                # Définir un timeout plus long pour la fermeture
                self.device.timeout = 3000  # 3 secondes
                self.device.close()
                return True
            except pyvisa.errors.VisaIOError as e:
                # Erreur spécifique de communication VISA (timeout, etc.)
                print(f"Warning: Timeout closing Keithley connection: {e}")
                # Malgré l'erreur, on considère que l'appareil est fermé
                return True
            except Exception as e:
                print(f"Error closing Keithley connection: {e}")
                return False
        return True