; ============================================
; OharaBank - Script do Instalador (Inno Setup)
; ============================================

[Setup]
AppName=OharaBank
AppVersion=1.0.0
AppPublisher=OharaBank
DefaultDirName={autopf}\OharaBank
DefaultGroupName=OharaBank
OutputDir=dist
OutputBaseFilename=OharaBank_Setup
Compression=lzma2/ultra64
SolidCompression=yes
SetupIconFile=imagens\logos\logoapp.ico
UninstallDisplayIcon={app}\OharaBank.exe
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
DisableProgramGroupPage=yes

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\OharaBank\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "installers\miktex-portable\*"; DestDir: "{app}\miktex-portable"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\OharaBank"; Filename: "{app}\OharaBank.exe"
Name: "{autodesktop}\OharaBank"; Filename: "{app}\OharaBank.exe"
Name: "{group}\Desinstalar OharaBank"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\OharaBank.exe"; Description: "Iniciar OharaBank"; Flags: nowait postinstall skipifsilent
