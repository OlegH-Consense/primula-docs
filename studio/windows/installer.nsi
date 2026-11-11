; Installer of Primula Studio for Windows 10+ (stage 23.6).  NSIS 3 (Unicode), built by
; studio/windows/build-win.sh --installer:
;   makensis /DVERSION=0.4.11 /DSOURCE=<application directory> /DOUTFILE=<setup.exe> installer.nsi
;
; Per-user installation: no administrator rights, files in %LOCALAPPDATA%\Programs\Primula Studio
; (writable: the examples are built in place), registry keys only in HKCU.  Silent mode: /S,
; the directory: /D=C:\path (last argument).  The uninstaller removes the whole installation
; directory, so keep your own documents outside of it (copy the examples first).
; Reference: https://nsis.sourceforge.io/Docs/

Unicode true
!ifndef VERSION
  !define VERSION "0.0.0"
!endif
!ifndef SOURCE
  !error "Define SOURCE: the application directory (build-win/primula-studio)"
!endif
!ifndef OUTFILE
  !define OUTFILE "primula-studio-${VERSION}-setup.exe"
!endif

!define APP "Primula Studio"
!define UNINSTKEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\PrimulaStudio"
!define PROGID "Primula.Document"

Name "${APP}"
OutFile "${OUTFILE}"
InstallDir "$LOCALAPPDATA\Programs\${APP}"
InstallDirRegKey HKCU "Software\primula-docs\Installer" "InstallDir"
RequestExecutionLevel user
SetCompressor /SOLID lzma
ShowInstDetails nevershow
BrandingText "${APP} ${VERSION}"

VIProductVersion "${VERSION}.0"
VIAddVersionKey "ProductName" "${APP}"
VIAddVersionKey "FileDescription" "${APP} installer"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "LegalCopyright" "Apache-2.0"

!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"

!define MUI_ICON "${__FILEDIR__}\primula-studio.ico"
!define MUI_UNICON "${__FILEDIR__}\primula-studio.ico"
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\primula-studio.exe"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "Ukrainian"
!insertmacro MUI_LANGUAGE "Russian"

LangString SecMain ${LANG_ENGLISH} "Primula Studio and the translator"
LangString SecMain ${LANG_UKRAINIAN} "Primula Studio і транслятор"
LangString SecMain ${LANG_RUSSIAN} "Primula Studio и транслятор"
LangString SecMenu ${LANG_ENGLISH} "Start menu shortcuts"
LangString SecMenu ${LANG_UKRAINIAN} "Ярлики в меню «Пуск»"
LangString SecMenu ${LANG_RUSSIAN} "Ярлыки в меню «Пуск»"
LangString SecDesktop ${LANG_ENGLISH} "Desktop shortcut"
LangString SecDesktop ${LANG_UKRAINIAN} "Ярлик на робочому столі"
LangString SecDesktop ${LANG_RUSSIAN} "Ярлык на рабочем столе"
LangString SecAssoc ${LANG_ENGLISH} "Open .prml files with Primula Studio"
LangString SecAssoc ${LANG_UKRAINIAN} "Відкривати файли .prml у Primula Studio"
LangString SecAssoc ${LANG_RUSSIAN} "Открывать файлы .prml в Primula Studio"
LangString Guide ${LANG_ENGLISH} "Author guide"
LangString Guide ${LANG_UKRAINIAN} "Посібник автора"
LangString Guide ${LANG_RUSSIAN} "Руководство автора"
LangString Examples ${LANG_ENGLISH} "Examples"
LangString Examples ${LANG_UKRAINIAN} "Приклади"
LangString Examples ${LANG_RUSSIAN} "Примеры"
LangString Uninstall ${LANG_ENGLISH} "Uninstall ${APP}"
LangString Uninstall ${LANG_UKRAINIAN} "Видалити ${APP}"
LangString Uninstall ${LANG_RUSSIAN} "Удалить ${APP}"
LangString Running ${LANG_ENGLISH} "${APP} is running. Close it and try again."
LangString Running ${LANG_UKRAINIAN} "${APP} запущено. Закрийте програму й повторіть."
LangString Running ${LANG_RUSSIAN} "${APP} запущен. Закройте программу и повторите."

; The language of the installer follows the system; the user may pick another one first.
Function .onInit
  !insertmacro MUI_LANGDLL_DISPLAY
FunctionEnd

