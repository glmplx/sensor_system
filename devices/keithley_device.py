"""
Interface pour l'appareil Keithley 6517.
Gère la communication, la configuration et les mesures de résistance via l'instrument GPIB.
Auteur: Guillaume Pailloux
"""

import time
import pyvisa
import sys
from core.constants import (
    KEITHLEY_COMMANDS,
    KEITHLEY_GPIB_ADDRESS,
    KEITHLEY_READ_TIMEOUT,
    KEITHLEY_OPERATION_TIMEOUT,
    KEITHLEY_VISA_ERROR_CLOSING_FAILED,
    KEITHLEY_POLARIZATION_VOLTAGE
)

class KeithleyDevice:
    """Interface pour l'électromètre Keithley 6517 permettant la mesure précise de résistance électrique"""
    
    # Gestionnaire d'exceptions personnalisé pour intercepter les erreurs VISA non gérées
    def _custom_excepthook(self, etype, evalue, etraceback):
        # Vérifie si l'erreur est une VisaIOError avec le code spécifique VI_ERROR_CLOSING_FAILED
        if etype == pyvisa.errors.VisaIOError and (
            str(getattr(evalue, 'error_code', '')) == KEITHLEY_VISA_ERROR_CLOSING_FAILED or
            'VI_ERROR_CLOSING_FAILED' in str(evalue)
        ):
            if not hasattr(self, '_closing_error_handled') or not self._closing_error_handled:
                print("Info: Appareil Keithley déconnecté de manière inattendue.")
        else:
            # Pour les autres types d'erreurs, utiliser le gestionnaire d'exceptions par défaut
            self._original_excepthook(etype, evalue, etraceback)
    
    def __init__(self, gpib_address=KEITHLEY_GPIB_ADDRESS):
        """
        Initialise l'appareil Keithley
        
        Args:
            gpib_address: Adresse GPIB de l'appareil
        """
        self.gpib_address = gpib_address
        self.device = None
        # Indicateur pour éviter la duplication des messages d'erreur lors du garbage collection
        self._closing_error_handled = False
        
        # Installe le gestionnaire d'exceptions personnalisé pour capturer les erreurs VISA
        self._original_excepthook = sys.excepthook
        sys.excepthook = lambda etype, evalue, etb: self._custom_excepthook(etype, evalue, etb)
    
    def connect(self, polarization_voltage=None):
        """
        Établit la connexion à l'appareil Keithley via GPIB
        
        Args:
            polarization_voltage: Tension de polarisation en Volts à utiliser.
                                  Si None, utilise la valeur par défaut définie dans les constantes.
        
        Returns:
            bool: True si la connexion a réussi, False sinon
        """
        try:
            rm = pyvisa.ResourceManager()
            self.device = rm.open_resource(self.gpib_address)
            self.configure(polarization_voltage)
            return True
        except Exception as e:
            print(f"Erreur de connexion à l'appareil Keithley: {e}")
            return False
    
    def configure(self, polarization_voltage=None):
        """
        Configure l'appareil Keithley avec les paramètres nécessaires pour les mesures de résistance
        
        Args:
            polarization_voltage: Tension de polarisation en Volts à utiliser. 
                                  Si None, utilise la valeur par défaut définie dans les constantes.
        
        Returns:
            bool: True si la configuration a réussi, False sinon
        """
        try:
            # Utiliser la tension spécifiée ou la valeur par défaut
            voltage = polarization_voltage if polarization_voltage is not None else KEITHLEY_POLARIZATION_VOLTAGE
            
            # Désactiver la vérification zéro
            self.device.write(KEITHLEY_COMMANDS["ZERO_CHECK_OFF"])
            
            # Définir le mode de mesure sur résistance
            self.device.write(KEITHLEY_COMMANDS["MODE_RESISTANCE"])
            
            # Définir les limites de gamme automatique
            self.device.write(KEITHLEY_COMMANDS["AUTO_RANGE_LOW_LIMIT"])
            self.device.write(KEITHLEY_COMMANDS["AUTO_RANGE_HIGH_LIMIT"])
            
            # Définir la plage et le niveau de tension
            self.device.write(KEITHLEY_COMMANDS["VOLTAGE_RANGE"])
            self.device.write(KEITHLEY_COMMANDS["VOLTAGE_LEVEL"].format(voltage))
            
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
                self.device.timeout = KEITHLEY_READ_TIMEOUT

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
            
            # Marquer l'appareil comme non disponible pour éviter d'autres erreurs
            # et déclencher la pause des mesures dans l'interface
            self.device = None
            
            # Signal à l'interface que l'appareil s'est déconnecté
            print("Keithley déconnecté - marquer comme indisponible")
            
            # Retourner None pour indiquer une déconnexion
            return None
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
                self.device.timeout = KEITHLEY_OPERATION_TIMEOUT

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
                self.device.timeout = KEITHLEY_OPERATION_TIMEOUT

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
                self.device.timeout = KEITHLEY_OPERATION_TIMEOUT
                self.device.close()
                self.device = None  # Libérer explicitement la référence
                return True
            except pyvisa.errors.VisaIOError as e:
                # Vérifier si c'est l'erreur de fermeture spécifique (VI_ERROR_CLOSING_FAILED)
                if str(e.error_code) == KEITHLEY_VISA_ERROR_CLOSING_FAILED or 'VI_ERROR_CLOSING_FAILED' in str(e):
                    # Marquer que cette erreur a été gérée pour éviter les messages d'erreur lors du garbage collection
                    self._closing_error_handled = True
                    print("Info: Appareil Keithley déconnecté ou retiré.")
                else:
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
    
    def __del__(self):
        """Destructeur - assure que la connexion est fermée lors de la suppression de l'objet"""
        try:
            self.close()
            # Restaurer le hook d'exception original
            if hasattr(self, '_original_excepthook') and sys.excepthook is not None:
                sys.excepthook = self._original_excepthook
        except pyvisa.errors.VisaIOError as e:
            # Intercepter spécifiquement l'erreur VI_ERROR_CLOSING_FAILED
            if str(getattr(e, 'error_code', '')) == KEITHLEY_VISA_ERROR_CLOSING_FAILED or 'VI_ERROR_CLOSING_FAILED' in str(e):
                self._closing_error_handled = True
                print("Info: Appareil Keithley déconnecté lors de la fermeture du programme.")
            # Ne pas propager l'exception pour éviter le traceback
        except Exception:
            # Ne pas propager d'autres exceptions non plus
            pass