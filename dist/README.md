# Documentation du Système de Capteurs

*Auteur: Guillaume Pailloux*

## Table des matières

1. [Introduction](#introduction)
2. [Installation et prérequis](#installation-et-prérequis)
3. [Architecture du système](#architecture-du-système)
4. [Fonctionnalités principales](#fonctionnalités-principales)
5. [Interface utilisateur](#interface-utilisateur)
6. [Mode manuel](#mode-manuel)
7. [Mode automatique](#mode-automatique)
8. [Méthodes importantes](#méthodes-importantes)
9. [Dépannage](#dépannage)
10. [Exportation des données](#exportation-des-données)
11. [Configuration du système](#configuration-du-système)

## Introduction

Cette application est conçue pour gérer un système de capteurs qui mesure la conductance, le CO2, la température et l'humidité. Elle offre des fonctionnalités complètes pour la visualisation des données en temps réel, l'exécution de protocoles de mesure et l'exportation des données.

Le système permet de détecter automatiquement les variations de conductance, d'identifier les phases de stabilisation, et d'exécuter des protocoles de régénération du capteur lorsque nécessaire. L'ensemble du système peut fonctionner en mode manuel ou automatique selon les besoins de l'utilisateur.

## Installation et prérequis

### Matériel requis

1. **Appareils de mesure** :
   - Multimètre Keithley 6517 (avec interface GPIB)
   - Arduino avec capteur CO2, température et humidité
   - Carte de régénération avec contrôle de température

2. **Connexions** :
   - Adaptateur GPIB-USB pour le Keithley
   - Connexions USB pour l'Arduino et la carte de régénération

### Logiciels prérequis

- Python 3.6 ou supérieur
- Bibliothèques Python : matplotlib, numpy, openpyxl, pyserial, pyvisa

### Installation

1. Installer les bibliothèques requises :
   ```
   pip install matplotlib numpy openpyxl pyserial pyvisa
   ```

2. Connecter les appareils aux ports USB de l'ordinateur

3. Lancer l'application :
   ```
   python main.py
   ```

### Exécutable autonome

Un exécutable autonome peut être créé en utilisant :
```
python create_executable.py
```

Cela générera un fichier exécutable qui ne nécessite pas d'installation Python.

## Architecture du système

Le système est composé de plusieurs composants principaux :

1. **Dispositifs de mesure** :
   - **Keithley** : Appareil pour les mesures de résistance/conductance
   - **Arduino** : Appareil pour les mesures de CO2, température et humidité
   - **Appareil de régénération** : Contrôle la température de la résistance

2. **Gestionnaires** :
   - **MeasurementManager** : Gère la logique de collecte et de traitement des données
   - **PlotManager** : Gère l'interface graphique et l'affichage des données

3. **Applications** :
   - **Mode manuel** (manual_app.py) : Permet un contrôle manuel des mesures
   - **Mode automatique** (auto_app.py) : Exécute des mesures automatisées

## Fonctionnalités principales

### Mesures

- **Mesure de conductance** : Mesure la conductance électrique via l'appareil Keithley
- **Mesure de CO2, température et humidité** : Utilise un capteur connecté à l'Arduino
- **Mesure de température de résistance** : Contrôle et mesure la température de régénération

### Protocoles

- **Protocole CO2** : Mesure les variations de CO2 pendant un cycle de régénération
- **Protocole de conductance** : Mesure les variations de conductance pendant un cycle thermique
- **Protocole complet** : Combine les mesures de CO2 et de conductance

### Interface utilisateur

L'interface utilisateur est basée sur matplotlib et offre :
- Graphiques en temps réel pour chaque type de mesure
- Boutons de contrôle pour démarrer/arrêter les mesures
- Indicateurs d'état pour les différents capteurs
- Configuration des paramètres comme R0 et Tcons

#### Démarrage de l'application

Lors du démarrage, l'application affiche un menu initial qui permet de:

1. **Sélectionner les ports COM** pour l'Arduino et la carte de régénération
2. **Sélectionner le mode de fonctionnement** (manuel ou automatique)
3. **Sélectionner les types de mesure à activer** (en mode manuel)
4. **Accéder à l'aide** via le bouton "Aide" qui ouvre ce document

#### Navigation dans l'interface

- **Panneau supérieur** : Graphiques et visualisation des données
- **Panneau central** : Indicateurs d'état pour les capteurs et la détection
- **Panneau inférieur** : Boutons de contrôle et champs de configuration

#### Indicateurs visuels

- **LED verte** : Indique une détection positive ou un capteur activé
- **LED rouge** : Indique une absence de détection ou un capteur désactivé
- **Ligne verticale (en pointillé)** : Marque les événements importants sur les graphiques

## Mode manuel

Le mode manuel permet à l'utilisateur de contrôler individuellement chaque type de mesure :

1. **Contrôles de base** :
   - Boutons Start/Stop pour chaque type de mesure
   - Boutons RAZ (réinitialisation) pour chaque type de mesure
   - Bouton Start/Stop All pour contrôler toutes les mesures simultanément

2. **Protocoles** :
   - Protocole CO2 : Exécute un cycle complet de mesure de CO2
   - Protocole Conductance : Exécute un cycle de mesure de conductance
   - Protocole Complet : Combine les deux protocoles

3. **Contrôles supplémentaires** :
   - Configuration de R0 (résistance de référence)
   - Configuration de Tcons (température de consigne)
   - Contrôles de vérin (Push/Open, Retract/Close)

## Mode automatique

Le mode automatique permet d'exécuter des séquences prédéfinies de mesures sans intervention manuelle.

1. **Fonctionnement automatisé** :
   - Détection automatique de l'augmentation de conductance
   - Détection automatique de la stabilisation de conductance
   - Déclenchement automatique de la régénération lorsque nécessaire
   - Suivi continu des paramètres CO2, température et humidité

2. **Interface utilisateur du mode automatique** :
   - Bouton AUTO pour activer/désactiver les mesures automatiques
   - Bouton RAZ pour réinitialiser les graphiques et les données
   - Bouton de régénération pour déclencher manuellement le protocole
   - Indicateurs visuels pour le statut du capteur et l'état de la détection
   - Affichage temps réel de l'avancement du protocole de régénération

3. **Sauvegarde automatique** :
   - Création automatique d'un dossier de test horodaté
   - Sauvegarde périodique des données mesurées
   - Possibilité de renommer le dossier de données à la fin du test

## Méthodes importantes

### MeasurementManager

- `read_conductance()` : Lit les données de conductance depuis l'appareil Keithley
- `read_co2_temp_humidity()` : Lit les données de CO2, température et humidité depuis l'Arduino
- `read_res_temp()` : Lit les données de température de résistance
- `detect_conductance_increase()` : Détecte une augmentation significative de conductance
- `detect_conductance_stabilization()` : Détecte la stabilisation de la conductance
- `start_regeneration_protocol()` : Démarre le protocole de régénération
- `calculate_carbon_mass()` : Calcule la masse de carbone basée sur les mesures

### PlotManager

- `update_conductance_plot()` : Met à jour le graphique de conductance
- `update_co2_temp_humidity_plot()` : Met à jour les graphiques de CO2/température/humidité
- `update_res_temp_plot()` : Met à jour le graphique de température de résistance
- `configure_measurement_panels()` : Configure les panneaux de mesure visibles

## Dépannage

### Connexion aux appareils

Si les appareils ne sont pas détectés :
1. Vérifiez les connexions physiques
2. Vérifiez que les ports COM sont correctement spécifiés
3. Utilisez les boutons "Ajouter appareils" pour reconnecter les dispositifs

### Problèmes de mesure

- **Lectures instables** : Vérifiez les connexions et l'alimentation des appareils
- **Pas de détection d'augmentation** : Ajustez les paramètres de seuil dans constants.py
- **Erreurs de communication** : Redémarrez l'application et reconnectez les appareils

## Exportation des données

Les données sont automatiquement sauvegardées dans des fichiers Excel avec horodatage. Vous pouvez trouver ces fichiers dans le répertoire de l'application.

### Structure des fichiers Excel

1. **Données de conductance** :
   - Horodatage
   - Conductance (S)
   - Résistance (Ω)
   - Marqueurs d'événements (augmentation, stabilisation, etc.)

2. **Données CO2/Température/Humidité** :
   - Horodatage
   - CO2 (ppm)
   - Température ambiante (°C)
   - Humidité relative (%)
   - Marqueurs de régénération

3. **Données de température/résistance** :
   - Horodatage
   - Température de consigne (Tcons en °C)
   - Température mesurée (°C)
   - Marqueurs de régénération

### Localisation des données

Les fichiers Excel sont sauvegardés dans le répertoire défini par `EXCEL_BASE_DIR` dans le fichier constants.py. Par défaut, ces fichiers sont organisés dans des sous-dossiers par date et heure du test.

## Configuration du système

### Constants.py

Le fichier `constants.py` contient les paramètres de configuration du système, notamment:

- **Seuils de détection** : paramètres pour la détection d'augmentation et stabilisation
- **Protocole de régénération** : températures et durées pour chaque étape
- **Paramètres des appareils** : adresses, timeouts, et configurations par défaut

### Personnalisation

Pour personnaliser le comportement du système, vous pouvez modifier les valeurs dans constants.py:

```python
# Exemple de paramètres modifiables
STABILITY_DURATION = 2 * 60  # Durée de stabilité requise (secondes)
INCREASE_THRESHOLD = 0.02    # Seuil de détection d'augmentation
STABILITY_THRESHOLD = 0.01   # Seuil de stabilité
```

Il est recommandé de sauvegarder une copie du fichier avant toute modification.