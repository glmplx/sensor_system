"""
Interface pour l'appareil Arduino
"""

import serial
import time

class ArduinoDevice:
    """Interface pour l'appareil Arduino qui mesure le CO2, la température et l'humidité"""
    
    def __init__(self, port=None, baud_rate=115200, timeout=2):
        """
        Initialise l'appareil Arduino
        
        Args:
            port: Port série à connecter
            baud_rate: Vitesse en bauds pour la connexion série
            timeout: Délai d'expiration pour les opérations série en secondes
        """
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.device = None
    
    def connect(self):
        """Connexion à l'appareil Arduino"""
        try:
            if not self.port:
                raise ValueError("Serial port not specified")
            
            self.device = serial.Serial(self.port, self.baud_rate, timeout=self.timeout)
            return True
        except Exception as e:
            print(f"Error connecting to Arduino: {e}")
            return False
    
    def read_line(self):
        """
        Lire une ligne depuis l'Arduino
        
        Returns:
            str: La ligne lue, ou None en cas d'erreur
        """
        
        try:
            if not self.device:
                return None
                
            # Vérifier s'il y a des données disponibles
            if self.device.in_waiting > 0:
                line = self.device.readline().decode('utf-8').strip()
                return line
            # Si pas de données disponibles, retourner None immédiatement
            return None
        except UnicodeDecodeError:
            # Si on a une erreur de décodage, essayer avec un autre encodage ou ignorer
            try:
                line = self.device.readline().decode('latin-1').strip()
                return line
            except Exception:
                print("Error decoding Arduino data")
                return None
        except Exception as e:
            print(f"Erreur lors de la lecture depuis Arduino: {e}")
            return None
    
    def send_command(self, command):
        """
        Envoyer une commande à l'Arduino
        
        Args:
            command: La commande à envoyer
            
        Returns:
            bool: True si la commande a été envoyée avec succès, False sinon
        """
        try:
            if not self.device:
                return False
            
            self.device.write(command.encode('utf-8'))
            return True
        except Exception as e:
            print(f"Error sending command to Arduino: {e}")
            return False
    
    def close(self):
        """Fermer la connexion à l'Arduino"""
        if self.device:
            try:
                self.device.close()
                return True
            except Exception as e:
                print(f"Error closing Arduino connection: {e}")
                return False
        return True