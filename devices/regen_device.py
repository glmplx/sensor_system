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
                raise ValueError("Port série non spécifié")
            
            self.device = serial.Serial(self.port, self.baud_rate, timeout=self.timeout)
            return True
        except Exception as e:
            print(f"Erreur lors de la connexion à l'appareil de régénération: {e}")
            return False
    
    async def _async_delay(self, seconds):
        """Délai asynchrone pour ne pas bloquer l'exécution"""
        import asyncio
        await asyncio.sleep(seconds)
    
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
            
            # Définir un timeout plus court pour cette opération
            original_timeout = self.device.timeout
            self.device.timeout = 0.5  # Timeout réduit pour éviter les blocages
            
            self.device.write(command.encode())
            self.device.write(address.encode())
            
            # Au lieu de time.sleep bloquant, on utilise une approche non bloquante
            # On attend un court instant que les données soient disponibles
            import select
            readable, _, _ = select.select([self.device], [], [], 0.1)
            
            if readable:
                response = self.device.read(self.device.in_waiting).decode().strip()
                
                # Restaurer le timeout original
                self.device.timeout = original_timeout
                
                if response.startswith('L'):
                    cleaned_response = response[1:].strip()
                    if cleaned_response.startswith('a') or cleaned_response.startswith('d'):
                        cleaned_response = cleaned_response[1:].strip()
                    if '.' not in cleaned_response:
                        cleaned_response += '.0'
                    return cleaned_response
                return "0.0"
            else:
                # Restaurer le timeout original même si aucune donnée n'est disponible
                self.device.timeout = original_timeout
                return "0.0"
                
        except Exception as e:
            print(f"Erreur lors de la lecture de variable depuis l'appareil de régénération: {e}")
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
            
            # Au lieu de time.sleep bloquant, on utilise une approche non bloquante
            # On attend un court instant que les données soient disponibles
            import select
            readable, _, _ = select.select([self.device], [], [], 0.1)
            
            # Vider tout buffer de réception si nécessaire
            if readable and self.device.in_waiting > 0:
                response = self.device.read(self.device.in_waiting)
                
            return True
        except Exception as e:
            print(f"Erreur lors de l'écriture de paramètre dans l'appareil de régénération: {e}")
            return False
    
    def close(self):
        """Fermer la connexion à l'appareil de régénération"""
        if self.device:
            try:
                self.device.close()
                self.device = None  # Libérer explicitement la référence
                return True
            except Exception as e:
                print(f"Erreur lors de la fermeture de la connexion à l'appareil de régénération: {e}")
                self.device = None  # Libérer la référence même en cas d'erreur
                return False
        return True