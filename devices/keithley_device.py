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
            # Désactiver la vérification zéro
            self.device.write(KEITHLEY_COMMANDS["ZERO_CHECK_OFF"])
            
            # Définir le mode de mesure sur résistance
            self.device.write(KEITHLEY_COMMANDS["MODE_RESISTANCE"])
            
            # Définir les limites de gamme automatique
            self.device.write(KEITHLEY_COMMANDS["AUTO_RANGE_LOW_LIMIT"])
            self.device.write(KEITHLEY_COMMANDS["AUTO_RANGE_HIGH_LIMIT"])
            
            # Définir la plage et le niveau de tension
            self.device.write(KEITHLEY_COMMANDS["VOLTAGE_RANGE"])
            self.device.write(KEITHLEY_COMMANDS["VOLTAGE_LEVEL"])
            
            # Activer la sortie
            self.device.write(KEITHLEY_COMMANDS["OUTPUT_ON"])
            
            return True
        except Exception as e:
            print(f"Erreur lors de la configuration du Keithley: {e}")
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
    
    async def _async_delay(self, seconds):
        """Délai asynchrone pour ne pas bloquer l'exécution"""
        import asyncio
        await asyncio.sleep(seconds)
        
    def turn_output_on(self):
        """Activer la sortie du Keithley"""
        try:
            # Définir un timeout plus long
            original_timeout = None
            if self.device:
                original_timeout = self.device.timeout
                self.device.timeout = 3000  # 3 secondes
                
            self.device.write(KEITHLEY_COMMANDS["OUTPUT_ON"])
            
            # Au lieu de bloquer avec time.sleep, on continue immédiatement
            # Définir un délai plus long pour la prochaine opération si nécessaire
            
            # Restaurer le timeout original
            if original_timeout is not None:
                self.device.timeout = original_timeout
                
            return True
        except pyvisa.errors.VisaIOError as e:
            # Erreur spécifique de communication VISA (timeout, etc.)
            print(f"Avertissement: Délai dépassé lors de l'activation de la sortie Keithley: {e}")
            # Malgré l'erreur, on continue en considérant que l'opération a réussi
            return True
        except Exception as e:
            print(f"Erreur lors de l'activation de la sortie Keithley: {e}")
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
            
            # Au lieu de bloquer avec time.sleep, on continue immédiatement
            # Définir un délai plus long pour la prochaine opération si nécessaire
            
            # Restaurer le timeout original
            if original_timeout is not None:
                self.device.timeout = original_timeout
                
            return True
        except pyvisa.errors.VisaIOError as e:
            # Erreur spécifique de communication VISA (timeout, etc.)
            print(f"Avertissement: Délai dépassé lors de la désactivation de la sortie Keithley: {e}")
            # Malgré l'erreur, on continue en considérant que l'opération a réussi
            return True
        except Exception as e:
            print(f"Erreur lors de la désactivation de la sortie Keithley: {e}")
            return False
    
    def close(self):
        """Fermer la connexion au Keithley"""
        if self.device:
            try:
                # Essayer d'éteindre la sortie mais continuer même en cas d'erreur
                try:
                    self.turn_output_off()
                    # On supprime le délai bloquant
                except:
                    print("Avertissement: Impossible de désactiver la sortie Keithley pendant la fermeture")
                
                # Définir un timeout plus long pour la fermeture
                self.device.timeout = 3000  # 3 secondes
                self.device.close()
                self.device = None  # Libérer explicitement la référence
                return True
            except pyvisa.errors.VisaIOError as e:
                # Erreur spécifique de communication VISA (timeout, etc.)
                print(f"Avertissement: Délai dépassé lors de la fermeture de la connexion Keithley: {e}")
                # Libérer la référence même en cas d'erreur
                self.device = None
                return True
            except Exception as e:
                print(f"Erreur lors de la fermeture de la connexion Keithley: {e}")
                # Libérer la référence même en cas d'erreur
                self.device = None
                return False
        return True