Section "$(SecMain)" SecMain
  SectionIn RO
  SetOutPath "$INSTDIR"
  ; A running Studio keeps its files open: stop with a message instead of a half installation.
  ClearErrors
  IfFileExists "$INSTDIR\primula-studio.exe" 0 +4
    FileOpen $0 "$INSTDIR\primula-studio.exe" a
    IfErrors 0 +2
      Abort "$(Running)"
    FileClose $0
  File /r "${SOURCE}\*.*"
  WriteUninstaller "$INSTDIR\uninstall.exe"
  WriteRegStr HKCU "Software\primula-docs\Installer" "InstallDir" "$INSTDIR"
  ; "Apps & features" entry
  WriteRegStr HKCU "${UNINSTKEY}" "DisplayName" "${APP}"
  WriteRegStr HKCU "${UNINSTKEY}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "${UNINSTKEY}" "Publisher" "primula-docs"
  WriteRegStr HKCU "${UNINSTKEY}" "DisplayIcon" "$INSTDIR\primula-studio.exe"
  WriteRegStr HKCU "${UNINSTKEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${UNINSTKEY}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegStr HKCU "${UNINSTKEY}" "QuietUninstallString" '"$INSTDIR\uninstall.exe" /S'
  WriteRegDWORD HKCU "${UNINSTKEY}" "NoModify" 1
  WriteRegDWORD HKCU "${UNINSTKEY}" "NoRepair" 1
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  IntFmt $0 "0x%08X" $0
  WriteRegDWORD HKCU "${UNINSTKEY}" "EstimatedSize" "$0"
SectionEnd

Section "$(SecMenu)" SecMenu
  SetShellVarContext current
  CreateDirectory "$SMPROGRAMS\${APP}"
  CreateShortCut "$SMPROGRAMS\${APP}\${APP}.lnk" "$INSTDIR\primula-studio.exe"
  CreateShortCut "$SMPROGRAMS\${APP}\$(Guide).lnk" "$INSTDIR\guide"
  CreateShortCut "$SMPROGRAMS\${APP}\$(Examples).lnk" "$INSTDIR\examples"
  CreateShortCut "$SMPROGRAMS\${APP}\$(Uninstall).lnk" "$INSTDIR\uninstall.exe"
SectionEnd

Section "$(SecDesktop)" SecDesktop
  SetShellVarContext current
  CreateShortCut "$DESKTOP\${APP}.lnk" "$INSTDIR\primula-studio.exe"
SectionEnd

Section "$(SecAssoc)" SecAssoc
  ; Per-user association (HKCU\Software\Classes), no administrator rights.
  WriteRegStr HKCU "Software\Classes\.prml" "" "${PROGID}"
  WriteRegStr HKCU "Software\Classes\${PROGID}" "" "Primula document"
  WriteRegStr HKCU "Software\Classes\${PROGID}\DefaultIcon" "" "$INSTDIR\primula-studio.exe,0"
  WriteRegStr HKCU "Software\Classes\${PROGID}\shell\open\command" "" '"$INSTDIR\primula-studio.exe" "%1"'
  WriteRegStr HKCU "Software\primula-docs\Installer" "Association" "1"
  System::Call 'shell32::SHChangeNotify(i 0x08000000, i 0, p 0, p 0)'
SectionEnd

Section "Uninstall"
  SetShellVarContext current
  ; Never remove a directory that is not ours (a mistaken /D= or a moved uninstaller).
  IfFileExists "$INSTDIR\primula-studio.exe" +3 0
    MessageBox MB_OK|MB_ICONSTOP "primula-studio.exe: not found in $INSTDIR"
    Abort
  Delete "$SMPROGRAMS\${APP}\*.lnk"
  RMDir "$SMPROGRAMS\${APP}"
  Delete "$DESKTOP\${APP}.lnk"
  ReadRegStr $0 HKCU "Software\primula-docs\Installer" "Association"
  ${If} $0 == "1"
    DeleteRegKey HKCU "Software\Classes\${PROGID}"
    DeleteRegKey HKCU "Software\Classes\.prml"
    System::Call 'shell32::SHChangeNotify(i 0x08000000, i 0, p 0, p 0)'
  ${EndIf}
  DeleteRegKey HKCU "${UNINSTKEY}"
  DeleteRegKey HKCU "Software\primula-docs\Installer"
  RMDir /r "$INSTDIR"
SectionEnd
