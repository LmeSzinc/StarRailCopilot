#define AppName "StarRailCopilot"
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#define Suffix "-cn"

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
OutputBaseFilename={#AppName}-Setup-{#AppVersion}{#Suffix}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
DisableDirPage=no
DisableProgramGroupPage=no
AllowNoIcons=yes

[Languages]
Name: "chinesesimplified"; MessagesFile: "Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "在桌面创建图标(&D)"; Flags: unchecked

[Files]
Source: "StarRailCopilot\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion uninsrestartdelete

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\src.exe"; IconFilename: "{app}\src.exe"
Name: "{group}\SRC"; Filename: "{app}\src.exe"; IconFilename: "{app}\src.exe"
Name: "{group}\卸载{#AppName}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\src.exe"; IconFilename: "{app}\src.exe"; IconIndex: 0; Tasks: desktopicon

[Run]
Filename: "{app}\src.exe"; Description: "运行 {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
function InitializeUninstall: Boolean;
var
  PyExe, KillScripts, Args: String;
  R: Integer;
begin
  PyExe := ExpandConstant('{app}\toolkit\python.exe');
  KillScripts := ExpandConstant('{app}\installer\kill_processes.py');
  Args := '"' + KillScripts + '" "' + ExpandConstant('{app}') + '"';
  Exec(PyExe, Args, '', SW_HIDE, ewWaitUntilTerminated, R);
  Sleep(500);
  Result := True;
end;