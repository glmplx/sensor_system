"""
Interface pour l'appareil de régénération
"""

import serial
import time

class RegenDevice:
    """Interface pour l'appareil de régénération de résistance"""
    
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
        """Connexion à l'appareil de régénération"""
        try:
            if not self.port:
                raise ValueError("Serial port not specified")
            
            self.device = serial.Serial(self.port, self.baud_rate, timeout=self.timeout)
            return True
        except Exception as e:
            print(f"Error connecting to regeneration device: {e}")
            return False
    
    def read_variable(self, command, address):
        """
        Lire une variable depuis l'appareil de régénération
        
        Args:
            command: Caractère de commande (par exemple, 'L')
            address: Caractère d'adresse (par exemple, 'a', 'b', 'c', 'd')
            
        Returns:
            str: La valeur lue, ou None en cas d'erreur
        """
        try:
            if not self.device:
                return None
            
            self.device.write(command.encode())
            self.device.write(address.encode())
            time.sleep(0.1)
            response = self.device.read(self.device.in_waiting).decode().strip()
            
            if response.startswith('L'):
                cleaned_response = response[1:].strip()
                if cleaned_response.startswith('a') or cleaned_response.startswith('d'):
                    cleaned_response = cleaned_response[1:].strip()
                if '.' not in cleaned_response:
                    cleaned_response += '.0'
                return cleaned_response
            return "0.0"
        except Exception as e:
            print(f"Error reading variable from regeneration device: {e}")
            return None
    
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
            
            command_str = f"{command}{address}{value}\n"
            self.device.write(command_str.encode())
            
            # Attendre un court instant pour s'assurer que la commande est traitée
            time.sleep(0.1)
            
            # Vider tout buffer de réception si nécessaire
            if self.device.in_waiting > 0:
                response = self.device.read(self.device.in_waiting)
                
            return True
        except Exception as e:
            print(f"Error writing parameter to regeneration device: {e}")
            return False
    
    def close(self):
        """Fermer la connexion à l'appareil de régénération"""
        if self.device:
            try:
                self.device.close()
                return True
            except Exception as e:
                print(f"Error closing regeneration device connection: {e}")
                return False
        return True