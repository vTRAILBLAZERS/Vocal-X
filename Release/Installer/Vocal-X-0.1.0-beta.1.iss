#preproc ispp

#define CandidateDir GetEnv("VOCAL_X_CANDIDATE")
#define AppName "Vocal X"
#define AppVersion "0.1.0-beta.1"
#define SetupFilename "Vocal-X-0.1.0-beta.1-Setup"

#if CandidateDir == ""
  #error "VOCAL_X_CANDIDATE environment variable is required"
#endif

[Setup]
AppId={{388CABC5-2484-5832-A13D-CF4C5D265D2E}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
VersionInfoVersion=0.1.0.1
VersionInfoProductName={#AppName}
VersionInfoDescription=Vocal X Beta Installer
VersionInfoProductVersion=0.1.0.1
DefaultDirName={localappdata}\Programs\Vocal X
DefaultGroupName=Vocal X
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
SetupArchitecture=x64
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
WizardStyle=modern
OutputDir=Output
OutputBaseFilename={#SetupFilename}
SetupIconFile={#CandidateDir}\App\assets\vocal-x.ico
UninstallDisplayIcon={app}\App\assets\vocal-x.ico
UninstallDisplayName={#AppName} {#AppVersion}
Compression=lzma2/max
SolidCompression=yes
DiskSpanning=no
SetupLogging=yes
CloseApplications=yes
RestartApplications=no
RestartIfNeededByRun=no
UsePreviousAppDir=yes
UsePreviousGroup=yes
UsePreviousTasks=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Files]
Source: "{#CandidateDir}\*"; DestDir: "{app}"; Excludes: "\Models\*"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{app}\Models"

[Tasks]
Name: "desktopicon"; Description: "Desktop-Verknüpfung erstellen"; GroupDescription: "Zusätzliche Verknüpfungen:"; Flags: unchecked

[Icons]
Name: "{group}\Vocal X"; Filename: "{app}\Runtime\pythonw.exe"; Parameters: """{app}\App\vocal_gui.py"""; WorkingDir: "{app}\App"; IconFilename: "{app}\App\assets\vocal-x.ico"
Name: "{autodesktop}\Vocal X"; Filename: "{app}\Runtime\pythonw.exe"; Parameters: """{app}\App\vocal_gui.py"""; WorkingDir: "{app}\App"; IconFilename: "{app}\App\assets\vocal-x.ico"; Tasks: desktopicon
