#define AppName "StarRailCopilot"
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#define Suffix "-cn"

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={userappdata}\{#AppName}
DefaultGroupName={#AppName}
OutputBaseFilename={#AppName}-Setup-{#AppVersion}{#Suffix}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
DisableDirPage=no
DisableProgramGroupPage=no

[Languages]
Name: "chinesesimplified"; MessagesFile: "Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "在桌面创建图标(&D)"; Flags: unchecked
Name: "startmenuentry"; Description: "创建开始菜单项(&S)"; Flags: checkedonce

[Files]
Source: "StarRailCopilot\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#AppName}";      Filename: "{app}\src.exe"; IconFilename: "{app}\src.exe"; IconIndex: 0; Tasks: startmenuentry
Name: "{group}\SRC";            Filename: "{app}\src.exe"; IconFilename: "{app}\src.exe"; IconIndex: 0; Tasks: startmenuentry
Name: "{group}\卸载 {#AppName}"; Filename: "{uninstallexe}";                                  Tasks: startmenuentry
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\src.exe"; IconFilename: "{app}\src.exe"; IconIndex: 0; Tasks: desktopicon

[Run]
Filename: "{app}\src.exe"; Description: "运行 {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
