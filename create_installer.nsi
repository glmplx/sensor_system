; Système de capteurs - Script d'installation NSIS
; Créé automatiquement pour simplifier l'installation

!include "MUI2.nsh"

; Définition des informations générales
Name "Systeme de capteurs ASNR"
OutFile "SensorSystemInstaller.exe"
InstallDir "$PROGRAMFILES\ASNR\SensorSystem"
InstallDirRegKey HKCU "Software\ASNR\SensorSystem" ""
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
  StrCpy $INSTDIR "$PROGRAMFILES\ASNR\SensorSystem"
FunctionEnd

; Section principale d'installation
Section "Installation principale" SecMain
  SetOutPath "$INSTDIR"
  
  ; Copier tous les fichiers de l'exécutable
  File /r "dist\*.*"
  
  ; Créer le dossier pour les données Excel
  CreateDirectory "$INSTDIR\donnees_excel"
  
  ; Créer un raccourci dans le Menu Démarrer
  CreateDirectory "$SMPROGRAMS\ASNR"
  CreateShortcut "$SMPROGRAMS\ASNR\Systeme de capteurs.lnk" "$INSTDIR\SensorSystem.exe"
  CreateShortcut "$DESKTOP\Systeme de capteurs ASNR.lnk" "$INSTDIR\SensorSystem.exe"
  
  ; Écrire les informations d'installation dans le registre
  WriteRegStr HKCU "Software\ASNR\SensorSystem" "" $INSTDIR
  
  ; Créer la désinstallation
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ASNR_SensorSystem" "DisplayName" "Systeme de capteurs ASNR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ASNR_SensorSystem" "UninstallString" "$\"$INSTDIR\Uninstall.exe$\""
SectionEnd

; Section de désinstallation
Section "Uninstall"
  ; Supprimer les fichiers et dossiers
  Delete "$SMPROGRAMS\ASNR\Systeme de capteurs.lnk"
  Delete "$DESKTOP\Systeme de capteurs ASNR.lnk"
  RMDir /r "$SMPROGRAMS\ASNR"
  
  ; Demander à l'utilisateur s'il souhaite conserver les données
  MessageBox MB_YESNO "Voulez-vous conserver les données Excel? Cliquez sur 'Oui' pour les conserver, 'Non' pour tout supprimer." IDYES KeepData
  RMDir /r "$INSTDIR\donnees_excel"
  
  KeepData:
  ; Supprimer les autres fichiers
  Delete "$INSTDIR\Uninstall.exe"
  RMDir /r "$INSTDIR"
  
  ; Supprimer les entrées du registre
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ASNR_SensorSystem"
  DeleteRegKey HKCU "Software\ASNR\SensorSystem"
SectionEnd