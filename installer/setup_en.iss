#define AppName "StarRailCopilot"
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef PayloadSize
  #define PayloadSize "0"
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
ExtraDiskSpaceRequired={#PayloadSize}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; Flags: unchecked

[Files]
Source: "StarRailCopilot\src.exe"; DestDir: "{app}"; Flags: ignoreversion uninsrestartdelete
Source: "StarRailCopilot\payload.exe"; DestDir: "{app}"; Flags: ignoreversion deleteafterinstall

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\src.exe"; IconFilename: "{app}\src.exe"
Name: "{group}\SRC"; Filename: "{app}\src.exe"; IconFilename: "{app}\src.exe"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\src.exe"; IconFilename: "{app}\src.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\payload.exe"; Parameters: "-y -gm2 -o{app}"; Flags: runhidden waituntilterminated
Filename: "{app}\src.exe"; Description: "Run {#AppName} now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
function InitializeUninstall: Boolean;
var
  Cmd, Args: String;
  R: Integer;
begin
  Exec('taskkill.exe', '/f /t /im src.exe', '', SW_HIDE, ewWaitUntilTerminated, R);
  Cmd := ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe');
  Args := '-NoLogo -NonInteractive -Command "Get-Process python | Where-Object {$_.Path -eq ''' + ExpandConstant('{app}\toolkit\python.exe') + '''} | Stop-Process -Force"';
  Exec(Cmd, Args, '', SW_HIDE, ewWaitUntilTerminated, R);
  Sleep(500);
  Result := True;
end;