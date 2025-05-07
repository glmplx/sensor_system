"""
Interface pour l'appareil de régénération.
Gère la communication série avec l'appareil qui contrôle la température de la résistance.
"""

import serial
import time
from serial.serialutil import SerialException

class RegenDevice:
    """Interface pour l'appareil de régénération de résistance, permettant de contrôler et lire la température"""
    
    def __init__(self, port=None, baud_rate=115200, timeout=2):
        """
        Initialise l'appareil de régénération
        
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
        Établit la connexion à l'appareil de régénération
        
        Returns:
            bool: True si la connexion a réussi, False sinon
        """
        try:
            if not self.port:
                raise ValueError("Port série non spécifié")
            
            self.device = serial.Serial(self.port, self.baud_rate, timeout=self.timeout)
            return True
        except Exception as e:
            print(f"Erreur de connexion à l'appareil de régénération: {e}")
            return False
    
    def read_variable(self, command, address):
        """
        Lire une variable depuis l'appareil de régénération
        
        Args:
            command: Caractère de commande (par exemple, 'L')
            address: Caractère d'adresse (par exemple, 'a', 'b', 'c', 'd')
            
        Returns:
            str: La valeur lue, ou "0.0" en cas d'erreur (jamais None)
        """
        try:
            if not self.device:
                return "0.0"  # Retourne une chaîne par défaut au lieu de None
            
            # Vérifier si le port est encore ouvert
            if not self.device.is_open:
                print("Port série fermé détecté lors de la lecture")
                self.device = None
                return "0.0"
                
            # Vider le tampon d'entrée avant d'envoyer la commande
            self.device.reset_input_buffer()
            
            # Envoyer la commande complète
            self.device.write(f"{command}{address}".encode())
            time.sleep(0.2)  # Délai pour donner le temps au périphérique de répondre
            
            # Vérifier encore une fois si le port est ouvert avant la lecture
            if not self.device.is_open:
                print("Port série fermé détecté après écriture")
                self.device = None
                return "0.0"
            
            # Attendre que les données soient disponibles avec plusieurs tentatives
            attempts = 0
            while self.device.in_waiting == 0 and attempts < 5:
                time.sleep(0.1)  # Attendre 100ms
                attempts += 1
                
            if self.device.in_waiting == 0:
                print(f"Aucune donnée reçue après {attempts} tentatives")
                
            response = self.device.read(self.device.in_waiting).decode().strip()
            
            if response.startswith('L'):
                cleaned_response = response[1:].strip()
                if cleaned_response.startswith('a') or cleaned_response.startswith('d') or cleaned_response.startswith('c'):
                    cleaned_response = cleaned_response[1:].strip()
                if '.' not in cleaned_response:
                    cleaned_response += '.0'
                return cleaned_response if cleaned_response else "0.0"  # Vérification supplémentaire
            return "0.0"
        except (OSError, IOError, serial.SerialException, PermissionError) as e:
            # Erreurs de communication série - probablement déconnecté
            print(f"Error reading variable from regeneration device: {e}")
            # Marquer l'appareil comme non disponible
            self.device = None
            return "0.0"
        except Exception as e:
            print(f"Unexpected error reading from regeneration device: {e}")
            return "0.0"  # Retourne une chaîne par défaut au lieu de None
    
    def write_parameter(self, command, address, value):
        """
        Écrire un paramètre dans l'appareil de régénération
        
        Args:
            command: Caractère de commande (par exemple, 'e')
            address: Caractère d'adresse (par exemple, 'a', 'b')
            value: Valeur à écrire
            
        Returns:
            bool: True si le paramètre a été écrit avec succès, False sinon
        """
        try:
            if not self.device:
                return False
                
            # Vérifier si le port est encore ouvert
            if not self.device.is_open:
                print("Port série fermé détecté lors de l'écriture")
                self.device = None
                return False
            
            command_str = f"{command}{address}{value}\n"
            self.device.write(command_str.encode())
            
            # Attendre un court instant pour s'assurer que la commande est traitée
            time.sleep(0.1)
            
            # Vérifier encore une fois si le port est ouvert
            if not self.device.is_open:
                print("Port série fermé détecté après envoi de commande")
                self.device = None
                return False
            
            # Vider tout buffer de réception si nécessaire
            if self.device.in_waiting > 0:
                response = self.device.read(self.device.in_waiting)
                
            return True
        except (OSError, IOError, serial.SerialException, PermissionError) as e:
            # Erreurs de communication série - probablement déconnecté
            print(f"Error writing parameter to regeneration device: {e}")
            # Marquer l'appareil comme non disponible
            self.device = None
            return False
        except Exception as e:
            print(f"Unexpected error writing to regeneration device: {e}")
            return False
    
    def close(self):
        """
        Ferme proprement la connexion à l'appareil de régénération
        
        Returns:
            bool: True si la fermeture a réussi ou si l'appareil était déjà fermé, False en cas d'erreur
        """
        if self.device:
            try:
                # Vérifier si le port est déjà fermé avant d'essayer de le fermer
                if self.device.is_open:
                    self.device.close()
                # Marquer explicitement l'appareil comme déconnecté
                self.device = None
                return True
            except Exception as e:
                print(f"Error closing regeneration device connection: {e}")
                # Marquer l'appareil comme déconnecté même en cas d'erreur
                self.device = None
                return False
        return True