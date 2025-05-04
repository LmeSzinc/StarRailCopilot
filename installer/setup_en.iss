#define AppName "StarRailCopilot"
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={userappdata}\{#AppName}
DefaultGroupName={#AppName}
OutputBaseFilename={#AppName}-Setup-{#AppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
DisableDirPage=no
DisableProgramGroupPage=no

; ---------- Languages ----------
; Use Inno Setup’s built‑in English resources
[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

; ---------- Optional tasks ----------
[Tasks]
Name: "desktopicon";   Description: "Create a &desktop icon";     Flags: unchecked
Name: "startmenuentry"; Description: "Add shortcut to &Start Menu"; Flags: checkedonce

; ---------- Files to pack ----------
; The script lives inside the extracted payload folder, so * means “everything”.
[Files]
Source: "StarRailCopilot\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

; ---------- Shortcuts ----------
[Icons]
Name: "{group}\{#AppName}";          Filename: "{app}\src.exe"; IconFilename: "{app}\src.exe"; Tasks: startmenuentry
Name: "{group}\SRC";                Filename: "{app}\src.exe"; IconFilename: "{app}\src.exe"; Tasks: startmenuentry
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}";                        Tasks: startmenuentry
Name: "{userdesktop}\{#AppName}";    Filename: "{app}\src.exe"; IconFilename: "{app}\src.exe"; Tasks: desktopicon

; ---------- Post‑install ----------
[Run]
Filename: "{app}\src.exe"; Description: "Run {#AppName} now"; Flags: nowait postinstall skipifsilent

; ---------- Full cleanup on uninstall ----------
[UninstallDelete]
Type: filesandordirs; Name: "{app}"
