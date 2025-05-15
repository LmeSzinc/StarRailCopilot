#define AppName "StarRailCopilot"
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
OutputBaseFilename={#AppName}-Setup-{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
DisableDirPage=no
DisableProgramGroupPage=no
AllowNoIcons=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; Flags: unchecked

[Files]
Source: "StarRailCopilot\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion uninsrestartdelete

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\src.exe"; IconFilename: "{app}\src.exe"
Name: "{group}\SRC"; Filename: "{app}\src.exe"; IconFilename: "{app}\src.exe"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\src.exe"; IconFilename: "{app}\src.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\src.exe"; Description: "Run {#AppName} now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
function InitializeUninstall: Boolean;
var
  PyExe, KillScripts, Args: String;
  R: Integer;
begin
  PyExe := ExpandConstant('{app}\toolkit\python.exe');
  KillScripts := ExpandConstant('{app}\toolkit\kill_processes.py');
  Args := '"' + KillScripts + '" "' + ExpandConstant('{app}') + '"';
  Exec(PyExe, Args, '', SW_HIDE, ewWaitUntilTerminated, R);
  Sleep(500);
  Result := True;
end;