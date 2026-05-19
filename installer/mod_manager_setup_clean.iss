#define AppName "PRO Mod Manager"
#define AppVersion "1.0.0"
#define AppPublisher "MK2"
#define AppExeName "PRO_Mod_Manager_Native.exe"

[Setup]
AppId={{A2E5E6A6-4DE6-4675-A89A-66C52D7658E1}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\PRO Mod Manager
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
SetupIconFile=..\assets\mod_manager_new.ico
UninstallDisplayIcon={app}\{#AppExeName}
OutputDir=..\dist_installer
OutputBaseFilename=PRO_Mod_Manager_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\PRO_Mod_Manager_Native.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
