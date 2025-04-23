; Système de capteurs - Script d'installation NSIS
; Créé automatiquement pour simplifier l'installation

!include "MUI2.nsh"

; Définition des informations générales
Name "Système de capteurs IRSN"
OutFile "SensorSystemInstaller.exe"
InstallDir "$PROGRAMFILES\IRSN\SensorSystem"
InstallDirRegKey HKCU "Software\IRSN\SensorSystem" ""
RequestExecutionLevel admin

; Pages de l'interface utilisateur
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Pages de désinstallation
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Langues
!insertmacro MUI_LANGUAGE "French"

; Fonction d'initialisation
Function .onInit
  ; Par défaut, proposer l'installation dans Program Files
  StrCpy $INSTDIR "$PROGRAMFILES\IRSN\SensorSystem"
FunctionEnd

; Section principale d'installation
Section "Installation principale" SecMain
  SetOutPath "$INSTDIR"
  
  ; Copier tous les fichiers de l'exécutable
  File /r "dist\*.*"
  
  ; Créer le dossier pour les données Excel
  CreateDirectory "$INSTDIR\donnees_excel"
  
  ; Créer un raccourci dans le Menu Démarrer
  CreateDirectory "$SMPROGRAMS\IRSN"
  CreateShortcut "$SMPROGRAMS\IRSN\Système de capteurs.lnk" "$INSTDIR\SensorSystem.exe"
  CreateShortcut "$DESKTOP\Système de capteurs IRSN.lnk" "$INSTDIR\SensorSystem.exe"
  
  ; Écrire les informations d'installation dans le registre
  WriteRegStr HKCU "Software\IRSN\SensorSystem" "" $INSTDIR
  
  ; Créer la désinstallation
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\IRSN_SensorSystem" "DisplayName" "Système de capteurs IRSN"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\IRSN_SensorSystem" "UninstallString" "$\"$INSTDIR\Uninstall.exe$\""
SectionEnd

; Section de désinstallation
Section "Uninstall"
  ; Supprimer les fichiers et dossiers
  Delete "$SMPROGRAMS\IRSN\Système de capteurs.lnk"
  Delete "$DESKTOP\Système de capteurs IRSN.lnk"
  RMDir /r "$SMPROGRAMS\IRSN"
  
  ; Demander à l'utilisateur s'il souhaite conserver les données
  MessageBox MB_YESNO "Voulez-vous conserver les données Excel? Cliquez sur 'Oui' pour les conserver, 'Non' pour tout supprimer." IDYES KeepData
  RMDir /r "$INSTDIR\donnees_excel"
  
  KeepData:
  ; Supprimer les autres fichiers
  Delete "$INSTDIR\Uninstall.exe"
  RMDir /r "$INSTDIR"
  
  ; Supprimer les entrées du registre
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\IRSN_SensorSystem"
  DeleteRegKey HKCU "Software\IRSN\SensorSystem"
SectionEnd