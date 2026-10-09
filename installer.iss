; ============================================================
; installer.iss — Inno Setup script for MuliaMixing
; Cara pakai:
;   1. Build dulu dengan PyInstaller: pyinstaller build.spec
;   2. Buka file ini dengan Inno Setup Compiler (ISCC)
;   3. Atau jalankan dari command line: iscc installer.iss
; ============================================================

#define AppName      "MuliaMixing"
#define AppVersion   "1.1.0"
#define AppPublisher "Mulia Creator"
#define AppURL       "https://muliacreator.com"
#define AppExeName   "MuliaMixing.exe"
#define SourceDir    "dist\MuliaMixing"

[Setup]
AppId={{A3F2C1B4-7E9D-4A5C-8F3B-2D6E1C4A9B7F}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=dist\installer
OutputBaseFilename=MuliaMixing_Setup_v{#AppVersion}
SetupIconFile=resources\icons\app.ico
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
MinVersion=10.0
WizardStyle=modern
ShowLanguageDialog=no
LanguageDetectionMethod=none
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
Uninstallable=yes
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#AppExeName}
CreateUninstallRegKey=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Buat shortcut di Desktop"; GroupDescription: "Shortcut:"; Flags: checkedonce

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; FileName: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"; AppUserModelID: "{#AppName}"
Name: "{group}\Uninstall {#AppName}"; FileName: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; FileName: "{app}\{#AppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#AppExeName}"; AppUserModelID: "{#AppName}"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Jalankan {#AppName} sekarang"; Flags: nowait postinstall skipifsilent

[Registry]
Root: HKCU; Subkey: "Software\{#AppPublisher}\{#AppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
