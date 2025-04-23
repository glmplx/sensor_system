#!/usr/bin/env python
"""
Point d'entrée principal pour l'application de système de capteurs
"""

import sys
import traceback
import time

def main():
    """Point d'entrée principal pour l'application"""
    try:
        # Import here to catch import errors
        from ui.menu import MenuUI
        menu = MenuUI()
        menu.run()
    except Exception as e:
        # Print error information
        print(f"ERROR: {str(e)}")
        print("Traceback:")
        traceback.print_exc()
        # Keep console open
        print("\nAppuyez sur Entrée pour fermer le programme...")
        input()  # Attend que l'utilisateur appuie sur Entrée au lieu de bloquer avec time.sleep
        sys.exit(1)

if __name__ == "__main__":
    main()