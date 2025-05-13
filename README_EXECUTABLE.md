# Système de capteurs - Exécutable

Cet exécutable contient le système complet de capteurs. Il ne nécessite pas d'installation de Python ni de bibliothèques supplémentaires.

## Utilisation

1. Double-cliquez sur le fichier SensorSystem.exe pour lancer l'application
2. Sélectionnez les ports COM pour les différents appareils
3. Choisissez le mode (Manuel ou Automatique)
4. Cliquez sur "Lancer le programme"

## Configuration persistante

L'exécutable utilise un fichier de configuration externe `sensor_config.json` qui se trouve dans le même dossier que l'exécutable. Ce fichier est créé automatiquement lors de la première exécution et contient tous les paramètres du système.

Lorsque vous modifiez des paramètres via l'interface (menu "Paramètres"), les changements sont automatiquement sauvegardés dans ce fichier. Ils seront donc conservés lorsque vous redémarrerez l'application.

Si vous souhaitez réinitialiser les paramètres aux valeurs par défaut, il vous suffit de supprimer le fichier `sensor_config.json` et de redémarrer l'application.

## Résolution des problèmes

- Si l'exécutable ne se lance pas, essayez de le déplacer dans un dossier dont le chemin ne contient pas de caractères spéciaux
- Pour les problèmes de connexion aux appareils, vérifiez que les pilotes des ports COM sont correctement installés
- Si les paramètres ne sont pas sauvegardés, vérifiez que vous avez les droits d'écriture dans le dossier
- Pour tout autre problème, consultez la documentation complète
