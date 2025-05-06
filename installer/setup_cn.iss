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
AppMutex=SRCMutex
AllowNoIcons=yes

[Languages]
Name: "chinesesimplified"; MessagesFile: "Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "在桌面创建图标(&D)"; Flags: unchecked

[Files]
Source: "StarRailCopilot\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

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
function InitializeUninstall(): Boolean;
var
  ErrorCode: Integer;
begin
  if CheckForMutexes('SRCMutex') and
     (MsgBox('SRC正在运行，是否要关闭它？',
             mbConfirmation, MB_OKCANCEL) = IDOK) then
  begin
    Exec('taskkill.exe', '/f /im src.exe', '', SW_HIDE,
         ewWaitUntilTerminated, ErrorCode);
  end;

  Result := True;
end;
