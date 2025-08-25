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
Source: "StarRailCopilot\src.exe"; DestDir: "{app}"; Flags: ignoreversion uninsrestartdelete
Source: "StarRailCopilot\*.md"; DestDir: "{app}"; Flags: ignoreversion uninsrestartdelete skipifsourcedoesntexist
Source: "StarRailCopilot\installer\*"; DestDir: "{app}\installer"; Flags: recursesubdirs createallsubdirs ignoreversion uninsrestartdelete skipifsourcedoesntexist
Source: "StarRailCopilot\config\*"; DestDir: "{app}\config"; Flags: recursesubdirs createallsubdirs ignoreversion uninsrestartdelete skipifsourcedoesntexist
Source: "StarRailCopilot\.git\*"; DestDir: "{app}\.git"; Flags: recursesubdirs createallsubdirs ignoreversion uninsrestartdelete skipifsourcedoesntexist

Source: "toolkit.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall skipifsourcedoesntexist
Source: "locales.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall skipifsourcedoesntexist
Source: "resources.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall skipifsourcedoesntexist
Source: "deploy.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall skipifsourcedoesntexist

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\src.exe"; IconFilename: "{app}\src.exe"
Name: "{group}\SRC"; Filename: "{app}\src.exe"; IconFilename: "{app}\src.exe"
Name: "{group}\卸载{#AppName}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\src.exe"; IconFilename: "{app}\src.exe"; IconIndex: 0; Tasks: desktopicon

[Run]
Filename: "{app}\src.exe"; Description: "运行 {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[CustomMessages]
chinesesimplified.ExtractingFiles=正在解压文件...
chinesesimplified.ExtractingComponent=正在解压 %1...
chinesesimplified.ExtractComplete=解压完成！
chinesesimplified.ExtractingDesc=请稍候，正在解压大型组件...

[Code]
var
  ExtractPage: TOutputProgressWizardPage;
  TotalProgress: Integer;
  
procedure ExtractSFXArchive(ArchiveName: String; DestPath: String; ProgressWeight: Integer);
var
  ResultCode: Integer;
  StartProgress: Integer;
begin
  StartProgress := ExtractPage.ProgressBar.Position;
  ExtractPage.SetText(FmtMessage(CustomMessage('ExtractingComponent'), [ArchiveName]), '');
  ExtractPage.SetProgress(ExtractPage.ProgressBar.Position, ExtractPage.ProgressBar.Max);
  
  if not Exec(ExpandConstant('{tmp}\' + ArchiveName + '.exe'), 
              '-y -o"' + DestPath + '"', 
              '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    MsgBox('解压 ' + ArchiveName + ' 失败。错误代码: ' + IntToStr(ResultCode), mbError, MB_OK);
  end
  else
  begin
    ExtractPage.SetProgress(StartProgress + ProgressWeight, ExtractPage.ProgressBar.Max);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  SFXFiles: array[0..3] of String;
  SFXWeights: array[0..3] of Integer;
  i: Integer;
  TotalWeight: Integer;
  CurrentProgress: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    SFXFiles[0] := 'toolkit';    SFXWeights[0] := 85;
    SFXFiles[1] := 'locales';    SFXWeights[1] := 3;
    SFXFiles[2] := 'resources';  SFXWeights[2] := 3;
    SFXFiles[3] := 'deploy';     SFXWeights[3] := 9;
    
    TotalWeight := 0;
    for i := 0 to 3 do
      if FileExists(ExpandConstant('{tmp}\' + SFXFiles[i] + '.exe')) then
        TotalWeight := TotalWeight + SFXWeights[i];
    
    if TotalWeight > 0 then
    begin
      ExtractPage := CreateOutputProgressPage(CustomMessage('ExtractingFiles'), 
        CustomMessage('ExtractingDesc'));
      try
        ExtractPage.Show;
        ExtractPage.SetProgress(0, TotalWeight);
        
        CurrentProgress := 0;
        for i := 0 to 3 do
        begin
          if FileExists(ExpandConstant('{tmp}\' + SFXFiles[i] + '.exe')) then
          begin
            ExtractSFXArchive(SFXFiles[i], ExpandConstant('{app}'), SFXWeights[i]);
            CurrentProgress := CurrentProgress + SFXWeights[i];
            ExtractPage.SetProgress(CurrentProgress, TotalWeight);
          end;
        end;
        
        ExtractPage.SetText(CustomMessage('ExtractComplete'), '');
        Sleep(500);
      finally
        ExtractPage.Hide;
      end;
    end;
  end;
end;

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