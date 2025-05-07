#!/usr/bin/env python
"""
Point d'entrée principal pour l'application de système de capteurs.
Lance l'interface de menu qui permet de sélectionner le mode d'opération et les paramètres.
Auteur: Guillaume Pailloux
"""

import sys
import traceback
import time

def main():
    """
    Point d'entrée principal pour l'application.
    Initialise l'interface utilisateur et gère les exceptions globales.
    """
    try:
        # Importer ici pour capturer les erreurs d'importation
        from ui.menu import MenuUI
        menu = MenuUI()
        menu.run()
    except Exception as e:
        # Afficher les informations d'erreur
        print(f"ERROR: {str(e)}")
        print("Traceback:")
        traceback.print_exc()
        # Garder la console ouverte pour que l'utilisateur puisse lire l'erreur
        print("\nAppuyez sur Entrée pour fermer le programme...")
        input()  # Attend que l'utilisateur appuie sur Entrée pour confirmer qu'il a lu le message d'erreur
        sys.exit(1)

if __name__ == "__main__":
    main()