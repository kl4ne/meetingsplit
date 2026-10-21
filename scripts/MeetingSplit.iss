; Script para Inno Setup 6.5+ (Windows). NO ha sido ejecutado en este entorno Linux.
#define MyAppName "MeetingSplit"
#define MyAppVersion "0.8.4"
[Setup]
AppId={{DB612738-836F-4524-B199-FACE68AF3D52}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=MeetingSplit
DefaultDirName={localappdata}\Programs\MeetingSplit
DefaultGroupName=MeetingSplit
OutputDir=..\dist
OutputBaseFilename=MeetingSplit_Setup_v0.8.4
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\MeetingSplit.exe
[Files]
Source: "..\dist\MeetingSplit\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{autoprograms}\MeetingSplit"; Filename: "{app}\MeetingSplit.exe"
Name: "{autodesktop}\MeetingSplit"; Filename: "{app}\MeetingSplit.exe"; Tasks: desktopicon
[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked
[Run]
Filename: "{app}\MeetingSplit.exe"; Description: "Abrir MeetingSplit"; Flags: nowait postinstall skipifsilent
