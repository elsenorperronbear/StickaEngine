; NSIS installer script for StickaEngine
; Save this as installer.nsi and compile with makensis

; General settings
Name "StickaEngine"
OutFile "StickaEngine_Setup.exe"
InstallDir "$LOCALAPPDATA\StickaEngine\App"
RequestExecutionLevel admin

; Interface settings
InstallDirRegKey HKCU "Software\StickaEngine" "Install_Dir"
Icon "icon.ico"
UninstallIcon "icon.ico"

; Modern UI
!include "MUI2.nsh"
!include "LogicLib.nsh"

; Pages
!define MUI_ABORTWARNING
!define MUI_ICON "icon.ico"
!define MUI_UNICON "icon.ico"

; Main pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "license.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Uninstall pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "Spanish"
!insertmacro MUI_LANGUAGE "English"

; Main section
Section "Install"
    SetOutPath $INSTDIR
    
    ; Copy all files from dist directory
    File /r "dist\StickaEngine.exe"
    File /r "dist\_internal\*"
    
    ; Create version file
    FileWrite $INSTDIR\version.json '{"version": "1.0.0", "name": "StickaEngine"}'
    
    ; Create desktop shortcut
    CreateShortCut "$DESKTOP\StickaEngine.lnk" "$INSTDIR\StickaEngine.exe" 
    
    ; Create start menu shortcut
    CreateDirectory "$SMPROGRAMS\StickaEngine"
    CreateShortCut "$SMPROGRAMS\StickaEngine\StickaEngine.lnk" "$INSTDIR\StickaEngine.exe"
    CreateShortCut "$SMPROGRAMS\StickaEngine\Uninstall.lnk" "$INSTDIR\uninstall.exe"
    
    ; Write uninstall info
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\StickaEngine" \
        "DisplayName" "StickaEngine"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\StickaEngine" \
        "UninstallString" "\"$INSTDIR\uninstall.exe\""
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\StickaEngine" \
        "QuietUninstallString" "\"$INSTDIR\uninstall.exe\" /S"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\StickaEngine" \
        "DisplayVersion" "1.0.0"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\StickaEngine" \
        "Publisher" "StickaEngine Team"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\StickaEngine" \
        "Description" "Desktop sticker hub with iOS-style glassmorphism UI"
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\StickaEngine" \
        "NoModify" 1
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\StickaEngine" \
        "NoRepair" 1
    
    ; Store installation directory
    WriteRegStr HKCU "Software\StickaEngine" "Install_Dir" $INSTDIR
    
    ; Set environment variable (optional)
    ; Env::SetValue "PATH" "$INSTDIR" "$PATH" 0
SectionEnd

; Uninstall section
Section "Uninstall"
    ; Remove files
    Delete "$INSTDIR\StickaEngine.exe"
    Delete "$INSTDIR\version.json"
    Delete "$INSTDIR\uninstall.exe"
    RMDir "$INSTDIR\_internal"
    RMDir "$INSTDIR"
    
    ; Remove shortcuts
    Delete "$DESKTOP\StickaEngine.lnk"
    Delete "$SMPROGRAMS\StickaEngine\StickaEngine.lnk"
    Delete "$SMPROGRAMS\StickaEngine\Uninstall.lnk"
    RMDir "$SMPROGRAMS\StickaEngine"
    
    ; Remove registry entries
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\StickaEngine"
    DeleteRegKey HKCU "Software\StickaEngine"
    
    ; Remove data (optional - comment out to preserve user data)
    ; RMDir "$LOCALAPPDATA\StickaEngine"
SectionEnd

; Language strings for Spanish
LangString DESC_SecUninstall ${LANG_SPANISH} "Desinstala StickaEngine"
LangString DESC_SecMain ${LANG_SPANISH} "Archivos principales de StickaEngine"

; Language strings for English
LangString DESC_SecUninstall ${LANG_ENGLISH} "Uninstall StickaEngine"
LangString DESC_SecMain ${LANG_ENGLISH} "StickaEngine main files"
