; Inno Setup 6.5+; development QA only while release_gate.json remains blocked.
#define MyAppName "MeetingSplit"
#define MyAppVersion "0.8.6"
[Setup]
AppId={{DB612738-836F-4524-B199-FACE68AF3D52}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=MeetingSplit
DefaultDirName={localappdata}\Programs\MeetingSplit
DefaultGroupName=MeetingSplit
OutputDir=..\dist
OutputBaseFilename=MeetingSplit_Setup_v0.8.6
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\MeetingSplit.exe
[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"
[CustomMessages]
en.DesktopShortcut=Create a desktop shortcut
es.DesktopShortcut=Crear acceso directo en el escritorio
en.Shortcuts=Shortcuts:
es.Shortcuts=Accesos directos:
en.OptionalComponents=Prepare optional CUDA / Ollama after setup (separate downloads)
es.OptionalComponents=Preparar CUDA / Ollama opcionales al terminar (descargas separadas)
en.Components=Optional components:
es.Components=Componentes opcionales:
en.ConfigureComponents=Configure optional components
es.ConfigureComponents=Configurar componentes opcionales
en.OpenApp=Open MeetingSplit
es.OpenApp=Abrir MeetingSplit
[Files]
Source: "..\dist\MeetingSplit\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{autoprograms}\MeetingSplit"; Filename: "{app}\MeetingSplit.exe"
Name: "{autodesktop}\MeetingSplit"; Filename: "{app}\MeetingSplit.exe"; Tasks: desktopicon
[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopShortcut}"; GroupDescription: "{cm:Shortcuts}"; Flags: unchecked
Name: "optionalcomponents"; Description: "{cm:OptionalComponents}"; GroupDescription: "{cm:Components}"; Flags: unchecked
[Run]
Filename: "{app}\MeetingSplit.exe"; Parameters: "--configure-components"; Tasks: optionalcomponents; Description: "{cm:ConfigureComponents}"; Flags: postinstall skipifsilent
Filename: "{app}\MeetingSplit.exe"; Tasks: not optionalcomponents; Description: "{cm:OpenApp}"; Flags: nowait postinstall skipifsilent
