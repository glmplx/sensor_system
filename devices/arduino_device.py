"""
Interface pour l'appareil Arduino.
Gère la communication avec l'Arduino qui mesure le CO2, la température et l'humidité.
Auteur: Guillaume Pailloux
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
        """
        Établit la connexion à l'appareil Arduino via le port série
        
        Returns:
            bool: True si la connexion a réussi, False sinon
        """
        try:
            if not self.port:
                raise ValueError("Port série non spécifié")
            
            self.device = serial.Serial(self.port, self.baud_rate, timeout=self.timeout)
            return True
        except Exception as e:
            print(f"Erreur de connexion à l'Arduino: {e}")
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
                
            # Vérifie s'il y a des données disponibles dans le buffer
            if self.device.in_waiting > 0:
                line = self.device.readline().decode('utf-8').strip()
                return line
            # Si aucune donnée n'est disponible, retourne None immédiatement sans bloquer
            return None
        except UnicodeDecodeError:
            # En cas d'erreur de décodage UTF-8, essaie avec l'encodage Latin-1 comme solution de repli
            try:
                line = self.device.readline().decode('latin-1').strip()
                return line
            except Exception:
                print("Erreur de décodage des données Arduino")
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
            print(f"Erreur lors de l'envoi de commande à l'Arduino: {e}")
            return False
    
    def close(self):
        """
        Ferme proprement la connexion à l'Arduino
        
        Returns:
            bool: True si la fermeture a réussi ou si l'appareil était déjà fermé, False en cas d'erreur
        """
        if self.device:
            try:
                self.device.close()
                return True
            except Exception as e:
                print(f"Erreur lors de la fermeture de la connexion Arduino: {e}")
                return False
        return True